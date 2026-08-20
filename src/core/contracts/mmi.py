"""RCP<->MMI (Fase 0, plan §6): REST para comandos, WebSocket para estado en vivo.

Congela solo el sobre de sesion/control/estado que Fase 1 necesita para el
"primer pipe de datos en vivo sim->WS->PPI" (docs/implementacion/fases.md).
Scan Worksheet, System Visualization/BITE detallado, vistas PPI/RHI/ASCOPE y
demas superficie de operador son de Fase 2/3 y no se anticipan aqui — habria
que inventar forma sin acuerdo del equipo, que es justo lo que este contrato
existe para evitar.

Este modulo es la fuente Pydantic para el codegen a TypeScript (plan §5, D-08:
"tipado Pydantic -> TypeScript generado"); el pipeline de codegen en si no es
parte de Fase 0.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from .bite import BiteTransition
from .control import RoutineResult
from .dsp import RadialStatus
from .hal import AntennaPosition, SignalId
from .safety import AntennaAxis
from .scan import AxisPositioningParams, ScanCutResult


class OperatorMode(StrEnum):
    """D-07: arbitraje de control colapsado a passive/active, un solo operador."""

    PASSIVE = "passive"
    ACTIVE = "active"


class ControlAuthorityState(BaseModel):
    """`since_wall` es hora de pared: es un dato para el operador/auditoria,
    no telemetria interna (AGENTS.md, "dos relojes")."""

    mode: OperatorMode
    actor: str
    since_wall: datetime


# --- REST -------------------------------------------------------------


class SetControlModeRequest(BaseModel):
    mode: OperatorMode
    actor: str


# --- Ejecucion de rutinas de control (Fase 2, ampliacion de este contrato ya
# congelado -- mismo criterio que D-10 en docs/alcance/decisiones.md: se
# amplia para una capacidad nueva y necesaria, no se reinterpreta nada ya
# fijado). Ninguno de estos campos lleva default: si `core/control_routines/`
# exige el parametro sin default (no hay valor real confirmado, ver
# PEND-RCP-07), la MMI tiene que traerlo explicito -- inventar un default aca
# seria el mismo error ya evitado ahi. ---


class TransmitterPowerOnRequest(BaseModel):
    warmup_timeout_s: float


class ReceiverPowerOnRequest(BaseModel):
    confirm_timeout_s: float


class AntennaUnitPowerOnRequest(BaseModel):
    confirm_timeout_s: float


class AntennaMovementRequest(BaseModel):
    axis: AntennaAxis
    voltage_reference: float


class AntennaPositioningRequest(BaseModel):
    axis: AntennaAxis
    target_deg: float
    gain_v_per_deg: float
    max_voltage: float
    tolerance_deg: float
    timeout_s: float


class ScanCutExecutionRequest(BaseModel):
    """`POST /api/scan/worksheet/{index}/execute` -- espejo de los kwargs de
    `core.scan_controller.run_scan_cut` (sin `cut`, ya identificado por
    `index`). Mismo criterio que el resto de este bloque: ningun campo lleva
    default -- ninguno tiene un valor real confirmado (PEND-RCP-07/09)."""

    azimuth_positioning: AxisPositioningParams
    elevation_positioning: AxisPositioningParams
    sweep_voltage_magnitude: float
    sweep_tolerance_deg: float
    sweep_timeout_s: float


class ControlJobStatus(StrEnum):
    RUNNING = "running"
    DONE = "done"


class ControlJobAccepted(BaseModel):
    """Respuesta inmediata (202) de los seis `POST /api/control/*` -- ya no
    esperan a que la rutina termine (podia ser hasta `timeout_s`, minutos en
    `antenna-positioning`/power-on con caldeo real). `status` siempre arranca
    en `RUNNING`; el llamador sondea `GET /api/control/jobs/{job_id}`."""

    job_id: str
    routine: str
    status: ControlJobStatus


class ControlJobStatusResponse(BaseModel):
    """Respuesta de `GET /api/control/jobs/{job_id}`. `result` es `None`
    mientras `status == RUNNING`. `error` distingue una excepcion inesperada
    (p.ej. el HAL se desconecto a mitad de camino) de un `RoutineResult` con
    `outcome` en `failed`/`interrupted`, que es un resultado legitimo de la
    rutina, no un error de infraestructura."""

    job_id: str
    routine: str
    status: ControlJobStatus
    # `ScanCutResult` (Scan Controller) se agrego a esta union en vez de un
    # contrato de job separado -- mismo criterio D-10 (ampliar el contrato ya
    # congelado): `routine` ya era `str` libre, no el enum cerrado
    # `RoutineName`, y el resto del sobre (job_id/status/error) es identico.
    result: RoutineResult | ScanCutResult | None
    error: str | None


class DspStreamStatus(BaseModel):
    """Estado resumido del stream DSP/DRX -- decision 2026-08-19: solo contadores/estado,
    no los momentos completos. Streaming de momentos a la MMI queda para cuando se diseñe
    la vista PPI (Fase 2/3, ver docstring del modulo); exponerlo antes seria inventar una
    forma de PPI sin acuerdo, justo lo que este contrato existe para evitar."""

    connected: bool
    radials_received: int
    last_volume_number: int | None = None
    last_elevation_number: int | None = None
    last_radial_status: RadialStatus | None = None


class BiteFaultSummary(BaseModel):
    """Una falla activa del System Status & BITE Manager (`core/bite/`), ya
    con hora de pared -- el gateway se la asigna al momento de detectarla
    (AGENTS.md "dos relojes": el reloj monotono de `BiteEvent.at_us` no se
    convierte a hora de pared, se le asigna una nueva al cruzar la
    frontera hacia la MMI, igual que `ControlAuthorityState.since_wall`)."""

    signal_id: SignalId
    detail: str
    since_wall: datetime


class SystemStatusSnapshot(BaseModel):
    control: ControlAuthorityState
    hal_connected: bool
    antenna: AntennaPosition | None = None
    dsp: DspStreamStatus | None = None
    active_bite_faults: list[BiteFaultSummary] = Field(default_factory=list)


# --- WebSocket ----------------------------------------------------------
# Sobre discriminado por "type", siguiendo el mismo patron de canal
# unico usado ya en docs/interfaces/websocket.md de `radar_emulator`
# (no es el mismo contrato: la MMI no habla con el emulador directamente).


class SessionMessage(BaseModel):
    type: Literal["session"] = "session"
    rcp_version: str
    started_at_wall: datetime
    control: ControlAuthorityState


class AntennaMessage(BaseModel):
    type: Literal["antenna"] = "antenna"
    position: AntennaPosition


class OperatorEventMessage(BaseModel):
    type: Literal["event"] = "event"
    seq: int
    at_wall: datetime
    kind: str
    actor: str
    payload: dict[str, object] = Field(default_factory=dict)


class HeartbeatMessage(BaseModel):
    type: Literal["heartbeat"] = "heartbeat"
    at_wall: datetime


class BiteEventMessage(BaseModel):
    """Una transicion (`core/bite/manager.py`) recien detectada -- para el
    BITE Message Window (plan §4.4). El historial/filtrado en si vive del
    lado de la MMI a partir de estos mensajes mas el snapshot inicial de
    `GET /api/status`; el gateway no reenvia el historial completo por WS."""

    type: Literal["bite_event"] = "bite_event"
    signal_id: SignalId
    transition: BiteTransition
    detail: str
    at_wall: datetime


WsMessage = Annotated[
    Union[SessionMessage, AntennaMessage, OperatorEventMessage, HeartbeatMessage, BiteEventMessage],
    Field(discriminator="type"),
]
