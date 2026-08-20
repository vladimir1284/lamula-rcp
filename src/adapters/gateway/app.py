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
import uuid
from collections.abc import Coroutine
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import TypeAdapter

from adapters.dsp import MomentStreamReceiver
from adapters.hal_sim import SimulatedHAL
from core.bite import BiteManager
from core.contracts.bite import BiteTransition
from core.contracts.control import RoutineResult
from core.contracts.mmi import (
    AntennaMessage,
    AntennaMovementRequest,
    AntennaPositioningRequest,
    AntennaUnitPowerOnRequest,
    BiteEventMessage,
    BiteFaultSummary,
    ControlAuthorityState,
    ControlJobAccepted,
    ControlJobStatus,
    ControlJobStatusResponse,
    DspStreamStatus,
    HeartbeatMessage,
    OperatorEventMessage,
    OperatorMode,
    ReceiverPowerOnRequest,
    ScanCutExecutionRequest,
    SessionMessage,
    SetControlModeRequest,
    SystemStatusSnapshot,
    TransmitterPowerOnRequest,
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

# Throttle deliberado: el encoder UDP emite a 100 Hz (nominal), la MMI no
# necesita esa cadencia para el PPI. Ver radar_emulator/docs/interfaces/udp-encoder.md.
WS_ANTENNA_PERIOD_S = 0.1
WS_HEARTBEAT_PERIOD_S = 1.0
# core/bite/manager.py hace hasta 20 lecturas Modbus por poll (una por señal
# monitoreada) -- no son condiciones de tiempo duro, 2 Hz alcanza sin competir
# con el resto del trafico Modbus (posicionamiento de antena, etc.).
BITE_POLL_PERIOD_S = 0.5


SCAN_WORKSHEET_LIST_ADAPTER = TypeAdapter(list[ScanCut])


def create_app(
    hal: SimulatedHAL,
    dsp: MomentStreamReceiver,
    dsp_bind_host: str,
    dsp_port: int,
    scan_worksheet_path: Path = Path("data/scan_worksheet.json"),
) -> FastAPI:
    async def _bite_poll_loop(app: FastAPI) -> None:
        while True:
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
            await asyncio.sleep(BITE_POLL_PERIOD_S)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if not hal.is_connected():
            await hal.connect()
        await dsp.start(dsp_bind_host, dsp_port)
        bite_task = asyncio.create_task(_bite_poll_loop(app))
        try:
            yield
        finally:
            bite_task.cancel()
            try:
                await bite_task
            except asyncio.CancelledError:
                pass
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
    # Jobs asincronos de los seis POST /api/control/* (ver _start_control_job mas
    # abajo) -- dict ordinario, el orden de inserccion de Python 3.7+ es lo que
    # usa el tope de historial para descartar el mas viejo. En memoria, se pierde
    # al reiniciar el gateway, mismo nivel de esqueleto que el resto del estado.
    app.state.control_jobs: dict[str, ControlJobStatusResponse] = {}

    def _dsp_status() -> DspStreamStatus:
        latest = dsp.latest
        return DspStreamStatus(
            connected=dsp.connected,
            radials_received=dsp.radials_received,
            last_volume_number=latest.volume_number if latest else None,
            last_elevation_number=latest.elevation_number if latest else None,
            last_radial_status=latest.radial_status if latest else None,
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

    @app.get("/api/status", response_model=SystemStatusSnapshot)
    async def get_status() -> SystemStatusSnapshot:
        antenna = None
        try:
            antenna = await hal.read_antenna_position()
        except RuntimeError:
            antenna = None  # sin paquete de encoder todavia, o stream perdido
        return SystemStatusSnapshot(
            control=app.state.control.state,
            hal_connected=hal.is_connected(),
            antenna=antenna,
            dsp=_dsp_status(),
            active_bite_faults=_active_bite_faults(),
        )

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
            del app.state.control_jobs[next(iter(app.state.control_jobs))]

        async def _run() -> None:
            try:
                result = await coro
                app.state.control_jobs[job_id] = ControlJobStatusResponse(
                    job_id=job_id, routine=routine, status=ControlJobStatus.DONE, result=result, error=None
                )
            except Exception as e:
                # Excepcion de infraestructura (ej. el HAL se desconecto a
                # mitad de camino) -- distinto de un RoutineResult con
                # outcome failed/interrupted, que es un resultado legitimo de
                # la rutina, no un error.
                app.state.control_jobs[job_id] = ControlJobStatusResponse(
                    job_id=job_id, routine=routine, status=ControlJobStatus.DONE, result=None, error=str(e)
                )

        asyncio.create_task(_run())
        return ControlJobAccepted(job_id=job_id, routine=routine, status=ControlJobStatus.RUNNING)

    @app.get("/api/control/jobs/{job_id}", response_model=ControlJobStatusResponse)
    async def get_control_job(job_id: str) -> ControlJobStatusResponse:
        record = app.state.control_jobs.get(job_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"job {job_id} no encontrado")
        return record

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
