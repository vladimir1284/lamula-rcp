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
"""

from __future__ import annotations

import asyncio
import logging

from contract.vendor import dsp_rcp_v0_1 as wire
from core.contracts.dsp import RadialMoments

from .wire import WireFormatError, decode_moment_ray, parse_frame_header

logger = logging.getLogger(__name__)

#: Tope de tamano de mensaje. Un radial de 3680 celdas con los 14 momentos ronda
#: los 207 kB; 4 MB deja margen de sobra y evita que un `payload_len` corrupto
#: haga reservar memoria sin limite antes de que falle nada.
MAX_MESSAGE_BYTES = 4 * 1024 * 1024


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
        self._latest: RadialMoments | None = None
        self._server: asyncio.Server | None = None

    @property
    def latest(self) -> RadialMoments | None:
        return self._latest

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
        try:
            while True:
                msg_type, body = await self._read_message(reader)
                if msg_type == wire.MsgType.MOMENT_RAY:
                    self._latest = decode_moment_ray(body)
                    self.radials_received += 1
                else:
                    # status, bite_event, config_ack, capabilities... son
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
            writer.close()

    async def start(self, bind_host: str, port: int) -> None:
        self._server = await asyncio.start_server(self._handle_client, bind_host, port)

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
