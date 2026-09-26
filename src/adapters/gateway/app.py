"""Gateway RCP<->MMI (Fase 1, esqueleto): FastAPI sobre el sobre REST/WS ya
congelado en `src/core/contracts/mmi.py` -- primer "pipe de datos en vivo
sim->WS->PPI" de docs/implementacion/fases.md.

Este modulo es un adaptador: importa `src/core/` (estado de sesion),
`src/adapters/hal_sim` (posicion de antena) y `src/adapters/dsp` (estado
resumido del stream de momentos), nunca al reves (AGENTS.md). No incluye
autenticacion ni persistencia de sesion. El log de eventos
(`OperatorEventMessage`) solo llega a los WS conectados en el momento del
evento; no hay buffer de reconexion -- marcar PEND si Fase 2 lo necesita.

Decision 2026-08-19: el stream DSP se integra solo como estado resumido
(`DspStreamStatus` en `/api/status`), no como mensajes WS de momentos --
eso queda para cuando se diseñe la vista PPI (Fase 2/3), ver
`core/contracts/mmi.py`.
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import re
import psutil
import tomllib
import uuid
from collections import deque
from collections.abc import Coroutine
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import TypeAdapter

from adapters.dsp import MomentStreamReceiver
from adapters.hal_sim import SimulatedHAL
from adapters.hal_sim.signal_catalog import CATALOG
from core.bite import BiteManager
from core.contracts.bite import BiteTransition
from core.contracts.common import SignalQuality
from core.contracts.control import RoutineOutcome, RoutineResult
from core.contracts.mmi import (
    AccessLevel,
    CalibrationLogEntry,
    ZeroCheckSnapshot,
    AntennaMessage,
    AntennaMovementRequest,
    AntennaPositioningRequest,
    AntennaStepConfig,
    AntennaUnitPowerOnRequest,
    BiteEventMessage,
    BiteFaultSummary,
    BlankingSector,
    ControlAuthorityState,
    ControlJobAccepted,
    ControlJobStatus,
    ControlJobStatusResponse,
    DspInternalStatusSnapshot,
    DspResetCountersResponse,
    DspStreamStatus,
    HeartbeatMessage,
    MaintenanceState,
    MeasuredRadarConstant,
    OperatorEventMessage,
    OperatorMode,
    BurstAfcSettings,
    SpectrumSnapshot,
    ClutterFilterConfig,
    ClutterFilterSettings,
    TriggerSetupGeneralSnapshot,
    TriggerSetupPwSettings,
    ProcessingOptionsSettings,
    PowerMeasurementLimits,
    PowerMonitorSnapshot,
    RadarConstantParameters,
    RadarConstantSnapshot,
    ProcessInfo,
    ProcessMonitorSnapshot,
    RcpConfigProfile,
    RcpTaskInfo,
    ReceiverPowerOnRequest,
    ScanCutExecutionRequest,
    SectorBlankingProfile,
    SessionMessage,
    SetControlModeRequest,
    SinglePointCalibrationRequest,
    StatusMessage,
    SystemInfo,
    SystemStatusSnapshot,
    ThresholdsConfig,
    TransmitterPowerOnRequest,
    TrendChannelSample,
    TrendSeries,
    TrendStartRequest,
    TrendStatus,
    TxSamplingAdjustParams,
    TxSamplingAdjustSnapshot,
    UnlockMaintenanceRequest,
    WizardStepInputRequest,
    WsMessage,
)
from core.contracts.scan import ScanCut, ScanCutResult
from core.control_routines import (
    run_antenna_movement,
    run_antenna_positioning,
    run_antenna_unit_power_on,
    run_general_power_on,
    run_receiver_power_on,
    run_single_point_calibration,
    run_transmitter_power_on,
    run_tx_power_calibration,
    run_zero_check,
)
from core.scan_controller import run_scan_cut
from core.session import ControlAuthority

RCP_VERSION = "0.0.0"  # PEND: version real (pyproject/build info), no hay pipeline de release todavia
RCP_MAINTENANCE_PASSWORD = os.getenv("RCP_MAINTENANCE_PASSWORD", "mant1234")  # PEND-RCP-15
UPSTREAM_PIN = Path(__file__).resolve().parents[3] / "contract" / "vendor" / "UPSTREAM.toml"

# Throttle deliberado: el encoder UDP emite a 100 Hz (nominal), la MMI no
# necesita esa cadencia para el PPI. Ver radar_emulator/docs/interfaces/udp-encoder.md.
WS_ANTENNA_PERIOD_S = 0.1
WS_HEARTBEAT_PERIOD_S = 1.0
# A6 (docs/diseno/inventario-ui.md): cadencia del push de hal_connected/dsp
# por WS. 1 Hz alcanza para un umbral de "stale" de 5 s con margen.
WS_STATUS_PERIOD_S = 1.0
# core/bite/manager.py hace hasta 20 lecturas Modbus por poll (una por señal
# monitoreada) -- no son condiciones de tiempo duro, 2 Hz alcanza sin competir
# con el resto del trafico Modbus (posicionamiento de antena, etc.).
BITE_POLL_PERIOD_S = 0.5


SCAN_WORKSHEET_LIST_ADAPTER = TypeAdapter(list[ScanCut])

DEFAULT_RADAR_CONSTANT_PARAMS = RadarConstantParameters(
    pulse_width_us=1.0,
    zero_check_high_dbm=-75.0,
    zero_check_low_dbm=-80.0,
    tx_losses_db=1.5,
    rx_losses_db=1.5,
    radome_losses_db=0.5,
    atmospheric_attenuation_db_km=0.016,
    horizontal_beam_width_deg=0.95,
    vertical_beam_width_deg=0.95,
    antenna_gain_db=45.0,
    wavelength_cm=5.33,
    noise_figure_db=2.5,
    filter_init_pulses=4,
)


def compute_radar_constant_db(params: RadarConstantParameters) -> float:
    c_m_s = 2.99792458e8
    wavelength_m = params.wavelength_cm / 100.0
    theta_rad = math.radians(params.horizontal_beam_width_deg)
    phi_rad = math.radians(params.vertical_beam_width_deg)
    h_m = c_m_s * (params.pulse_width_us * 1e-6)
    k2 = 0.93  # |K|^2 para agua liquida

    const_factor = (math.pi ** 3 * k2) / (1024.0 * math.log(2.0))
    c_lin = (
        const_factor
        * (10.0 ** (2.0 * params.antenna_gain_db / 10.0))
        * theta_rad
        * phi_rad
        * h_m
        / ((wavelength_m ** 2) * (10.0 ** ((params.tx_losses_db + params.rx_losses_db + params.radome_losses_db) / 10.0)))
    )
    return round(10.0 * math.log10(c_lin), 2)


CALIBRATION_LOG_LIMIT = 200  # mismo criterio que MAX_LOG en useGateway.ts -- evita crecimiento sin limite


def _record_calibration_log(app: FastAPI, entry: CalibrationLogEntry) -> None:
    app.state.calibration_log.append(entry)
    if len(app.state.calibration_log) > CALIBRATION_LOG_LIMIT:
        app.state.calibration_log = app.state.calibration_log[-CALIBRATION_LOG_LIMIT:]


def create_app(
    hal: SimulatedHAL,
    dsp: MomentStreamReceiver,
    dsp_bind_host: str,
    dsp_port: int,
    scan_worksheet_path: Path = Path("data/scan_worksheet.json"),
    power_limits_path: Path = Path("data/power_limits.json"),
    sector_blanking_path: Path = Path("data/sector_blanking.json"),
    config_profile_path: Path = Path("data/config_profile.json"),
    radar_constant_path: Path = Path("data/radar_constant.json"),
    measured_radar_constant_path: Path = Path("data/measured_radar_constant.json"),
    tx_sampling_adjust_path: Path = Path("data/tx_sampling_adjust.json"),
) -> FastAPI:
    async def _bite_poll_loop(app: FastAPI) -> None:
        while True:
            try:
                events = await app.state.bite.poll(hal)
                now = datetime.now(timezone.utc)
                for event in events:
                    if event.transition is BiteTransition.FAULT:
                        app.state.bite_since_wall[event.signal_id] = now
                    else:
                        app.state.bite_since_wall.pop(event.signal_id, None)
                    await _broadcast(
                        app,
                        BiteEventMessage(signal_id=event.signal_id, transition=event.transition, detail=event.detail, at_wall=now),
                    )
            except (ConnectionError, RuntimeError):
                pass
            await asyncio.sleep(BITE_POLL_PERIOD_S)

    async def _trend_sample_loop(app: FastAPI) -> None:
        while True:
            try:
                if app.state.trend_running:
                    now = datetime.now(timezone.utc)
                    if app.state.trend_started_at and (now - app.state.trend_started_at) > timedelta(hours=8):
                        app.state.trend_running = False
                    else:
                        for sig in app.state.trend_channels:
                            try:
                                reading = await hal.read_analog(sig)
                                val = reading.value if reading.quality == SignalQuality.OK else None
                            except Exception:
                                val = None
                            sample = TrendChannelSample(at_wall=now, value=val)
                            if sig not in app.state.trend_buffers:
                                app.state.trend_buffers[sig] = deque(maxlen=28800)
                            app.state.trend_buffers[sig].append(sample)
            except Exception:
                pass
            await asyncio.sleep(1.0)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            if not hal.is_connected():
                await hal.connect()
        except ConnectionError:
            pass
        await dsp.start(dsp_bind_host, dsp_port)
        bite_task = asyncio.create_task(_bite_poll_loop(app))
        trend_task = asyncio.create_task(_trend_sample_loop(app))
        try:
            yield
        finally:
            bite_task.cancel()
            trend_task.cancel()
            try:
                await bite_task
            except asyncio.CancelledError:
                pass
            try:
                await trend_task
            except asyncio.CancelledError:
                pass
            if hal.is_connected():
                await hal.disconnect()
            await dsp.stop()

    app = FastAPI(title="lamula-rcp gateway", lifespan=lifespan)
    # PEND: red air-gapped de un solo operador (AGENTS.md) -- "*" es aceptable
    # para el dev server de Vite hoy; revisar si Fase 4 (empaquetado) exige
    # restringir origenes.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.hal = hal
    app.state.dsp = dsp
    app.state.control = ControlAuthority()
    app.state.maintenance = MaintenanceState(level=AccessLevel.OP)
    app.state.started_at = datetime.now(timezone.utc)
    app.state.event_seq = 0
    app.state.websockets: set[WebSocket] = set()
    app.state.bite = BiteManager()
    # hora de pared de cuando cada falla activa se detecto -- BiteEvent.at_us es
    # reloj monotono (core, "dos relojes"), esta es la asignada por el gateway al
    # cruzar la frontera hacia la MMI, igual que ControlAuthorityState.since_wall.
    app.state.bite_since_wall: dict[str, datetime] = {}
    # Scan Worksheet manual (plan Sec.8.2 Fase 2, core/contracts/scan.py):
    # persistido a un JSON en disco (`scan_worksheet_path`, `data/` gitignored --
    # un solo operador/instancia, sin necesidad de DB). Se carga una vez al
    # arrancar el proceso, se reescribe entero en cada mutacion (_save_scan_worksheet
    # mas abajo) -- suficiente para el tamaño de un worksheet manual, no pensado
    # para escritura concurrente de multiples operadores. Un archivo ausente o
    # corrupto arranca en lista vacia en vez de tumbar el proceso (mismo nivel de
    # esqueleto que el resto del gateway); PEND: todavia sin sincronizacion entre
    # pestanas/operadores en vivo (cada cliente solo ve lo que el mismo trajo por
    # GET, no hay broadcast por WS de esto).
    app.state.scan_worksheet_path = scan_worksheet_path
    try:
        app.state.scan_worksheet: list[ScanCut] = SCAN_WORKSHEET_LIST_ADAPTER.validate_python(
            json.loads(scan_worksheet_path.read_text())
        )
    except (FileNotFoundError, ValueError):
        app.state.scan_worksheet: list[ScanCut] = []
    # Limites de potencia editables (B7) -- mismo criterio de persistencia que
    # scan_worksheet_path arriba. Archivo ausente o corrupto arranca en `None`
    # ("sin limite"), no en un umbral inventado (ver docstring de
    # PowerMonitorSnapshot.limits).
    app.state.power_limits_path = power_limits_path
    try:
        app.state.power_limits: PowerMeasurementLimits | None = PowerMeasurementLimits.model_validate_json(
            power_limits_path.read_text()
        )
    except (FileNotFoundError, ValueError):
        app.state.power_limits: PowerMeasurementLimits | None = None

    app.state.sector_blanking_path = sector_blanking_path
    try:
        app.state.sector_blanking: SectorBlankingProfile = SectorBlankingProfile.model_validate_json(
            sector_blanking_path.read_text()
        )
    except (FileNotFoundError, ValueError):
        app.state.sector_blanking = SectorBlankingProfile()
    app.state.radar_constant_path = radar_constant_path
    try:
        app.state.radar_constant_params = RadarConstantParameters.model_validate_json(
            radar_constant_path.read_text()
        )
    except (FileNotFoundError, ValueError):
        app.state.radar_constant_params = DEFAULT_RADAR_CONSTANT_PARAMS
    app.state.measured_radar_constant_path = measured_radar_constant_path
    try:
        app.state.measured_radar_constant: MeasuredRadarConstant | None = MeasuredRadarConstant.model_validate_json(
            measured_radar_constant_path.read_text()
        )
    except (FileNotFoundError, ValueError):
        app.state.measured_radar_constant = None
    app.state.tx_sampling_adjust_path = tx_sampling_adjust_path
    try:
        app.state.tx_sampling_adjust_params: TxSamplingAdjustParams | None = (
            TxSamplingAdjustParams.model_validate_json(tx_sampling_adjust_path.read_text())
        )
    except (FileNotFoundError, ValueError):
        app.state.tx_sampling_adjust_params: TxSamplingAdjustParams | None = None
    # Jobs asincronos de los seis POST /api/control/* (ver _start_control_job mas
    # abajo) -- dict ordinario, el orden de inserccion de Python 3.7+ es lo que
    # usa el tope de historial para descartar el mas viejo. En memoria, se pierde
    # al reiniciar el gateway, mismo nivel de esqueleto que el resto del estado.
    app.state.control_jobs: dict[str, ControlJobStatusResponse] = {}
    # Task real detras de cada job -- separado de control_jobs (que solo
    # guarda el estado ya serializable) porque POST /api/control/jobs/{id}/cancel
    # necesita el objeto asyncio.Task para poder cancelarlo. Comparte tope de
    # historial con control_jobs (misma job_id, podado junto en el mismo
    # punto mas abajo) en vez de tener el suyo propio.
    app.state.control_job_tasks: dict[str, asyncio.Task[None]] = {}
    # job_id de jobs cancelados a proposito -- distingue "esta excepcion es la
    # cancelacion pedida por el operador, solo que pymodbus la envolvio en su
    # propia excepcion en vez de un CancelledError limpio" de un error de
    # infraestructura genuino, ambos indistinguibles por tipo en `_run` de
    # `_start_control_job` mas abajo. Mismo tope de historial que
    # control_jobs/control_job_tasks.
    app.state.control_job_cancel_requested: set[str] = set()
    app.state.antenna_step_config = AntennaStepConfig()
    app.state.trend_running: bool = False
    app.state.trend_channels: list[str] = []
    app.state.trend_buffers: dict[str, deque[TrendChannelSample]] = {}
    app.state.trend_started_at: datetime | None = None

    app.state.zero_check_last_run_at_wall: datetime | None = None
    app.state.zero_check_next_run_at_wall: datetime | None = None
    app.state.zero_check_interval_s: float = 3600.0
    app.state.zero_check_noise_high_dbm: float | None = None
    app.state.zero_check_noise_low_dbm: float | None = None
    app.state.zero_check_last_result: RoutineResult | None = None

    app.state.calibration_log: list[CalibrationLogEntry] = []
    app.state.control_job_inputs: dict[str, asyncio.Queue[dict[str, Any]]] = {}
    app.state.radiating_since_wall: datetime | None = None

    # Perfiles de configuracion local (E11)
    app.state.config_profile_path = config_profile_path
    app.state.thresholds = ThresholdsConfig()
    app.state.clutter_filter = ClutterFilterConfig()
    app.state.clutter_filter_settings = ClutterFilterSettings()
    app.state.trigger_setup_general = TriggerSetupGeneralSnapshot()
    app.state.trigger_pw_settings = TriggerSetupPwSettings()
    app.state.processing_options_settings = ProcessingOptionsSettings()
    app.state.burst_afc_settings = BurstAfcSettings()

    def _get_current_profile() -> RcpConfigProfile:
        return RcpConfigProfile(
            power_limits=app.state.power_limits,
            antenna_step_config=app.state.antenna_step_config,
            sector_blanking=app.state.sector_blanking,
            thresholds=app.state.thresholds,
            clutter_filter=app.state.clutter_filter,
        )

    def _apply_profile(profile: RcpConfigProfile) -> None:
        app.state.power_limits = profile.power_limits
        app.state.antenna_step_config = profile.antenna_step_config
        app.state.sector_blanking = profile.sector_blanking
        app.state.thresholds = profile.thresholds
        app.state.clutter_filter = profile.clutter_filter

    try:
        saved_prof = RcpConfigProfile.model_validate_json(config_profile_path.read_text())
        app.state.saved_profile: RcpConfigProfile = saved_prof
        _apply_profile(saved_prof)
    except (FileNotFoundError, ValueError):
        app.state.saved_profile = _get_current_profile()

    try:
        upstream_data = tomllib.loads(UPSTREAM_PIN.read_text(encoding="utf-8"))
        dsp_ver = f"v{upstream_data['contract']['version_major']}.{upstream_data['contract']['version_minor']}"
        dsp_commit = upstream_data["upstream"]["commit"]
        dsp_date = upstream_data["upstream"]["commit_date"]
    except Exception:
        dsp_ver = "desconocida"
        dsp_commit = "desconocido"
        dsp_date = "desconocida"

    def _dsp_status() -> DspStreamStatus:
        latest = dsp.latest
        return DspStreamStatus(
            connected=dsp.connected,
            radials_received=dsp.radials_received,
            last_volume_number=latest.volume_number if latest else None,
            last_elevation_number=latest.elevation_number if latest else None,
            last_radial_status=latest.radial_status if latest else None,
            last_radial_at_wall=dsp.last_radial_at,
        )

    def _active_bite_faults() -> list[BiteFaultSummary]:
        return [
            BiteFaultSummary(
                signal_id=f.signal_id,
                detail=f.detail,
                since_wall=app.state.bite_since_wall.get(f.signal_id, datetime.now(timezone.utc)),
            )
            for f in app.state.bite.active_faults()
        ]

    def _effective_maintenance() -> MaintenanceState:
        m: MaintenanceState = app.state.maintenance
        if m.level == AccessLevel.MANT and m.expires_wall is not None:
            now = datetime.now(timezone.utc)
            if now >= m.expires_wall:
                m = MaintenanceState(level=AccessLevel.OP)
                app.state.maintenance = m
                app.state.event_seq += 1
                event = OperatorEventMessage(
                    seq=app.state.event_seq,
                    at_wall=now,
                    kind="maintenance_expired",
                    actor="system",
                    payload={"level": AccessLevel.OP.value},
                )
                asyncio.create_task(_broadcast(app, event))
        return m

    def _dsp_internal_status() -> DspInternalStatusSnapshot:
        st = dsp.latest_status
        cfg = dsp.latest_config
        ray = dsp.latest

        if st is not None:
            uptime_s = st.uptime_s
            phase = st.phase
            severity = st.severity
            last_error = st.last_error
            n_rx_channels = st.n_rx_channels
            capability_flags = st.capability_flags
            bite_flags = st.bite_flags
            config_seq = st.config_seq
            rays_in = st.rays_in
            rays_out = st.rays_out
            rays_dropped = st.rays_dropped
            queue_depth = st.queue_depth
            bins_ok = st.bins_ok
            bins_total = st.bins_total
            trigger_period_cmd_ns = st.trigger_period_cmd_ns
            trigger_period_meas_ns = st.trigger_period_meas_ns
            noise_floor_dbm = [
                st.noise_floor_dbm_0,
                st.noise_floor_dbm_1,
                st.noise_floor_dbm_2,
                st.noise_floor_dbm_3,
            ]
            dc_offset_i = [
                st.dc_offset_i_0,
                st.dc_offset_i_1,
                st.dc_offset_i_2,
                st.dc_offset_i_3,
            ]
            dc_offset_q = [
                st.dc_offset_q_0,
                st.dc_offset_q_1,
                st.dc_offset_q_2,
                st.dc_offset_q_3,
            ]
        else:
            uptime_s = 0
            phase = 1 if dsp.connected else 0
            severity = 0
            last_error = 0
            n_rx_channels = 2
            capability_flags = 0x01FF
            bite_flags = 0
            config_seq = 1
            rays_in = dsp.radials_received
            rays_out = dsp.radials_received
            rays_dropped = 0
            queue_depth = 0
            bins_ok = 1000 * dsp.radials_received
            bins_total = 1000 * dsp.radials_received
            trigger_period_cmd_ns = 1_000_000
            trigger_period_meas_ns = 1_000_000
            noise_floor_dbm = [-112.0, -112.5, -112.0, -112.5]
            dc_offset_i = [0.001, 0.002, 0.001, 0.002]
            dc_offset_q = [0.001, 0.001, 0.001, 0.001]

        if cfg is not None:
            n_gates = cfg.n_gates
            n_pulses = cfg.n_pulses
            prf_hz = cfg.prf_hz
            gate_spacing_m = cfg.gate_spacing_m
            sqi_threshold = cfg.sqi_threshold
            sig_threshold = cfg.sig_threshold
            ccor_threshold = cfg.ccor_threshold
            log_threshold = cfg.log_threshold
            rfi_filter = cfg.rfi_filter
        else:
            n_gates = 1000
            n_pulses = 64
            prf_hz = ray.prf_hz if ray is not None else 1000.0
            gate_spacing_m = 150.0
            sqi_threshold = 0.25
            sig_threshold = 3.0
            ccor_threshold = 1.0
            log_threshold = 2.0
            rfi_filter = 0

        return DspInternalStatusSnapshot(
            connected=dsp.connected,
            uptime_s=uptime_s,
            phase=phase,
            severity=severity,
            last_error=last_error,
            n_rx_channels=n_rx_channels,
            capability_flags=capability_flags,
            bite_flags=bite_flags,
            config_seq=config_seq,
            rays_in=rays_in,
            rays_out=rays_out,
            rays_dropped=rays_dropped,
            queue_depth=queue_depth,
            bins_ok=bins_ok,
            bins_total=bins_total,
            trigger_period_cmd_ns=trigger_period_cmd_ns,
            trigger_period_meas_ns=trigger_period_meas_ns,
            noise_floor_dbm=noise_floor_dbm,
            dc_offset_i=dc_offset_i,
            dc_offset_q=dc_offset_q,
            n_gates=n_gates,
            n_pulses=n_pulses,
            prf_hz=prf_hz,
            gate_spacing_m=gate_spacing_m,
            sqi_threshold=sqi_threshold,
            sig_threshold=sig_threshold,
            ccor_threshold=ccor_threshold,
            log_threshold=log_threshold,
            rfi_filter=rfi_filter,
        )

    @app.get("/api/dsp/internal-status", response_model=DspInternalStatusSnapshot)
    async def get_dsp_internal_status() -> DspInternalStatusSnapshot:
        return _dsp_internal_status()

    @app.get("/api/dsp/trigger-setup-general", response_model=TriggerSetupGeneralSnapshot)
    async def get_trigger_setup_general() -> TriggerSetupGeneralSnapshot:
        return app.state.trigger_setup_general

    @app.get("/api/dsp/clutter-filters", response_model=ClutterFilterSettings)
    async def get_clutter_filters() -> ClutterFilterSettings:
        cfg = dsp.latest_config
        settings = app.state.clutter_filter_settings
        if cfg is not None:
            filter_map = {0: "none", 1: "gmap", 2: "notch"}
            if isinstance(cfg.clutter_filter, int) and cfg.clutter_filter in filter_map:
                settings.clutter_filter = filter_map[cfg.clutter_filter]  # type: ignore[assignment]
            settings.clutter_width_ms = cfg.clutter_width_ms
        return settings

    @app.post("/api/dsp/clutter-filters", response_model=ClutterFilterSettings)
    async def set_clutter_filters(settings: ClutterFilterSettings) -> ClutterFilterSettings:
        # `clutter_filter`/`clutter_width_ms` son telemetria del DSP (RcpDspConfig,
        # `dsp.latest_config`, sin path de escritura RCP->DSP hoy -- ver
        # docs/diseno/pendientes-p1.md "familia E"). Solo se persisten en memoria
        # los campos maquetados (#1-#4); los reales se re-derivan de la telemetria
        # para que este endpoint no pueda hacer creer que quedaron guardados.
        cfg = dsp.latest_config
        if cfg is not None:
            filter_map = {0: "none", 1: "gmap", 2: "notch"}
            if isinstance(cfg.clutter_filter, int) and cfg.clutter_filter in filter_map:
                settings.clutter_filter = filter_map[cfg.clutter_filter]  # type: ignore[assignment]
            settings.clutter_width_ms = cfg.clutter_width_ms
        app.state.clutter_filter_settings = settings
        return settings

    @app.get("/api/dsp/trigger-setup-pw", response_model=TriggerSetupPwSettings)
    async def get_trigger_setup_pw() -> TriggerSetupPwSettings:
        cfg = dsp.latest_config
        settings = app.state.trigger_pw_settings
        if cfg is not None:
            settings.gate_spacing_m = cfg.gate_spacing_m
            settings.prf_hz = cfg.prf_hz
        return settings

    @app.post("/api/dsp/trigger-setup-pw", response_model=TriggerSetupPwSettings)
    async def set_trigger_setup_pw(settings: TriggerSetupPwSettings) -> TriggerSetupPwSettings:
        # `gate_spacing_m`/`prf_hz` son telemetria del DSP -- mismo criterio que
        # `set_clutter_filters`: no hay path de escritura, se re-derivan de
        # `dsp.latest_config` en vez de aceptar el valor enviado como si fuera a
        # aplicarse al hardware.
        cfg = dsp.latest_config
        if cfg is not None:
            settings.gate_spacing_m = cfg.gate_spacing_m
            settings.prf_hz = cfg.prf_hz
        app.state.trigger_pw_settings = settings
        return settings

    @app.get("/api/dsp/processing-options", response_model=ProcessingOptionsSettings)
    async def get_processing_options() -> ProcessingOptionsSettings:
        cfg = dsp.latest_config
        settings = app.state.processing_options_settings
        if cfg is not None and hasattr(cfg, "phidp_offset_deg"):
            settings.phidp_offset_deg = cfg.phidp_offset_deg
        return settings

    @app.post("/api/dsp/processing-options", response_model=ProcessingOptionsSettings)
    async def set_processing_options(settings: ProcessingOptionsSettings) -> ProcessingOptionsSettings:
        # `phidp_offset_deg` es telemetria del DSP -- mismo criterio que
        # `set_clutter_filters`/`set_trigger_setup_pw`.
        cfg = dsp.latest_config
        if cfg is not None and hasattr(cfg, "phidp_offset_deg"):
            settings.phidp_offset_deg = cfg.phidp_offset_deg
        app.state.processing_options_settings = settings
        return settings

    @app.get("/api/dsp/burst-afc", response_model=BurstAfcSettings)
    async def get_burst_afc() -> BurstAfcSettings:
        return app.state.burst_afc_settings

    @app.post("/api/dsp/burst-afc", response_model=BurstAfcSettings)
    async def set_burst_afc(settings: BurstAfcSettings) -> BurstAfcSettings:
        app.state.burst_afc_settings = settings
        return settings

    @app.post("/api/dsp/request-spectrum", response_model=DspResetCountersResponse)
    async def request_dsp_spectrum() -> DspResetCountersResponse:
        if _effective_maintenance().level != AccessLevel.MANT:
            raise HTTPException(
                status_code=403,
                detail="se requiere nivel de mantenimiento para esta operación",
            )
        await dsp.request_spectrum()
        return DspResetCountersResponse(
            status="ok", message="Comando REQUEST_SPECTRUM enviado al DSP"
        )

    @app.get("/api/dsp/spectrum", response_model=SpectrumSnapshot)
    async def get_dsp_spectrum() -> SpectrumSnapshot:
        spec = dsp.latest_spectrum
        if spec is None:
            return SpectrumSnapshot(has_data=False)
        (
            _n_bins,
            channel,
            seq,
            capture_time_utc_ns,
            center_freq_hz,
            span_hz,
            ref_level_dbm,
            bins,
        ) = spec
        return SpectrumSnapshot(
            has_data=True,
            channel=channel,
            seq=seq,
            capture_time_utc_ns=capture_time_utc_ns,
            center_freq_hz=center_freq_hz,
            span_hz=span_hz,
            ref_level_dbm=ref_level_dbm,
            bins=bins,
        )

    @app.post("/api/dsp/reset-counters", response_model=DspResetCountersResponse)
    async def reset_dsp_counters() -> DspResetCountersResponse:
        if _effective_maintenance().level != AccessLevel.MANT:
            raise HTTPException(
                status_code=403,
                detail="se requiere nivel de mantenimiento para esta operación",
            )
        await dsp.reset_counters()
        now = datetime.now(timezone.utc)
        app.state.event_seq += 1
        event = OperatorEventMessage(
            seq=app.state.event_seq,
            at_wall=now,
            kind="dsp_reset_counters",
            actor="operator",
            payload={},
        )
        await _broadcast(app, event)
        return DspResetCountersResponse(
            status="ok",
            message="Contadores del DSP reiniciados correctamente",
        )

    @app.get("/api/system-info", response_model=SystemInfo)
    async def get_system_info() -> SystemInfo:
        return SystemInfo(
            rcp_version=RCP_VERSION,
            dsp_contract_version=dsp_ver,
            dsp_contract_commit=dsp_commit,
            dsp_contract_commit_date=dsp_date,
            connected_clients=len(app.state.websockets),
        )

    @app.get("/api/status", response_model=SystemStatusSnapshot)
    async def get_status() -> SystemStatusSnapshot:
        antenna = None
        try:
            antenna = await hal.read_antenna_position()
        except (RuntimeError, ConnectionError):
            antenna = None  # sin paquete de encoder todavia, o stream perdido
        return SystemStatusSnapshot(
            control=app.state.control.state,
            maintenance=_effective_maintenance(),
            hal_connected=hal.is_connected(),
            antenna=antenna,
            dsp=_dsp_status(),
            active_bite_faults=_active_bite_faults(),
        )

    @app.post("/api/maintenance/unlock", response_model=MaintenanceState)
    async def unlock_maintenance(req: UnlockMaintenanceRequest) -> MaintenanceState:
        if req.password != RCP_MAINTENANCE_PASSWORD:
            raise HTTPException(status_code=403, detail="contraseña de mantenimiento incorrecta")
        now = datetime.now(timezone.utc)
        expires_wall = now + timedelta(seconds=req.duration_s)
        state = MaintenanceState(
            level=AccessLevel.MANT,
            actor=req.actor,
            since_wall=now,
            expires_wall=expires_wall,
        )
        app.state.maintenance = state
        app.state.event_seq += 1
        event = OperatorEventMessage(
            seq=app.state.event_seq,
            at_wall=now,
            kind="maintenance_unlocked",
            actor=req.actor,
            payload={"level": AccessLevel.MANT.value, "duration_s": req.duration_s},
        )
        await _broadcast(app, event)
        return state

    @app.post("/api/maintenance/lock", response_model=MaintenanceState)
    async def lock_maintenance() -> MaintenanceState:
        state = MaintenanceState(level=AccessLevel.OP)
        app.state.maintenance = state
        app.state.event_seq += 1
        event = OperatorEventMessage(
            seq=app.state.event_seq,
            at_wall=datetime.now(timezone.utc),
            kind="maintenance_locked",
            actor="system",
            payload={"level": AccessLevel.OP.value},
        )
        await _broadcast(app, event)
        return state

    @app.post("/api/control", response_model=ControlAuthorityState)
    async def set_control(req: SetControlModeRequest) -> ControlAuthorityState:
        state = app.state.control.set_mode(req.mode, req.actor)
        app.state.event_seq += 1
        event = OperatorEventMessage(
            seq=app.state.event_seq,
            at_wall=datetime.now(timezone.utc),
            kind="control_mode_changed",
            actor=req.actor,
            payload={"mode": req.mode.value},
        )
        await _broadcast(app, event)
        return state

    def _require_active_control() -> None:
        # Primer punto donde la autoridad de control (D-07) importa de
        # verdad -- hasta esta sesion nada mas que el propio cambio de modo
        # la consultaba. Los seis endpoints de abajo comandan el HAL de
        # verdad, nunca deben ejecutar en modo passive.
        if app.state.control.state.mode != OperatorMode.ACTIVE:
            raise HTTPException(status_code=403, detail="control en modo passive -- tome control activo antes de comandar")

    CONTROL_JOB_HISTORY_LIMIT = 50  # mismo criterio que MAX_LOG en useGateway.ts -- evita crecimiento sin limite

    def _start_control_job(
        routine: str,
        coro: Coroutine[Any, Any, RoutineResult | ScanCutResult],
        job_id: str | None = None,
    ) -> ControlJobAccepted:
        # D-12: los seis POST /api/control/* dejaron de bloquear hasta que la
        # rutina termina (podia ser hasta `timeout_s`, minutos en
        # antenna-positioning/power-on con caldeo real) -- arrancan la
        # corrutina en un task de fondo y devuelven de inmediato; el llamador
        # sondea GET /api/control/jobs/{job_id}.
        if job_id is None:
            job_id = uuid.uuid4().hex
        app.state.control_jobs[job_id] = ControlJobStatusResponse(
            job_id=job_id, routine=routine, status=ControlJobStatus.RUNNING, result=None, error=None
        )
        if len(app.state.control_jobs) > CONTROL_JOB_HISTORY_LIMIT:
            oldest_job_id = next(iter(app.state.control_jobs))
            del app.state.control_jobs[oldest_job_id]
            app.state.control_job_tasks.pop(oldest_job_id, None)
            app.state.control_job_cancel_requested.discard(oldest_job_id)
            app.state.control_job_inputs.pop(oldest_job_id, None)

        async def _run() -> None:
            try:
                result = await coro
                app.state.control_jobs[job_id] = ControlJobStatusResponse(
                    job_id=job_id, routine=routine, status=ControlJobStatus.DONE, result=result, error=None
                )
            except asyncio.CancelledError:
                # Cancelado desde POST /api/control/jobs/{job_id}/cancel -- la
                # corrutina ya tuvo su chance de detener el eje que estuviera
                # comandando (cada rutina de movimiento/Scan Controller
                # atrapa la cancelacion, detiene y re-lanza; ver sus
                # docstrings) antes de llegar aca. Se absorbe aca en vez de
                # dejarla propagar: el job debe quedar en un estado terminal
                # (`DONE` + `error`) que el poller de la MMI pueda leer, no
                # una Task cancelada que nadie mas espera.
                app.state.control_jobs[job_id] = ControlJobStatusResponse(
                    job_id=job_id, routine=routine, status=ControlJobStatus.DONE, result=None, error="cancelado por el operador"
                )
            except Exception as e:
                # Dos causas posibles aca, indistinguibles por tipo de
                # excepcion: (a) excepcion de infraestructura genuina (ej. el
                # HAL se desconecto a mitad de camino), o (b) esta misma
                # cancelacion, pero pymodbus la convirtio en su propia
                # excepcion en vez de un `CancelledError` limpio si la
                # cancelacion llego mientras un `write_analog`/`read_*`
                # estaba en vuelo (ver docstring de
                # core/control_routines/antenna_movement.py). Se distingue
                # por `control_job_cancel_requested` (lo marca
                # POST /api/control/jobs/{job_id}/cancel antes de llamar
                # `task.cancel()`), no por el mensaje de la excepcion --
                # mas robusto que adivinar el texto exacto de un error de
                # pymodbus.
                error = "cancelado por el operador" if job_id in app.state.control_job_cancel_requested else str(e)
                app.state.control_jobs[job_id] = ControlJobStatusResponse(
                    job_id=job_id, routine=routine, status=ControlJobStatus.DONE, result=None, error=error
                )
            finally:
                app.state.control_job_inputs.pop(job_id, None)

        app.state.control_job_tasks[job_id] = asyncio.create_task(_run())
        return ControlJobAccepted(job_id=job_id, routine=routine, status=ControlJobStatus.RUNNING)

    @app.get("/api/control/jobs/{job_id}", response_model=ControlJobStatusResponse)
    async def get_control_job(job_id: str) -> ControlJobStatusResponse:
        record = app.state.control_jobs.get(job_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"job {job_id} no encontrado")
        return record

    @app.post("/api/control/jobs/{job_id}/step", response_model=ControlJobStatusResponse)
    async def advance_control_job_step(job_id: str, req: WizardStepInputRequest) -> ControlJobStatusResponse:
        record = app.state.control_jobs.get(job_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"job {job_id} no encontrado")
        queue = app.state.control_job_inputs.get(job_id)
        if queue is None or record.status != ControlJobStatus.AWAITING_OPERATOR_INPUT:
            raise HTTPException(status_code=400, detail=f"job {job_id} no está esperando entrada del operador")

        app.state.control_jobs[job_id] = ControlJobStatusResponse(
            job_id=job_id,
            routine=record.routine,
            status=ControlJobStatus.RUNNING,
            current_step=record.current_step,
            total_steps=record.total_steps,
            step_name=record.step_name,
            prompt=record.prompt,
            result=record.result,
            error=None,
        )
        await queue.put(req.data)
        return app.state.control_jobs[job_id]

    @app.post("/api/control/jobs/{job_id}/cancel", response_model=ControlJobStatusResponse)
    async def cancel_control_job(job_id: str) -> ControlJobStatusResponse:
        record = app.state.control_jobs.get(job_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"job {job_id} no encontrado")
        task = app.state.control_job_tasks.get(job_id)
        if record.status == ControlJobStatus.DONE or task is None or task.done():
            # Idempotente a proposito: si ya termino (por si solo o por una
            # cancelacion anterior), no hay nada que cancelar -- devolver el
            # estado actual en vez de 409/404, mismo criterio de "informar,
            # no fallar" que el resto de este endpoint.
            return record
        app.state.control_job_cancel_requested.add(job_id)
        task.cancel()
        await task  # espera a que la rutina detenga el eje antes de responder
        return app.state.control_jobs[job_id]

    @app.post("/api/control/general-power-on", response_model=ControlJobAccepted, status_code=202)
    async def general_power_on() -> ControlJobAccepted:
        _require_active_control()
        return _start_control_job("general_power_on", run_general_power_on(hal))

    @app.post("/api/control/transmitter-power-on", response_model=ControlJobAccepted, status_code=202)
    async def transmitter_power_on(req: TransmitterPowerOnRequest) -> ControlJobAccepted:
        _require_active_control()
        return _start_control_job("transmitter_power_on", run_transmitter_power_on(hal, warmup_timeout_s=req.warmup_timeout_s))

    @app.post("/api/control/receiver-power-on", response_model=ControlJobAccepted, status_code=202)
    async def receiver_power_on(req: ReceiverPowerOnRequest) -> ControlJobAccepted:
        _require_active_control()
        return _start_control_job("receiver_power_on", run_receiver_power_on(hal, confirm_timeout_s=req.confirm_timeout_s))

    @app.post("/api/control/antenna-unit-power-on", response_model=ControlJobAccepted, status_code=202)
    async def antenna_unit_power_on(req: AntennaUnitPowerOnRequest) -> ControlJobAccepted:
        _require_active_control()
        return _start_control_job(
            "antenna_unit_power_on", run_antenna_unit_power_on(hal, confirm_timeout_s=req.confirm_timeout_s)
        )

    @app.post("/api/control/antenna-movement", response_model=ControlJobAccepted, status_code=202)
    async def antenna_movement(req: AntennaMovementRequest) -> ControlJobAccepted:
        _require_active_control()
        return _start_control_job("antenna_movement", run_antenna_movement(hal, req.axis, req.voltage_reference))

    @app.post("/api/control/antenna-positioning", response_model=ControlJobAccepted, status_code=202)
    async def antenna_positioning(req: AntennaPositioningRequest) -> ControlJobAccepted:
        _require_active_control()
        return _start_control_job(
            "antenna_positioning",
            run_antenna_positioning(
                hal,
                req.axis,
                req.target_deg,
                gain_v_per_deg=req.gain_v_per_deg,
                max_voltage=req.max_voltage,
                tolerance_deg=req.tolerance_deg,
                timeout_s=req.timeout_s,
            ),
        )

    async def _execute_zero_check() -> RoutineResult:
        res = await run_zero_check(
            hal,
            record_log_func=lambda entry: _record_calibration_log(app, entry),
            actor=app.state.control.state.actor,
        )
        now = datetime.now(timezone.utc)
        app.state.zero_check_last_result = res
        if res.outcome == RoutineOutcome.SUCCESS:
            app.state.zero_check_last_run_at_wall = now
            app.state.zero_check_next_run_at_wall = now + timedelta(seconds=app.state.zero_check_interval_s)
            for step in res.steps:
                if "Noise High Channel:" in step.detail:
                    try:
                        val_str = step.detail.split(":")[1].replace("dBm", "").strip()
                        app.state.zero_check_noise_high_dbm = float(val_str)
                    except ValueError:
                        pass
                elif "Noise Low Channel:" in step.detail:
                    try:
                        val_str = step.detail.split(":")[1].replace("dBm", "").strip()
                        app.state.zero_check_noise_low_dbm = float(val_str)
                    except ValueError:
                        pass
        return res

    @app.get("/api/zero-check", response_model=ZeroCheckSnapshot)
    async def get_zero_check() -> ZeroCheckSnapshot:
        return ZeroCheckSnapshot(
            last_run_at_wall=app.state.zero_check_last_run_at_wall,
            next_run_at_wall=app.state.zero_check_next_run_at_wall,
            interval_s=app.state.zero_check_interval_s,
            enabled=True,
            noise_high_dbm=app.state.zero_check_noise_high_dbm,
            noise_low_dbm=app.state.zero_check_noise_low_dbm,
            last_result=app.state.zero_check_last_result,
        )

    @app.get("/api/calibration-log", response_model=list[CalibrationLogEntry])
    async def get_calibration_log() -> list[CalibrationLogEntry]:
        return app.state.calibration_log

    @app.post("/api/control/zero-check", response_model=ControlJobAccepted, status_code=202)
    async def zero_check() -> ControlJobAccepted:
        _require_active_control()
        return _start_control_job("zero_check", _execute_zero_check())

    @app.post("/api/control/tx-power-calibration", response_model=ControlJobAccepted, status_code=202)
    async def tx_power_calibration() -> ControlJobAccepted:
        _require_active_control()
        if _effective_maintenance().level != AccessLevel.MANT:
            raise HTTPException(
                status_code=403,
                detail="se requiere nivel de mantenimiento MANT para la calibración de potencia TX",
            )

        # warmup_duration_s se calcula server-side a partir de radiating_since_wall
        # (actualizado en cada lectura de tx.radiating_status via _read_radiating) --
        # nunca se confia en un valor provisto por el llamador para esta precondicion.
        radiating_now = await _read_radiating()
        warmup_duration_s = (
            (datetime.now(timezone.utc) - app.state.radiating_since_wall).total_seconds()
            if radiating_now and app.state.radiating_since_wall is not None
            else 0.0
        )

        job_id = uuid.uuid4().hex
        input_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

        async def _get_input() -> dict[str, Any]:
            return await input_queue.get()

        def _on_step_change(current_step: int, total_steps: int, step_name: str, prompt: str) -> None:
            rec = app.state.control_jobs.get(job_id)
            if rec:
                app.state.control_jobs[job_id] = ControlJobStatusResponse(
                    job_id=job_id,
                    routine="tx_power_calibration",
                    status=ControlJobStatus.AWAITING_OPERATOR_INPUT,
                    current_step=current_step,
                    total_steps=total_steps,
                    step_name=step_name,
                    prompt=prompt,
                    result=rec.result,
                    error=None,
                )

        coro = run_tx_power_calibration(
            hal,
            actor=app.state.control.state.actor,
            step_input_func=_get_input,
            on_step_change_func=_on_step_change,
            record_log_func=lambda entry: _record_calibration_log(app, entry),
            warmup_duration_s=warmup_duration_s,
            required_warmup_s=1200.0,
        )

        app.state.control_job_inputs[job_id] = input_queue
        accepted = _start_control_job("tx_power_calibration", coro, job_id=job_id)
        return accepted

    @app.post("/api/control/single-point-calibration", response_model=ControlJobAccepted, status_code=202)
    async def single_point_calibration(req: SinglePointCalibrationRequest) -> ControlJobAccepted:
        _require_active_control()
        if _effective_maintenance().level != AccessLevel.MANT:
            raise HTTPException(
                status_code=403,
                detail="se requiere nivel de mantenimiento MANT para la calibración de punto único",
            )

        job_id = uuid.uuid4().hex
        input_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

        async def _get_input() -> dict[str, Any]:
            return await input_queue.get()

        def _on_step_change(current_step: int, total_steps: int, step_name: str, prompt: str) -> None:
            rec = app.state.control_jobs.get(job_id)
            if rec:
                app.state.control_jobs[job_id] = ControlJobStatusResponse(
                    job_id=job_id,
                    routine="single_point_calibration",
                    status=ControlJobStatus.AWAITING_OPERATOR_INPUT,
                    current_step=current_step,
                    total_steps=total_steps,
                    step_name=step_name,
                    prompt=prompt,
                    result=rec.result,
                    error=None,
                )

        coro = run_single_point_calibration(
            hal,
            mode=req.mode,
            actor=app.state.control.state.actor,
            step_input_func=_get_input,
            on_step_change_func=_on_step_change,
            record_log_func=lambda entry: _record_calibration_log(app, entry),
        )

        app.state.control_job_inputs[job_id] = input_queue
        accepted = _start_control_job("single_point_calibration", coro, job_id=job_id)
        return accepted

    _SINGLE_POINT_RESULT_SIGNAL_IDS = {
        "rx.single_point_radar_constant_db": "auto",
        "rx.single_point_radar_constant": "external",
    }

    @app.post(
        "/api/control/single-point-calibration/{job_id}/save-result",
        response_model=MeasuredRadarConstant,
    )
    async def save_single_point_calibration_result(job_id: str) -> MeasuredRadarConstant:
        # PEND-RCP-18 (docs/alcance/pendientes.md): persiste el valor medido por G4
        # aparte de `RadarConstantParameters`/G7 -- no hay todavia decision de si
        # este numero debe alimentar el calculo operacional que llega al DSP/DRX.
        if _effective_maintenance().level != AccessLevel.MANT:
            raise HTTPException(
                status_code=403,
                detail="se requiere nivel de mantenimiento MANT para guardar la calibración de punto único",
            )

        job = app.state.control_jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job no encontrado")
        if (
            job.routine != "single_point_calibration"
            or job.status != ControlJobStatus.DONE
            or job.result is None
            or job.result.outcome != RoutineOutcome.SUCCESS
        ):
            raise HTTPException(
                status_code=409,
                detail="el job no tiene un resultado exitoso de calibración de punto único para guardar",
            )

        radar_constant_db: float | None = None
        mode = "auto"
        for step in job.result.steps:
            scenario = _SINGLE_POINT_RESULT_SIGNAL_IDS.get(step.signal_id)
            if scenario is None:
                continue
            match = re.search(r"(-?\d+(?:\.\d+)?)\s*dB\s*$", step.detail)
            if match:
                mode = scenario
                radar_constant_db = float(match.group(1))
        if radar_constant_db is None:
            raise HTTPException(
                status_code=422,
                detail="no se pudo extraer la constante de radar medida del resultado del job",
            )

        measured = MeasuredRadarConstant(
            radar_constant_db=radar_constant_db,
            mode=mode,
            measured_at=datetime.now(timezone.utc),
        )
        app.state.measured_radar_constant = measured
        app.state.measured_radar_constant_path.parent.mkdir(parents=True, exist_ok=True)
        app.state.measured_radar_constant_path.write_text(measured.model_dump_json())
        return measured

    @app.get("/api/antenna/step-config", response_model=AntennaStepConfig)
    async def get_antenna_step_config() -> AntennaStepConfig:
        return app.state.antenna_step_config

    @app.post("/api/antenna/step-config", response_model=AntennaStepConfig)
    async def set_antenna_step_config(config: AntennaStepConfig) -> AntennaStepConfig:
        app.state.antenna_step_config = config
        return app.state.antenna_step_config

    @app.get("/api/process-monitor", response_model=ProcessMonitorSnapshot)
    async def get_process_monitor() -> ProcessMonitorSnapshot:
        proc = psutil.Process(os.getpid())
        try:
            priority = proc.nice()
        except Exception:
            priority = 0

        proc_info = ProcessInfo(
            pid=proc.pid,
            name=proc.name(),
            priority=priority,
            status=proc.status(),
            cpu_percent=proc.cpu_percent(interval=0.1),
            memory_mb=round(proc.memory_info().rss / 1e6, 2),
        )

        tasks = []
        for task in asyncio.all_tasks():
            state = "done" if task.done() else ("cancelled" if task.cancelled() else "pending")
            tasks.append(RcpTaskInfo(name=task.get_name(), state=state))

        return ProcessMonitorSnapshot(process=proc_info, tasks=tasks)

    @app.get("/api/trend/channels", response_model=list[str])
    async def get_trend_channels() -> list[str]:
        return [s.id for s in CATALOG.values() if s.kind == "AI"]

    @app.get("/api/trend/status", response_model=TrendStatus)
    async def get_trend_status() -> TrendStatus:
        return TrendStatus(
            running=app.state.trend_running,
            started_at_wall=app.state.trend_started_at,
            signal_ids=app.state.trend_channels,
        )

    @app.post("/api/trend/start", response_model=TrendStatus)
    async def start_trend(req: TrendStartRequest) -> TrendStatus:
        if app.state.trend_running:
            raise HTTPException(status_code=409, detail="muestreo de tendencias ya está en ejecución; detenga antes de iniciar")
        now = datetime.now(timezone.utc)
        app.state.trend_channels = req.signal_ids
        app.state.trend_buffers = {sig: deque(maxlen=28800) for sig in req.signal_ids}
        app.state.trend_started_at = now
        app.state.trend_running = True
        return TrendStatus(
            running=app.state.trend_running,
            started_at_wall=app.state.trend_started_at,
            signal_ids=app.state.trend_channels,
        )

    @app.post("/api/trend/stop", response_model=TrendStatus)
    async def stop_trend() -> TrendStatus:
        app.state.trend_running = False
        return TrendStatus(
            running=app.state.trend_running,
            started_at_wall=app.state.trend_started_at,
            signal_ids=app.state.trend_channels,
        )

    @app.post("/api/trend/continue", response_model=TrendStatus)
    async def continue_trend() -> TrendStatus:
        app.state.trend_running = True
        return TrendStatus(
            running=app.state.trend_running,
            started_at_wall=app.state.trend_started_at,
            signal_ids=app.state.trend_channels,
        )

    @app.post("/api/trend/clear", response_model=TrendStatus)
    async def clear_trend() -> TrendStatus:
        app.state.trend_running = False
        app.state.trend_buffers.clear()
        app.state.trend_channels = []
        app.state.trend_started_at = None
        return TrendStatus(
            running=app.state.trend_running,
            started_at_wall=app.state.trend_started_at,
            signal_ids=app.state.trend_channels,
        )

    @app.get("/api/trend/data", response_model=list[TrendSeries])
    async def get_trend_data() -> list[TrendSeries]:
        return [
            TrendSeries(signal_id=sig, samples=list(buf))
            for sig, buf in app.state.trend_buffers.items()
        ]

    async def _read_radiating() -> bool:
        try:
            value = (await hal.read_digital("tx.radiating_status")).value
        except Exception:
            value = False
        if value:
            if app.state.radiating_since_wall is None:
                app.state.radiating_since_wall = datetime.now(timezone.utc)
        else:
            app.state.radiating_since_wall = None
        return value

    @app.get("/api/radar-constant", response_model=RadarConstantSnapshot)
    async def get_radar_constant() -> RadarConstantSnapshot:
        params = app.state.radar_constant_params
        return RadarConstantSnapshot(
            params=params,
            radar_constant_db=compute_radar_constant_db(params),
        )

    @app.post("/api/radar-constant", response_model=RadarConstantSnapshot)
    async def set_radar_constant(params: RadarConstantParameters) -> RadarConstantSnapshot:
        app.state.radar_constant_params = params
        return RadarConstantSnapshot(
            params=params,
            radar_constant_db=compute_radar_constant_db(params),
        )

    @app.post("/api/radar-constant/save", response_model=RadarConstantSnapshot)
    async def save_radar_constant() -> RadarConstantSnapshot:
        app.state.radar_constant_path.parent.mkdir(parents=True, exist_ok=True)
        app.state.radar_constant_path.write_text(
            app.state.radar_constant_params.model_dump_json()
        )
        _record_calibration_log(
            app,
            CalibrationLogEntry(
                at_wall=datetime.now(timezone.utc),
                severity="info",
                procedure="Radar Constant Parameters",
                actor=app.state.control.state.actor,
                message="Parámetros de constante de radar guardados.",
            ),
        )
        return RadarConstantSnapshot(
            params=app.state.radar_constant_params,
            radar_constant_db=compute_radar_constant_db(app.state.radar_constant_params),
        )

    @app.get("/api/power-monitor", response_model=PowerMonitorSnapshot)
    async def get_power_monitor() -> PowerMonitorSnapshot:
        async def _read_power(sig: str) -> float | None:
            try:
                reading = await hal.read_analog(sig)
            except Exception:
                return None
            return reading.value if reading.quality == SignalQuality.OK else None

        forward = await _read_power("tx.tx_peak_power_sample")
        reverse = await _read_power("tx.tx_reflected_power_sample")
        vswr = None
        if forward is not None and reverse is not None and forward > 0 and reverse < forward:
            ratio = (reverse / forward) ** 0.5
            vswr = round((1 + ratio) / (1 - ratio), 3)

        return PowerMonitorSnapshot(
            forward_power_kw=forward,
            reverse_power_kw=reverse,
            vswr=vswr,
            bus_ok=hal.is_connected(),
            radiating=await _read_radiating(),
            limits=app.state.power_limits,
        )

    @app.post("/api/power-monitor/limits", response_model=PowerMeasurementLimits)
    async def set_power_limits(limits: PowerMeasurementLimits) -> PowerMeasurementLimits:
        app.state.power_limits = limits
        return app.state.power_limits

    @app.post("/api/power-monitor/limits/save", response_model=PowerMeasurementLimits)
    async def save_power_limits() -> PowerMeasurementLimits:
        if app.state.power_limits is None:
            raise HTTPException(status_code=409, detail="no hay limites para guardar -- use Set primero")
        if await _read_radiating():
            raise HTTPException(
                status_code=409,
                detail="no se puede guardar mientras el radar esta radiando -- apague radiacion primero",
            )
        app.state.power_limits_path.parent.mkdir(parents=True, exist_ok=True)
        app.state.power_limits_path.write_text(app.state.power_limits.model_dump_json())
        return app.state.power_limits

    @app.get("/api/tx-sampling-adjust", response_model=TxSamplingAdjustSnapshot)
    async def get_tx_sampling_adjust() -> TxSamplingAdjustSnapshot:
        async def _read_analog_safe(sig: str) -> float | None:
            try:
                reading = await hal.read_analog(sig)
            except Exception:
                return None
            return reading.value if reading.quality == SignalQuality.OK else None

        tx_sample = await _read_analog_safe("tx.tx_sample")
        tx_freq = await _read_analog_safe("tx.tx_frequency")
        commanded_lo = await _read_analog_safe("tx.commanded_lo_freq")
        tx_start = await _read_analog_safe("tx.tx_start_sample")
        tx_stop = await _read_analog_safe("tx.tx_stop_sample")

        return TxSamplingAdjustSnapshot(
            tx_sample_readout=tx_sample,
            tx_frequency_readout_mhz=tx_freq,
            commanded_lo_freq_readout_mhz=commanded_lo,
            tx_start_sample_readout=tx_start,
            tx_stop_sample_readout=tx_stop,
            bus_ok=hal.is_connected(),
            radiating=await _read_radiating(),
            params=app.state.tx_sampling_adjust_params,
        )

    @app.post("/api/tx-sampling-adjust", response_model=TxSamplingAdjustParams)
    async def set_tx_sampling_adjust(params: TxSamplingAdjustParams) -> TxSamplingAdjustParams:
        app.state.tx_sampling_adjust_params = params
        return app.state.tx_sampling_adjust_params

    @app.post("/api/tx-sampling-adjust/save", response_model=TxSamplingAdjustParams)
    async def save_tx_sampling_adjust() -> TxSamplingAdjustParams:
        if app.state.tx_sampling_adjust_params is None:
            raise HTTPException(status_code=409, detail="no hay parametros de muestreo TX para guardar -- use Set primero")
        if await _read_radiating():
            raise HTTPException(
                status_code=409,
                detail="no se puede guardar mientras el radar esta radiando -- apague radiacion primero",
            )
        app.state.tx_sampling_adjust_path.parent.mkdir(parents=True, exist_ok=True)
        app.state.tx_sampling_adjust_path.write_text(app.state.tx_sampling_adjust_params.model_dump_json())
        _record_calibration_log(
            app,
            CalibrationLogEntry(
                at_wall=datetime.now(timezone.utc),
                severity="info",
                procedure="TX Sampling Adjust",
                actor=app.state.control.state.actor,
                message="Parámetros de ajuste de muestreo TX guardados.",
            ),
        )
        return app.state.tx_sampling_adjust_params

    @app.get("/api/sector-blanking", response_model=SectorBlankingProfile)
    async def get_sector_blanking() -> SectorBlankingProfile:
        return app.state.sector_blanking

    @app.post("/api/sector-blanking/set", response_model=SectorBlankingProfile)
    async def set_sector_blanking(profile: SectorBlankingProfile) -> SectorBlankingProfile:
        app.state.sector_blanking = profile
        return app.state.sector_blanking

    @app.post("/api/sector-blanking/save", response_model=SectorBlankingProfile)
    async def save_sector_blanking() -> SectorBlankingProfile:
        app.state.sector_blanking_path.parent.mkdir(parents=True, exist_ok=True)
        app.state.sector_blanking_path.write_text(app.state.sector_blanking.model_dump_json())
        return app.state.sector_blanking

    @app.get("/api/config/profile/current", response_model=RcpConfigProfile)
    async def get_config_profile_current() -> RcpConfigProfile:
        return _get_current_profile()

    @app.get("/api/config/profile/saved", response_model=RcpConfigProfile)
    async def get_config_profile_saved() -> RcpConfigProfile:
        return app.state.saved_profile

    @app.post("/api/config/profile/set", response_model=RcpConfigProfile)
    async def set_config_profile(profile: RcpConfigProfile) -> RcpConfigProfile:
        _apply_profile(profile)
        return _get_current_profile()

    @app.post("/api/config/profile/save", response_model=RcpConfigProfile)
    async def save_config_profile() -> RcpConfigProfile:
        if await _read_radiating():
            raise HTTPException(
                status_code=409,
                detail="no se puede guardar el perfil mientras el radar esta radiando -- apague radiacion primero",
            )
        current = _get_current_profile()
        app.state.saved_profile = current
        app.state.config_profile_path.parent.mkdir(parents=True, exist_ok=True)
        app.state.config_profile_path.write_text(current.model_dump_json())
        return current

    @app.post("/api/config/profile/restore", response_model=RcpConfigProfile)
    async def restore_config_profile() -> RcpConfigProfile:
        _apply_profile(app.state.saved_profile)
        return _get_current_profile()

    @app.post("/api/config/profile/factory", response_model=RcpConfigProfile)
    async def factory_config_profile() -> RcpConfigProfile:
        factory_profile = RcpConfigProfile()
        _apply_profile(factory_profile)
        return _get_current_profile()

    def _save_scan_worksheet() -> None:
        app.state.scan_worksheet_path.parent.mkdir(parents=True, exist_ok=True)
        app.state.scan_worksheet_path.write_text(
            SCAN_WORKSHEET_LIST_ADAPTER.dump_json(app.state.scan_worksheet).decode()
        )

    @app.get("/api/scan/worksheet", response_model=list[ScanCut])
    async def get_scan_worksheet() -> list[ScanCut]:
        return app.state.scan_worksheet

    @app.post("/api/scan/worksheet", response_model=list[ScanCut])
    async def add_scan_cut(cut: ScanCut) -> list[ScanCut]:
        app.state.scan_worksheet.append(cut)
        _save_scan_worksheet()
        return app.state.scan_worksheet

    @app.delete("/api/scan/worksheet/{index}", response_model=list[ScanCut])
    async def delete_scan_cut(index: int) -> list[ScanCut]:
        if index < 0 or index >= len(app.state.scan_worksheet):
            raise HTTPException(status_code=404, detail=f"indice {index} fuera de rango (worksheet tiene {len(app.state.scan_worksheet)} cortes)")
        del app.state.scan_worksheet[index]
        _save_scan_worksheet()
        return app.state.scan_worksheet

    @app.post("/api/scan/worksheet/{index}/execute", response_model=ControlJobAccepted, status_code=202)
    async def execute_scan_cut(index: int, req: ScanCutExecutionRequest) -> ControlJobAccepted:
        # Mismo gating que las seis rutinas -- el Scan Controller comanda el
        # HAL de verdad (Rutinas 5/6), nunca en modo passive.
        _require_active_control()
        if index < 0 or index >= len(app.state.scan_worksheet):
            raise HTTPException(status_code=404, detail=f"indice {index} fuera de rango (worksheet tiene {len(app.state.scan_worksheet)} cortes)")
        cut = app.state.scan_worksheet[index]
        return _start_control_job(
            "scan_cut",
            run_scan_cut(
                hal,
                cut,
                azimuth_positioning=req.azimuth_positioning,
                elevation_positioning=req.elevation_positioning,
                sweep_voltage_magnitude=req.sweep_voltage_magnitude,
                sweep_tolerance_deg=req.sweep_tolerance_deg,
                sweep_timeout_s=req.sweep_timeout_s,
            ),
        )

    @app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket) -> None:
        await websocket.accept()
        app.state.websockets.add(websocket)
        try:
            await websocket.send_text(
                SessionMessage(
                    rcp_version=RCP_VERSION,
                    started_at_wall=app.state.started_at,
                    control=app.state.control.state,
                ).model_dump_json()
            )
            loop = asyncio.get_running_loop()
            last_heartbeat = loop.time()
            last_status = loop.time()
            while True:
                try:
                    position = await hal.read_antenna_position()
                    await websocket.send_text(AntennaMessage(position=position).model_dump_json())
                except RuntimeError:
                    pass  # sin paquete de encoder todavia / stream perdido -- no cerrar la conexion por esto

                now = loop.time()
                if now - last_heartbeat >= WS_HEARTBEAT_PERIOD_S:
                    await websocket.send_text(
                        HeartbeatMessage(at_wall=datetime.now(timezone.utc)).model_dump_json()
                    )
                    last_heartbeat = now
                if now - last_status >= WS_STATUS_PERIOD_S:
                    await websocket.send_text(
                        StatusMessage(
                            at_wall=datetime.now(timezone.utc),
                            hal_connected=hal.is_connected(),
                            dsp=_dsp_status(),
                        ).model_dump_json()
                    )
                    last_status = now

                await asyncio.sleep(WS_ANTENNA_PERIOD_S)
        except WebSocketDisconnect:
            pass
        finally:
            app.state.websockets.discard(websocket)

    return app


async def _broadcast(app: FastAPI, message: WsMessage) -> None:
    dead = []
    for ws in app.state.websockets:
        try:
            await ws.send_text(message.model_dump_json())
        except Exception:
            dead.append(ws)  # socket ya caido del lado del cliente -- se poda, no rompe el broadcast
    for ws in dead:
        app.state.websockets.discard(ws)
