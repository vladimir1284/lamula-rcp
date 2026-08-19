"""RCP<->HAL (Fase 0, plan §6): interfaz abstracta de dispositivo.

Un solo puerto que implementan por igual el adaptador real (Modbus/Profibus
via SBC) y el adaptador simulador (cliente Modbus + receptor UDP contra
`radar_emulator`, ver docs/alcance/contexto.md#relacion-con-radar_emulator).
Nada por encima del HAL distingue cual esta activo (D-06).

Identidad de senal: string namespaced "subsystem.signal" (p.ej.
"tx.tx_on_status", "ant.az_position"), igual que el catalogo de
`radar_emulator` para el RD100S. Fijo a un solo modelo de radar (AGENTS.md);
no hay aqui una capa de configuracion generica por diseno.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

from .common import MonotonicMicros, SignalQuality

SignalId = str

T = TypeVar("T", bool, float)


class SignalReading(BaseModel, Generic[T]):
    """Lectura de una senal digital o analogica, en unidades de ingenieria.

    La conversion a crudo (Type Code, rango 0..65535, etc. — ver
    docs/interfaces/modbus.md de radar_emulator) ocurre solo en el adaptador,
    en el borde. El core nunca ve un valor crudo.
    """

    value: T
    quality: SignalQuality
    at_us: MonotonicMicros


class AntennaPosition(BaseModel):
    """Snapshot derivado de RD100S-ENC-UDP v1, ya en unidades de ingenieria.

    Deliberadamente sin el bit `SIM` del paquete: es un marcador de traza del
    transporte UDP, no un dato de dominio, y filtrarlo aqui es lo que hace
    que nada por encima del HAL pueda distinguir real de simulado (D-06). Si
    hace falta saber "es una prueba simulada" para un log de auditoria, ese
    dato vive en la capa de sesion del adaptador, no en este modelo.
    """

    az_deg: float
    el_deg: float
    az_rate_deg_s: float
    el_rate_deg_s: float
    az_valid: bool
    el_valid: bool
    az_ref_ok: bool
    el_ref_ok: bool
    az_fault: bool
    el_fault: bool
    degraded: bool
    seq: int
    """Secuencia del emisor de encoder, envuelve en 2^32. Solo para detectar
    huecos/reinicio; el HAL no expone el reinicio como excepcion, lo absorbe
    y produce la mejor lectura disponible marcandola con `quality`."""
    at_us: MonotonicMicros


class HardwareAbstractionLayer(ABC):
    """Puerto que implementan `hal_real` y `hal_sim` (src/adapters/).

    Los metodos de escritura son fire-and-forget desde la perspectiva del
    llamador: `await write_digital(...)` que retorna NO garantiza que el
    valor ya este aplicado. El spike de Fase 0 contra `radar_emulator`
    confirmo que toda escritura `from_controller` queda pendiente hasta el
    siguiente tick del simulador (signal-store.ts, ~50 ms en la semilla); el
    adaptador real tiene su propio ciclo de interrogacion Modbus con la misma
    propiedad. Un llamador que necesite confirmar el valor debe volver a leer
    despues de al menos un ciclo — no asumir consistencia read-your-write.
    """

    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    @abstractmethod
    def is_connected(self) -> bool: ...

    @abstractmethod
    async def read_digital(self, signal_id: SignalId) -> SignalReading[bool]: ...

    @abstractmethod
    async def read_analog(self, signal_id: SignalId) -> SignalReading[float]: ...

    @abstractmethod
    async def write_digital(self, signal_id: SignalId, value: bool) -> None: ...

    @abstractmethod
    async def write_analog(self, signal_id: SignalId, value: float) -> None: ...

    @abstractmethod
    async def read_antenna_position(self) -> AntennaPosition: ...
