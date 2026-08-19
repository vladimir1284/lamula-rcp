"""Receptor RD100S-ENC-UDP v1 (radar_emulator/docs/interfaces/udp-encoder.md).

Parsea el paquete de 36 octetos, sigue la secuencia para detectar reinicio
del emisor, y expone la ultima posicion valida. Formato ejercitado ya en
spike-fase0/udp_encoder_spike.py -- esta version corre como
`asyncio.DatagramProtocol` de fondo, no como script de una sola corrida.

Documento normativo "propuesta, con valores provisionales" (PEND-01 a
PEND-05 de radar_emulator): escala angular, unidad de timestamp, cadencia y
bits de estado pueden cambiar antes de congelar la version 1.
"""

from __future__ import annotations

import asyncio
import struct
import time

from core.contracts.common import MonotonicMicros
from core.contracts.hal import AntennaPosition

MAGIC = 0x5244
VERSION = 0x01
PKT_STRUCT = struct.Struct("<HBBIQiiiiHH")
assert PKT_STRUCT.size == 36

STALE_TIMEOUT_S = 0.1  # 100 ms, diez periodos nominales a 100 Hz (mismo margen que el spike)

_AZ_VALID, _EL_VALID, _AZ_REF_OK, _EL_REF_OK, _AZ_FAULT, _EL_FAULT, _SIM, _DEGRADED = range(8)


def _decode(datagram: bytes) -> dict | None:
    if len(datagram) != PKT_STRUCT.size:
        return None
    magic, version, _r0, seq, t_us, az_mdeg, el_mdeg, az_rate, el_rate, status, _r1 = PKT_STRUCT.unpack(datagram)
    if magic != MAGIC or version != VERSION:
        return None
    return dict(seq=seq, t_us=t_us, az_mdeg=az_mdeg, el_mdeg=el_mdeg, az_rate=az_rate, el_rate=el_rate, status=status)


def _seq_delta(prev: int, curr: int) -> int:
    """Delta con envolvente en 2^32, con signo (negativo = retroceso)."""
    raw = (curr - prev) & 0xFFFFFFFF
    if raw >= 0x80000000:
        raw -= 0x100000000
    return raw


class EncoderReceiver(asyncio.DatagramProtocol):
    """Mantiene la ultima posicion valida; nunca bloquea, nunca reintenta.

    `at_us` de la posicion expuesta es el reloj monotono de ESTE proceso al
    recibir el datagrama, no el `t_us` del paquete: ese es el monotono del
    proceso emisor, y common.py prohibe comparar monotonos de procesos
    distintos. `t_us` del paquete solo se usa aqui dentro, entre paquetes
    consecutivos del mismo emisor, para detectar su reinicio.
    """

    def __init__(self) -> None:
        self._latest: tuple[dict, MonotonicMicros] | None = None
        self._prev_pkt: dict | None = None
        self.resets_detected = 0

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        pass

    def datagram_received(self, data: bytes, addr) -> None:
        pkt = _decode(data)
        if pkt is None:
            return  # descarte silencioso: magic/version/longitud invalidos, por contrato

        if self._prev_pkt is not None:
            d_seq = _seq_delta(self._prev_pkt["seq"], pkt["seq"])
            d_t = pkt["t_us"] - self._prev_pkt["t_us"]
            if d_seq < 0 and d_t < 0:
                self.resets_detected += 1  # reinicio del emisor, absorbido, no se expone como excepcion

        self._prev_pkt = pkt
        self._latest = (pkt, time.monotonic_ns() // 1000)

    def latest_position(self) -> AntennaPosition:
        if self._latest is None:
            raise RuntimeError("sin paquete de encoder recibido todavia")
        pkt, at_us = self._latest
        now_us = time.monotonic_ns() // 1000
        if (now_us - at_us) > STALE_TIMEOUT_S * 1_000_000:
            raise RuntimeError(
                f"stream de encoder perdido: sin paquete nuevo hace {(now_us - at_us) / 1000:.1f} ms"
            )

        status = pkt["status"]
        return AntennaPosition(
            az_deg=pkt["az_mdeg"] / 1000.0,
            el_deg=pkt["el_mdeg"] / 1000.0,
            az_rate_deg_s=pkt["az_rate"] / 1000.0,
            el_rate_deg_s=pkt["el_rate"] / 1000.0,
            az_valid=bool(status & (1 << _AZ_VALID)),
            el_valid=bool(status & (1 << _EL_VALID)),
            az_ref_ok=bool(status & (1 << _AZ_REF_OK)),
            el_ref_ok=bool(status & (1 << _EL_REF_OK)),
            az_fault=bool(status & (1 << _AZ_FAULT)),
            el_fault=bool(status & (1 << _EL_FAULT)),
            degraded=bool(status & (1 << _DEGRADED)),
            seq=pkt["seq"],
            at_us=at_us,
        )


async def start(bind_host: str, port: int) -> tuple[asyncio.DatagramTransport, EncoderReceiver]:
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        EncoderReceiver, local_addr=(bind_host, port)
    )
    return transport, protocol
