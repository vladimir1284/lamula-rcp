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


class SinglePointCalibrationRequest(BaseModel):
    """Solicitud de calibración de punto único (G4)."""

    mode: Literal["auto", "external"] = Field(default="auto", description="Escenario de calibración: auto (generador interno) o external (operador)")
    injected_power_dbm: float | None = Field(default=None, description="Potencia inyectada externamente (dBm)")
    measured_radar_constant_db: float | None = Field(default=None, description="Constante de radar medida manualmente por el operador (dB)")


class MeasuredRadarConstant(BaseModel):
    """Constante de radar medida empíricamente vía G4 (Single Point Calibration).

    Independiente de `RadarConstantParameters`/`RadarConstantSnapshot` (G7, cálculo
    paramétrico) -- PEND-RCP-18 (docs/alcance/pendientes.md) deja abierto si/cómo este
    valor debe alimentar el cálculo operacional que sí llega al DSP/DRX.
    """

    radar_constant_db: float
    mode: Literal["auto", "external"]
    measured_at: datetime


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


class ClutterFilterSettings(BaseModel):
    clutter_filter: Literal["none", "gmap", "notch"] = "gmap"
    clutter_width_ms: float = Field(1.0, ge=0.0, le=50.0, description="Ancho de clutter en m/s (Modelo Gaussiano #5-#7)")
    fixed_win: int = Field(0, description="Ventana del filtro fijo (#1-#3)")
    fixed_width_pts: int = Field(5, description="Ancho en puntos del filtro fijo")
    fixed_edge_pts: int = Field(2, description="Puntos de borde del filtro fijo")
    variable_hunt_pts: int = Field(3, description="Puntos de búsqueda del filtro variable (#4)")
    secondary_sqi_slope: float = 0.0
    secondary_sqi_offset: float = 0.0


class TriggerTimingRow(BaseModel):
    trigger_index: int
    name: str
    start_us: float
    width_us: float
    high: bool = True
    prt_term_enabled: bool = False


class TriggerSetupGeneralSnapshot(BaseModel):
    triggers: list[TriggerTimingRow] = Field(
        default_factory=lambda: [
            TriggerTimingRow(trigger_index=1, name="Trig 1 (Tx)", start_us=0.0, width_us=1.0, high=True),
            TriggerTimingRow(trigger_index=2, name="Trig 2 (Rx)", start_us=0.5, width_us=1.0, high=True),
            TriggerTimingRow(trigger_index=3, name="Trig 3 (Aux)", start_us=1.0, width_us=2.0, high=True),
            TriggerTimingRow(trigger_index=4, name="Trig 4 (Spare)", start_us=2.0, width_us=2.0, high=False),
        ]
    )


class TriggerSetupPwSettings(BaseModel):
    selected_pulse_width: Literal["short", "medium", "long"] = "medium"
    gate_spacing_m: float = Field(150.0, ge=1.0, le=5000.0)
    prf_hz: float = Field(1000.0, ge=50.0, le=20000.0)
    external_pretrigger_delay_us: float = 0.0
    current_noise_level_dbm: float = -110.0
    powerup_noise_level_dbm: float = -112.0
    triggers: list[TriggerTimingRow] = Field(
        default_factory=lambda: [
            TriggerTimingRow(trigger_index=1, name="Trig 1 (Tx)", start_us=0.0, width_us=1.0, high=True),
            TriggerTimingRow(trigger_index=2, name="Trig 2 (Rx)", start_us=0.5, width_us=1.0, high=True),
            TriggerTimingRow(trigger_index=3, name="Trig 3 (Aux)", start_us=1.0, width_us=2.0, high=True),
            TriggerTimingRow(trigger_index=4, name="Trig 4 (Spare)", start_us=2.0, width_us=2.0, high=False),
        ]
    )


class ProcessingOptionsSettings(BaseModel):
    spectral_window: Literal["user", "rect", "hamming", "blackman"] = "user"
    r2_processing: Literal["never", "user", "always"] = "never"
    clutter_microsuppression: Literal["never", "user", "always"] = "never"
    ppp_autocorrels: Literal["never", "user", "always"] = "user"
    unfold_velocity: Literal["never", "user", "always"] = "always"
    process_custom_trigs: Literal["never", "user", "always"] = "never"
    interference_filter: Literal["none", "alg1", "alg2", "alg3"] = "none"
    phidp_offset_deg: float = 0.0


class SpectrumSnapshot(BaseModel):
    has_data: bool = False
    channel: int = 0
    seq: int = 0
    capture_time_utc_ns: int = 0
    center_freq_hz: float = 0.0
    span_hz: float = 0.0
    ref_level_dbm: float = 0.0
    bins: list[float] = Field(default_factory=list)


class BurstAfcSettings(BaseModel):
    # Frecuencias
    tx_if_mhz: float = Field(30.0, description="Frecuencia intermedia del transmisor (MHz)")
    rx_if_mhz: float = Field(30.0, description="Frecuencia intermedia del receptor (MHz)")
    if_increases_approaching: bool = Field(True, description="FI aumenta para blanco que se aproxima")

    # Burst
    phase_lock_burst: Literal["never", "user", "always"] = Field("never", description="PhaseLock al pulso de burst")
    min_burst_power_dbm: float = Field(-10.0, description="Potencia mínima para pulso burst válido (dBm)")
    burst_analysis_window: Literal["rect", "hamming", "blackman"] = Field("hamming", description="Ventana de diseño/análisis de burst")
    burst_estimator_settling_s: float = Field(0.01, description="Tiempo de establecimiento (al 1%) del estimador de frecuencia burst (s)")

    # AFC
    afc_enabled: bool = Field(True, description="Habilitar funciones AFC y MFC")
    afc_servo_mode: Literal["dc_coupled", "motor_integrator"] = Field("dc_coupled", description="Modo del servo AFC")
    afc_wait_time_s: float = Field(1.0, description="Tiempo de espera antes de aplicar AFC (s)")
    afc_hysteresis_inner_khz: float = Field(50.0, description="Histéresis AFC interior (kHz)")
    afc_hysteresis_outer_khz: float = Field(200.0, description="Histéresis AFC exterior (kHz)")
    afc_outer_tolerance_khz: float = Field(100.0, description="Tolerancia exterior AFC durante procesamiento de datos (kHz)")
    afc_feedback_slope: float = Field(1.0, description="Pendiente de realimentación AFC")
    afc_slew_rate_min: float = Field(0.1, description="Slew rate mínimo AFC")
    afc_slew_rate_max: float = Field(10.0, description="Slew rate máximo AFC")
    afc_state: str = Field("disabled", description="Estado de lazo AFC (ej. disabled, manual, no_burst, wait, track, locked)")

    # AFC eléctrico
    afc_format: Literal["bin", "bcd", "8b4d"] = Field("bin", description="Formato de la palabra AFC")
    afc_format_act_low: bool = Field(False, description="Polaridad activa en bajo del formato AFC")
    afc_uplink_protocol: Literal["off", "normal", "pin_map"] = Field("normal", description="Protocolo de uplink AFC")
    fault_status_pin: int = Field(1, description="Pin de estado FAULT")
    fault_pin_act_low: bool = Field(False, description="Pin FAULT activo en bajo")
    burst_freq_increases_with_afc_volts: bool = Field(True, description="Frecuencia burst aumenta con mayor tensión AFC")

    # Seguimiento
    enable_burst_tracking: Literal["never", "user", "always"] = Field("never", description="Habilitar seguimiento de pulso burst")
    enable_missing_burst_hunt: Literal["never", "user", "always"] = Field("never", description="Habilitar búsqueda de tiempo/frecuencia para burst perdido")
    search_freq_intervals: int = Field(5, description="Número de intervalos de frecuencia a buscar")
    hop_settling_time_s: float = Field(0.05, description="Tiempo de establecimiento por salto de frecuencia (s)")
    auto_hunt_on_reset: bool = Field(False, description="Búsqueda automática inmediatamente tras reset")
    repeat_auto_hunt_s: float = Field(10.0, description="Repetir búsqueda automática cada N segundos (s)")

    # Calibración
    burst_power_z0_correction: Literal["never", "user", "always"] = Field("never", description="Habilitar corrección de Z0 basada en potencia de burst")

    # Simulación
    simulate_burst_samples: bool = Field(False, description="Simular muestras de pulso burst")
    simulated_burst_span_start_mhz: float = Field(25.0, description="Span de frecuencia simulada inicio (MHz)")
    simulated_burst_span_stop_mhz: float = Field(35.0, description="Span de frecuencia simulada fin (MHz)")


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


class RadarConstantParameters(BaseModel):
    pulse_width_us: float
    zero_check_high_dbm: float
    zero_check_low_dbm: float
    tx_losses_db: float
    rx_losses_db: float
    radome_losses_db: float
    atmospheric_attenuation_db_km: float
    horizontal_beam_width_deg: float
    vertical_beam_width_deg: float
    antenna_gain_db: float
    wavelength_cm: float
    noise_figure_db: float | None = None
    filter_init_pulses: int


class RadarConstantSnapshot(BaseModel):
    params: RadarConstantParameters
    radar_constant_db: float


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


class WizardStepInputRequest(BaseModel):
    """Payload genérico para avanzar un paso interactivo en un wizard job."""

    data: dict[str, object] = Field(default_factory=dict)


class ControlJobStatus(StrEnum):
    RUNNING = "running"
    AWAITING_OPERATOR_INPUT = "awaiting_operator_input"
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
    mientras `status == RUNNING` o `AWAITING_OPERATOR_INPUT`. `error` distingue una excepcion inesperada
    (p.ej. el HAL se desconecto a mitad de camino) de un `RoutineResult` con
    `outcome` en `failed`/`interrupted`, que es un resultado legitimo de la
    rutina, no un error de infraestructura."""

    job_id: str
    routine: str
    status: ControlJobStatus
    current_step: int | None = None
    total_steps: int | None = None
    step_name: str | None = None
    prompt: str | None = None
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


class TxSamplingAdjustParams(BaseModel):
    """Parametros de ajuste de muestreo TX (G2, RAVIS Sec.7.4.1 -- TX/RX adjustment)."""

    tx_sample: float
    tx_frequency_mhz: float
    commanded_lo_freq_mhz: float
    tx_start_sample: float
    tx_stop_sample: float


class TxSamplingAdjustSnapshot(BaseModel):
    """Snapshot de ajuste de muestreo TX (G2) con lecturas vivas de Modbus + parametros
    comandados. Lecturas HAL en `None` si la lectura no es OK (stale/error de bus)."""

    tx_sample_readout: float | None = None
    tx_frequency_readout_mhz: float | None = None
    commanded_lo_freq_readout_mhz: float | None = None
    tx_start_sample_readout: float | None = None
    tx_stop_sample_readout: float | None = None
    bus_ok: bool = True
    radiating: bool = False
    params: TxSamplingAdjustParams | None = None


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
