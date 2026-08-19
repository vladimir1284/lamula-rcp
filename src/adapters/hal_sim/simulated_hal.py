"""Adaptador HAL-simulador -- cliente Modbus + receptor UDP contra `radar_emulator` (D-06).

Implementa `HardwareAbstractionLayer` (src/core/contracts/hal.py) igual que
tendra que hacerlo `hal_real`: nada por encima de este adaptador puede
distinguir cual esta activo. Una sola conexion TCP Modbus multiplexada
sobre los diez unit IDs de la semilla (verificado en
spike-fase0/modbus_client_spike.py, PEND-21 de radar_emulator), mas un
receptor UDP de encoder de fondo (`udp_encoder.py`).

Escrituras son fire-and-forget (hal.py): no hay espera de tick ni
read-your-write aqui: es responsabilidad del llamador, tal como documenta
la interfaz.
"""

from __future__ import annotations

import time

from pymodbus.client import AsyncModbusTcpClient

from core.contracts.common import MonotonicMicros, SignalQuality
from core.contracts.hal import AntennaPosition, HardwareAbstractionLayer, SignalId, SignalReading

from . import signal_catalog, udp_encoder


def _now_us() -> MonotonicMicros:
    return time.monotonic_ns() // 1000


class SimulatedHAL(HardwareAbstractionLayer):
    def __init__(
        self,
        modbus_host: str = "127.0.0.1",
        modbus_port: int = 15020,
        udp_bind_host: str = "0.0.0.0",
        udp_port: int = 15100,
    ) -> None:
        self._modbus_host = modbus_host
        self._modbus_port = modbus_port
        self._udp_bind_host = udp_bind_host
        self._udp_port = udp_port
        self._client: AsyncModbusTcpClient | None = None
        self._udp_transport: object | None = None
        self._udp_receiver: udp_encoder.EncoderReceiver | None = None

    async def connect(self) -> None:
        self._client = AsyncModbusTcpClient(self._modbus_host, port=self._modbus_port)
        await self._client.connect()
        if not self._client.connected:
            self._client = None
            raise ConnectionError(f"no se pudo conectar a Modbus {self._modbus_host}:{self._modbus_port}")
        self._udp_transport, self._udp_receiver = await udp_encoder.start(self._udp_bind_host, self._udp_port)

    async def disconnect(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
        if self._udp_transport is not None:
            self._udp_transport.close()
            self._udp_transport = None
        self._udp_receiver = None

    def is_connected(self) -> bool:
        return self._client is not None and self._client.connected

    def _client_or_raise(self) -> AsyncModbusTcpClient:
        if self._client is None or not self._client.connected:
            raise ConnectionError("SimulatedHAL no conectado -- llamar a connect() primero")
        return self._client

    async def read_digital(self, signal_id: SignalId) -> SignalReading[bool]:
        spec = signal_catalog.get(signal_id)
        if spec.kind not in ("DI", "DO"):
            raise ValueError(f"{signal_id}: no es una senal digital (kind={spec.kind})")
        client = self._client_or_raise()
        resp = await client.read_coils(spec.address, count=1, device_id=spec.unit_id)
        if resp.isError():
            raise RuntimeError(
                f"{signal_id}: excepcion Modbus leyendo coil {spec.address} (unit {spec.unit_id}): {resp}"
            )
        return SignalReading(value=bool(resp.bits[0]), quality=SignalQuality.OK, at_us=_now_us())

    async def read_analog(self, signal_id: SignalId) -> SignalReading[float]:
        spec = signal_catalog.get(signal_id)
        if spec.kind not in ("AI", "AO"):
            raise ValueError(f"{signal_id}: no es una senal analogica (kind={spec.kind})")
        client = self._client_or_raise()
        resp = await client.read_holding_registers(spec.address, count=1, device_id=spec.unit_id)
        if resp.isError():
            raise RuntimeError(
                f"{signal_id}: excepcion Modbus leyendo holding {spec.address} (unit {spec.unit_id}): {resp}"
            )
        value = spec.to_engineering(resp.registers[0])
        in_range = spec.eng_lo <= value <= spec.eng_hi
        quality = SignalQuality.OK if in_range else SignalQuality.OUT_OF_RANGE
        return SignalReading(value=value, quality=quality, at_us=_now_us())

    async def write_digital(self, signal_id: SignalId, value: bool) -> None:
        spec = signal_catalog.get(signal_id)
        if spec.kind not in ("DI", "DO"):
            raise ValueError(f"{signal_id}: no es una senal digital (kind={spec.kind})")
        if not spec.writable:
            raise ValueError(f"{signal_id}: de solo lectura (DI), no se puede escribir")
        client = self._client_or_raise()
        resp = await client.write_coil(spec.address, value, device_id=spec.unit_id)
        if resp.isError():
            raise RuntimeError(
                f"{signal_id}: excepcion Modbus escribiendo coil {spec.address} (unit {spec.unit_id}): {resp}"
            )

    async def write_analog(self, signal_id: SignalId, value: float) -> None:
        spec = signal_catalog.get(signal_id)
        if spec.kind not in ("AI", "AO"):
            raise ValueError(f"{signal_id}: no es una senal analogica (kind={spec.kind})")
        if not spec.writable:
            raise ValueError(f"{signal_id}: de solo lectura (AI), no se puede escribir")
        client = self._client_or_raise()
        raw = spec.to_raw(value)
        resp = await client.write_register(spec.address, raw, device_id=spec.unit_id)
        if resp.isError():
            raise RuntimeError(
                f"{signal_id}: excepcion Modbus escribiendo holding {spec.address} (unit {spec.unit_id}): {resp}"
            )

    async def read_antenna_position(self) -> AntennaPosition:
        if self._udp_receiver is None:
            raise ConnectionError("SimulatedHAL no conectado -- llamar a connect() primero")
        return self._udp_receiver.latest_position()
