"""Adaptador RCP<->DSP -- lado receptor del stream de momentos.

Ya no decodifica el framing inventado por `spike-fase0/dsp_moment_stream_spike.py`
(JSON con largo de 4 bytes big-endian). Habla el formato de cable real del
proyecto LAMULA DSP, `DSP<->RCP v0.1`, vendorizado en `contract/vendor/` y
anclado por hash: cabecera comun de 12 B, luego `payload_len` bytes con el
mensaje completo. La traduccion a `RadialMoments` la hace `wire.py`; aqui solo
vive el transporte y el estado de la conexion.

Decision 2026-08-19, que sigue en pie: solo se mantienen contadores y estado
resumido, no se exponen los momentos completos hacia la MMI todavia -- ver
`core/contracts/mmi.DspStreamStatus`. El streaming de momentos reales a la MMI
espera al diseno de la vista PPI (Fase 2/3).

Lo que si cambia respecto a la version del stub: ahora llegan mas tipos de
mensaje que radiales. Un `status`, un `bite_event` o un `config_ack` no son un
error de trama, asi que no se cierra la conexion al verlos; se cuentan aparte y
se ignoran hasta que haya quien los consuma. Una trama mal formada, en cambio,
si es un fallo: se registra y se corta, porque despues de un largo erroneo el
flujo esta desincronizado y seguir leyendo produce basura plausible.

Entre medias hay un tercer caso, que no es ninguno de los dos: un radial
intacto cuyo contenido no sirve (`DegenerateRadialError`, hoy solo el ancho de
azimut cero). El flujo sigue en sincronia, asi que ese radial se descarta y se
cuenta, pero el enlace no se corta.
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from datetime import datetime, timezone

from contract.vendor import dsp_rcp_v0_1 as wire
from core.contracts.dsp import DspBiteEvent, RadialMoments

from .wire import (
    DegenerateRadialError,
    WireFormatError,
    decode_bite_event,
    decode_moment_ray,
    decode_spectrum_frame,
    encode_config,
    encode_control,
    parse_frame_header,
)

logger = logging.getLogger(__name__)

#: Tope de tamano de mensaje. Un radial de 3680 celdas con los 14 momentos ronda
#: los 207 kB; 4 MB deja margen de sobra y evita que un `payload_len` corrupto
#: haga reservar memoria sin limite antes de que falle nada.
MAX_MESSAGE_BYTES = 4 * 1024 * 1024

#: Sucesos de BITE del DSP que se guardan. Es un buffer de diagnostico, no un
#: historial persistente: el historial de verdad es de quien los consuma.
DSP_BITE_HISTORY = 200


class MomentStreamReceiver:
    """Un solo emisor esperado a la vez.

    Si el emisor se desconecta y reconecta, `connected` vuelve a `True` con la
    siguiente conexion aceptada; los contadores no se resetean entre conexiones.
    """

    def __init__(self) -> None:
        self.connected = False
        self.radials_received = 0
        self.other_messages_received = 0
        self.frame_errors = 0
        # Radiales intactos pero sin barrido de azimut: se descartan sin
        # cortar el enlace. Contador interno; todavia no llega a la MMI
        # (haria falta un campo nuevo en DspStreamStatus y su TS).
        self.degenerate_radials = 0
        # Sucesos de BITE del DSP, los mas recientes primero en salir: hasta
        # ahora caian en el `else` generico y se perdian (PEND-RCP-14). Que
        # lleguen a la MMI, y como se mezclan con los fallos Modbus de
        # `core/bite/manager.py`, sigue sin decidirse -- son modelos
        # distintos, ver `DspBiteEvent`.
        self.dsp_bite_events: deque[DspBiteEvent] = deque(maxlen=DSP_BITE_HISTORY)
        self._latest: RadialMoments | None = None
        self._latest_status: wire.Status | None = None
        self._latest_config: wire.Config | None = None
        self._latest_spectrum: tuple[int, int, int, int, float, float, float, list[float]] | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._control_seq = 0
        # Hora de pared del ultimo MOMENT_RAY -- unica forma de que A6 (RD)
        # distinga "conectado pero sin datos hace rato" de "recibiendo de
        # verdad"; `connected` solo refleja el socket TCP, no el flujo.
        self._last_radial_at: datetime | None = None
        self._server: asyncio.Server | None = None
        # Perfil de banco (fase C0 del plan de integracion, `tools/hil/`): si
        # esta puesto, en cuanto el DSP conecta se le manda ese `config` y un
        # `START`. Es andamio de banco, no comportamiento de operador: en
        # produccion quien decide la configuracion es el Scan Controller, y
        # ese mapeo sigue abierto (PEND-RCP-10). Vale `None` salvo que el
        # gateway arranque con `--dsp-bench-profile`.
        self.bench_profile: wire.Config | None = None

    @property
    def latest(self) -> RadialMoments | None:
        return self._latest

    @property
    def latest_status(self) -> wire.Status | None:
        return self._latest_status

    @property
    def latest_config(self) -> wire.Config | None:
        return self._latest_config

    @property
    def latest_spectrum(self) -> tuple[int, int, int, int, float, float, float, list[float]] | None:
        return self._latest_spectrum

    @property
    def last_radial_at(self) -> datetime | None:
        return self._last_radial_at

    async def send_config(self, config: wire.Config) -> None:
        """Manda un `config` completo al DSP.

        Sin esto el DSP se queda en fase `setup` y no emite un solo radial:
        su maquina de estados exige `config` antes de aceptar `START`. Es el
        primer tramo del camino descendente RCP->DSP->DRx que este repo puede
        ejercer de verdad -- el DSP traduce los campos de DRx (`prf_div`,
        `pulse_width_idx`, `cell_mode`, `trigger_delay_*`/`trigger_width_*`) y
        los baja al DRx por su propio contrato.
        """
        if not self._writer:
            raise RuntimeError("DSP stream no esta conectado")
        self._writer.write(encode_config(config))
        await self._writer.drain()

    async def send_command(self, command: int) -> None:
        """Manda un mandato del plano de control; ver `wire.Command`."""
        if not self._writer:
            raise RuntimeError("DSP stream no esta conectado")
        self._control_seq = (self._control_seq + 1) & 0xFFFFFFFF
        self._writer.write(encode_control(self._control_seq, command))
        await self._writer.drain()

    async def request_spectrum(self) -> None:
        """Envia el comando REQUEST_SPECTRUM al DSP."""
        if not self._writer:
            raise RuntimeError("DSP stream no esta conectado")
        self._control_seq = (self._control_seq + 1) & 0xFFFFFFFF
        payload = encode_control(self._control_seq, wire.Command.REQUEST_SPECTRUM)
        self._writer.write(payload)
        await self._writer.drain()

    async def reset_counters(self) -> None:
        """Reinicia contadores de trigger/radiales (Vz)."""
        self.radials_received = 0
        self.other_messages_received = 0
        self.frame_errors = 0
        self.degenerate_radials = 0
        if self._latest_status:
            self._latest_status.rays_in = 0
            self._latest_status.rays_out = 0
            self._latest_status.rays_dropped = 0
        if self.connected and self._writer:
            try:
                self._control_seq += 1
                msg = encode_control(self._control_seq, wire.Command.RESET_COUNTERS)
                self._writer.write(msg)
                await self._writer.drain()
            except Exception:
                logger.exception("Error enviando mandato RESET_COUNTERS al DSP")

    async def _read_message(self, reader: asyncio.StreamReader) -> tuple[int, bytes]:
        raw_header = await reader.readexactly(wire.Header.SIZE)
        header = parse_frame_header(raw_header)
        if header.payload_len > MAX_MESSAGE_BYTES:
            raise WireFormatError(
                f"payload_len {header.payload_len} supera el tope de"
                f" {MAX_MESSAGE_BYTES} B; el flujo esta corrupto"
            )
        body = await reader.readexactly(header.payload_len)
        return header.msg_type, body

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        self.connected = True
        self._writer = writer
        if self.bench_profile is not None:
            try:
                await self.send_config(self.bench_profile)
                await self.send_command(wire.Command.START)
                logger.info("perfil de banco enviado al DSP (config + START)")
            except Exception:
                logger.exception("no se pudo aplicar el perfil de banco al DSP")
        try:
            while True:
                msg_type, body = await self._read_message(reader)
                if msg_type == wire.MsgType.MOMENT_RAY:
                    try:
                        self._latest = decode_moment_ray(body)
                    except DegenerateRadialError as exc:
                        # Trama intacta, contenido inservible: se descarta sin
                        # cerrar el enlace, al contrario que WireFormatError.
                        # Ver el doc de esa excepcion.
                        self.degenerate_radials += 1
                        if self.degenerate_radials == 1:
                            logger.warning("radial descartado: %s", exc)
                        continue
                    self.radials_received += 1
                    self._last_radial_at = datetime.now(timezone.utc)
                elif msg_type == wire.MsgType.STATUS:
                    self._latest_status = wire.Status.unpack(body)
                    self.other_messages_received += 1
                elif msg_type == wire.MsgType.CONFIG:
                    self._latest_config = wire.Config.unpack(body)
                    self.other_messages_received += 1
                elif msg_type == wire.MsgType.SPECTRUM_FRAME:
                    self._latest_spectrum = decode_spectrum_frame(body)
                    self.other_messages_received += 1
                elif msg_type == wire.MsgType.BITE_EVENT:
                    self.dsp_bite_events.append(decode_bite_event(body))
                    self.other_messages_received += 1
                else:
                    # config_ack, capabilities, selftest_result... son
                    # legitimos por este mismo enlace; todavia no hay consumidor.
                    self.other_messages_received += 1
        except (asyncio.IncompleteReadError, ConnectionError):
            pass  # el emisor cerro -- no es un fallo
        except WireFormatError:
            # Tras un largo o un magic malo el flujo esta desincronizado: seguir
            # leyendo produciria radiales que parecen validos y no lo son.
            self.frame_errors += 1
            logger.exception("trama invalida del DSP; se cierra la conexion")
        finally:
            self.connected = False
            self._writer = None
            writer.close()

    async def start(self, bind_host: str, port: int) -> None:
        self._server = await asyncio.start_server(self._handle_client, bind_host, port)

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
