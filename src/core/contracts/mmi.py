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


class AccessLevel(StrEnum):
    OP = "OP"
    MANT = "MANT"


class MaintenanceState(BaseModel):
    level: AccessLevel
    actor: str | None = None
    since_wall: datetime | None = None
    expires_wall: datetime | None = None


class UnlockMaintenanceRequest(BaseModel):
    password: str
    actor: str
    duration_s: float


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


class AntennaStepConfig(BaseModel):
    azimuth_step_deg: float = Field(1.0, ge=0.1, le=1.0)
    elevation_step_deg: float = Field(1.0, ge=0.1, le=1.0)


class ProcessInfo(BaseModel):
    pid: int
    name: str
    priority: int
    status: str
    cpu_percent: float
    memory_mb: float


class RcpTaskInfo(BaseModel):
    name: str
    state: Literal["pending", "done", "cancelled"]


class ProcessMonitorSnapshot(BaseModel):
    process: ProcessInfo
    tasks: list[RcpTaskInfo]


class TrendChannelSample(BaseModel):
    at_wall: datetime
    value: float | None


class TrendSeries(BaseModel):
    signal_id: SignalId
    samples: list[TrendChannelSample]


class TrendStartRequest(BaseModel):
    signal_ids: list[SignalId]


class TrendStatus(BaseModel):
    running: bool
    started_at_wall: datetime | None = None
    signal_ids: list[SignalId] = Field(default_factory=list)


class BlankingSector(BaseModel):
    in_use: bool = False
    az_start_deg: float = Field(0.0, ge=0.0, le=360.0)
    az_end_deg: float = Field(0.0, ge=0.0, le=360.0)
    el_start_deg: float = Field(-90.0, ge=-90.0, le=90.0)
    el_end_deg: float = Field(90.0, ge=-90.0, le=90.0)


def default_sectors() -> list[BlankingSector]:
    return [BlankingSector() for _ in range(8)]


class SectorBlankingProfile(BaseModel):
    enabled: bool = False
    sectors: list[BlankingSector] = Field(default_factory=default_sectors)


class ThresholdsConfig(BaseModel):
    log_threshold_db: float = 1.0
    csr_threshold_db: float = -18.0
    sqi_threshold: float = Field(0.3, ge=0.0, le=1.0)
    speckle_remover: bool = True


class ClutterFilterConfig(BaseModel):
    doppler_filter_id: int = 1
    doppler_type_db: str = "default"
    fft_filter_enabled: bool = False
    statistical_filter_enabled: bool = False


class PowerMeasurementLimits(BaseModel):
    """Limites editables por el operador (B7, RAVIS Sec.7.7) -- volatiles hasta
    `POST /api/power-monitor/limits/save` los persiste (mismo criterio que
    `scan_worksheet_path`: JSON en `data/`, gitignored)."""

    forward_limit_kw: float
    reverse_limit_kw: float
    vswr_limit: float


class CalibrationLogEntry(BaseModel):
    """Contrato unificado para el registro de actividades de calibracion (G8, RAVIS Sec.7.4).
    Reutilizado por todas las vistas de la familia G."""

    at_wall: datetime
    severity: Literal["info", "warn", "error"]
    procedure: str
    actor: str
    message: str
    detail: str | None = None


class RcpConfigProfile(BaseModel):
    """Perfiles de configuracion local RCP (E11, RAVIS/RVP §4.1.1 F/S/R).
    Agrupa los parametros de control directo del RCP: limites B7, step config C2/E5,
    sectores de blanking C5, umbrales E3 y filtros de clutter E4."""

    power_limits: PowerMeasurementLimits | None = None
    antenna_step_config: AntennaStepConfig = Field(default_factory=AntennaStepConfig)
    sector_blanking: SectorBlankingProfile = Field(default_factory=SectorBlankingProfile)
    thresholds: ThresholdsConfig = Field(default_factory=ThresholdsConfig)
    clutter_filter: ClutterFilterConfig = Field(default_factory=ClutterFilterConfig)


class PowerMonitorSnapshot(BaseModel):
    """`forward_power_kw`/`reverse_power_kw` en `None` si la lectura Modbus no es
    `SignalQuality.OK` (fuera de rango o excepcion) -- hueco, no dato fabricado.
    `vswr` requiere ambas lecturas OK y forward_power_kw > 0 (si no, `None`:
    no hay VSWR valido sin portadora). `bus_ok` es `hal_connected` (D-06: una
    sola conexion Modbus multiplexada hace de "bus status", no hay Profibus en
    este sistema -- ver docs/alcance/pendientes.md)."""

    forward_power_kw: float | None
    reverse_power_kw: float | None
    vswr: float | None
    bus_ok: bool
    radiating: bool
    # `None` hasta el primer `POST /api/power-monitor/limits` -- ningun limite
    # de fabrica esta confirmado (mismo criterio que PEND-RCP-07), asi que no
    # se fabrica un valor de partida; la MMI debe mostrar "sin limite" en vez
    # de un semaforo con un umbral inventado.
    limits: PowerMeasurementLimits | None


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
    # Hora de pared del ultimo MOMENT_RAY -- ver StatusMessage: es lo que le
    # permite a A6 (RD) distinguir "conectado sin datos hace rato" de datos
    # frescos, en vez de solo `connected`.
    last_radial_at_wall: datetime | None = None


class DspInternalStatusSnapshot(BaseModel):
    """Detalle completo del estado interno del DSP (E12 - V/Vz)."""

    connected: bool
    uptime_s: int
    phase: int
    severity: int
    last_error: int
    n_rx_channels: int
    capability_flags: int
    bite_flags: int
    config_seq: int
    rays_in: int
    rays_out: int
    rays_dropped: int
    queue_depth: int
    bins_ok: int
    bins_total: int
    trigger_period_cmd_ns: int
    trigger_period_meas_ns: int
    noise_floor_dbm: list[float]
    dc_offset_i: list[float]
    dc_offset_q: list[float]
    n_gates: int
    n_pulses: int
    prf_hz: float
    gate_spacing_m: float
    sqi_threshold: float
    sig_threshold: float
    ccor_threshold: float
    log_threshold: float
    rfi_filter: int


class DspResetCountersResponse(BaseModel):
    """Respuesta al reinicio de contadores del DSP (Vz)."""

    status: str
    message: str


class BiteFaultSummary(BaseModel):
    """Una falla activa del System Status & BITE Manager (`core/bite/`), ya
    con hora de pared -- el gateway se la asigna al momento de detectarla
    (AGENTS.md "dos relojes": el reloj monotono de `BiteEvent.at_us` no se
    convierte a hora de pared, se le asigna una nueva al cruzar la
    frontera hacia la MMI, igual que `ControlAuthorityState.since_wall`)."""

    signal_id: SignalId
    detail: str
    since_wall: datetime


class SystemInfo(BaseModel):
    rcp_version: str
    dsp_contract_version: str
    dsp_contract_commit: str
    dsp_contract_commit_date: str
    connected_clients: int


class SystemStatusSnapshot(BaseModel):
    control: ControlAuthorityState
    maintenance: MaintenanceState
    hal_connected: bool
    antenna: AntennaPosition | None = None
    dsp: DspStreamStatus | None = None
    active_bite_faults: list[BiteFaultSummary] = Field(default_factory=list)


class ZeroCheckSnapshot(BaseModel):
    """G5 Zero Check (docs/diseno/inventario-ui.md): muestreo de ruido del receptor.
    Corre automaticamente en boot y a intervalos fijos (interval_s), y se puede lanzar a mano."""

    last_run_at_wall: datetime | None = None
    next_run_at_wall: datetime | None = None
    interval_s: float
    enabled: bool
    noise_high_dbm: float | None = None
    noise_low_dbm: float | None = None
    last_result: RoutineResult | None = None


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


class StatusMessage(BaseModel):
    """A6 (SI/SR/SD/RD, docs/diseno/inventario-ui.md): empuje periodico de
    `hal_connected`/`dsp` por WS, para que la MMI derive el estado `stale`
    (sin datos hace >5s) sin tener que sondear `GET /api/status` ella misma.
    Si este mensaje deja de llegar, eso en si mismo es la señal de `SD`
    caido -- no hace falta un campo aparte para "el canal de estado murio"."""

    type: Literal["status"] = "status"
    at_wall: datetime
    hal_connected: bool
    dsp: DspStreamStatus | None = None


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
    Union[SessionMessage, AntennaMessage, OperatorEventMessage, HeartbeatMessage, BiteEventMessage, StatusMessage],
    Field(discriminator="type"),
]
