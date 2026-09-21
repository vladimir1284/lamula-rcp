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
from core.contracts.control import RoutineResult
from core.contracts.mmi import (
    AccessLevel,
    AntennaMessage,
    AntennaMovementRequest,
    AntennaPositioningRequest,
    AntennaStepConfig,
    AntennaUnitPowerOnRequest,
    BiteEventMessage,
    BiteFaultSummary,
    ControlAuthorityState,
    ControlJobAccepted,
    ControlJobStatus,
    ControlJobStatusResponse,
    DspStreamStatus,
    HeartbeatMessage,
    MaintenanceState,
    OperatorEventMessage,
    OperatorMode,
    PowerMeasurementLimits,
    PowerMonitorSnapshot,
    RadarConstantParameters,
    RadarConstantSnapshot,
    ProcessInfo,
    ProcessMonitorSnapshot,
    RcpTaskInfo,
    ReceiverPowerOnRequest,
    ScanCutExecutionRequest,
    SessionMessage,
    SetControlModeRequest,
    StatusMessage,
    SystemInfo,
    SystemStatusSnapshot,
    TransmitterPowerOnRequest,
    TrendChannelSample,
    TrendSeries,
    TrendStartRequest,
    TrendStatus,
    UnlockMaintenanceRequest,
    WsMessage,
)
from core.contracts.scan import ScanCut, ScanCutResult
from core.control_routines import (
    run_antenna_movement,
    run_antenna_positioning,
    run_antenna_unit_power_on,
    run_general_power_on,
    run_receiver_power_on,
    run_transmitter_power_on,
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


def create_app(
    hal: SimulatedHAL,
    dsp: MomentStreamReceiver,
    dsp_bind_host: str,
    dsp_port: int,
    scan_worksheet_path: Path = Path("data/scan_worksheet.json"),
    power_limits_path: Path = Path("data/power_limits.json"),
    radar_constant_path: Path = Path("data/radar_constant.json"),
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

    app.state.radar_constant_path = radar_constant_path
    try:
        app.state.radar_constant_params = RadarConstantParameters.model_validate_json(
            radar_constant_path.read_text()
        )
    except (FileNotFoundError, ValueError):
        app.state.radar_constant_params = DEFAULT_RADAR_CONSTANT_PARAMS
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

    def _start_control_job(routine: str, coro: Coroutine[Any, Any, RoutineResult | ScanCutResult]) -> ControlJobAccepted:
        # D-12: los seis POST /api/control/* dejaron de bloquear hasta que la
        # rutina termina (podia ser hasta `timeout_s`, minutos en
        # antenna-positioning/power-on con caldeo real) -- arrancan la
        # corrutina en un task de fondo y devuelven de inmediato; el llamador
        # sondea GET /api/control/jobs/{job_id}.
        job_id = uuid.uuid4().hex
        app.state.control_jobs[job_id] = ControlJobStatusResponse(
            job_id=job_id, routine=routine, status=ControlJobStatus.RUNNING, result=None, error=None
        )
        if len(app.state.control_jobs) > CONTROL_JOB_HISTORY_LIMIT:
            oldest_job_id = next(iter(app.state.control_jobs))
            del app.state.control_jobs[oldest_job_id]
            app.state.control_job_tasks.pop(oldest_job_id, None)
            app.state.control_job_cancel_requested.discard(oldest_job_id)

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

        app.state.control_job_tasks[job_id] = asyncio.create_task(_run())
        return ControlJobAccepted(job_id=job_id, routine=routine, status=ControlJobStatus.RUNNING)

    @app.get("/api/control/jobs/{job_id}", response_model=ControlJobStatusResponse)
    async def get_control_job(job_id: str) -> ControlJobStatusResponse:
        record = app.state.control_jobs.get(job_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"job {job_id} no encontrado")
        return record

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
            return (await hal.read_digital("tx.radiating_status")).value
        except Exception:
            return False

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
