"""Adaptador RCP<->DSP -- lado receptor del stream de momentos (Fase 1, esqueleto).

Escucha TCP y decodifica el mismo framing que
`spike-fase0/dsp_moment_stream_spike.py --role dsp` emite: JSON de
`RadialMoments` precedido por un largo de 4 bytes big-endian. Es el
framing propio de ese stub, no un protocolo real acordado con el proyecto
DSP (PEND-RCP-05, `src/core/contracts/dsp.py`) -- se descarta o se adapta
en cuanto exista una implementacion de referencia real del lado DSP.

Decision 2026-08-19: solo se mantienen contadores/estado resumido
(`radials_received`, ultimo volumen/elevacion/status), no se exponen los
momentos completos hacia la MMI todavia -- ver
`core/contracts/mmi.DspStreamStatus`. Streaming de momentos reales
(reflectividad, velocidad) a la MMI queda para cuando se diseñe la vista
PPI (Fase 2/3); resolverlo antes seria inventar una forma de PPI sin
acuerdo del equipo, que es justo lo que el contrato ya congelado evita.
"""

from __future__ import annotations

import asyncio
import struct

from core.contracts.dsp import RadialMoments


class MomentStreamReceiver:
    """Un solo emisor esperado a la vez -- si el emisor se desconecta y
    reconecta, `connected` vuelve a `True` con la siguiente conexion
    aceptada; los contadores no se resetean entre conexiones."""

    def __init__(self) -> None:
        self.connected = False
        self.radials_received = 0
        self._latest: RadialMoments | None = None
        self._server: asyncio.Server | None = None

    @property
    def latest(self) -> RadialMoments | None:
        return self._latest

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.connected = True
        try:
            while True:
                header = await reader.readexactly(4)
                (length,) = struct.unpack(">I", header)
                body = await reader.readexactly(length)
                self._latest = RadialMoments.model_validate_json(body)
                self.radials_received += 1
        except (asyncio.IncompleteReadError, ConnectionError):
            pass  # emisor cerro la conexion (fin de volumen en el stub) -- no es un fallo
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
