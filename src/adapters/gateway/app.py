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
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from adapters.dsp import MomentStreamReceiver
from adapters.hal_sim import SimulatedHAL
from core.bite import BiteManager
from core.contracts.bite import BiteTransition
from core.contracts.mmi import (
    AntennaMessage,
    BiteEventMessage,
    BiteFaultSummary,
    ControlAuthorityState,
    DspStreamStatus,
    HeartbeatMessage,
    OperatorEventMessage,
    SessionMessage,
    SetControlModeRequest,
    SystemStatusSnapshot,
    WsMessage,
)
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


def create_app(hal: SimulatedHAL, dsp: MomentStreamReceiver, dsp_bind_host: str, dsp_port: int) -> FastAPI:
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
