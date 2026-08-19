"""Spike Fase 2 -- guarda de seguridad de parametros, parte de limites de
antena: dispara los booleanos reales de `radar_emulator` (fin de carrera de
elevacion, proteccion termica de azimut) via su canal de control WS --
mismo mecanismo que spike-fase1/fault_injection_spike.py -- y verifica que
`core.safety_guard.check_antenna_movement` rechace/permita el movimiento
propuesto en consecuencia.

No ejercita la parte de PRF x pulse-width de la guarda (plan §4.3): no
existe todavia ninguna senal ni contrato que consultar para eso, ver
PEND-RCP-08 en docs/alcance/pendientes.md.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

import websockets

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from adapters.hal_sim import SimulatedHAL
from core.contracts.safety import AntennaAxis, AntennaMoveDirection
from core.safety_guard import check_antenna_movement

FAILURES = []


def check(condition, msg):
    print(f"[{'OK   ' if condition else 'FALLA'}] {msg}")
    if not condition:
        FAILURES.append(msg)
    return condition


async def force(ws, signal, value):
    await ws.send(json.dumps({"type": "force", "actor": "spike-fase2-parameter-guard", "signal": signal, "value": value}))


async def release(ws, signal):
    await ws.send(json.dumps({"type": "release", "actor": "spike-fase2-parameter-guard", "signal": signal}))


async def run(ws_url, modbus_port, udp_port):
    hal = SimulatedHAL(modbus_host="127.0.0.1", modbus_port=modbus_port, udp_bind_host="0.0.0.0", udp_port=udp_port)
    await hal.connect()

    async with websockets.connect(ws_url) as ws:
        await asyncio.wait_for(ws.recv(), timeout=2)  # "session" inicial

        # --- baseline: sin ningun limite/traba forzado (valor calculado real) ---
        await release(ws, "ant.el_upper_limit_status")
        await release(ws, "ant.el_lower_limit_status")
        await release(ws, "ant.i2t_drive_az_status")
        await asyncio.sleep(0.2)

        r = await check_antenna_movement(hal, AntennaAxis.ELEVATION, AntennaMoveDirection.UP)
        check(r.allowed, f"elevacion/up sin fin de carrera: allowed={r.allowed} ({r.reason})")
        r = await check_antenna_movement(hal, AntennaAxis.ELEVATION, AntennaMoveDirection.DOWN)
        check(r.allowed, f"elevacion/down sin fin de carrera: allowed={r.allowed} ({r.reason})")
        r = await check_antenna_movement(hal, AntennaAxis.AZIMUTH, AntennaMoveDirection.UP)
        check(r.allowed, f"azimut sin traba termica: allowed={r.allowed} ({r.reason})")

        # --- fin de carrera superior de elevacion ------------------------------
        await force(ws, "ant.el_upper_limit_status", True)
        await asyncio.sleep(0.2)
        r = await check_antenna_movement(hal, AntennaAxis.ELEVATION, AntennaMoveDirection.UP)
        check(not r.allowed, f"elevacion/up con el_upper_limit_status forzado: allowed={r.allowed} ({r.reason})")
        r = await check_antenna_movement(hal, AntennaAxis.ELEVATION, AntennaMoveDirection.DOWN)
        check(r.allowed, f"elevacion/down no bloqueado por el limite superior: allowed={r.allowed} ({r.reason})")
        await release(ws, "ant.el_upper_limit_status")
        await asyncio.sleep(0.2)

        # --- fin de carrera inferior de elevacion ------------------------------
        await force(ws, "ant.el_lower_limit_status", True)
        await asyncio.sleep(0.2)
        r = await check_antenna_movement(hal, AntennaAxis.ELEVATION, AntennaMoveDirection.DOWN)
        check(not r.allowed, f"elevacion/down con el_lower_limit_status forzado: allowed={r.allowed} ({r.reason})")
        await release(ws, "ant.el_lower_limit_status")
        await asyncio.sleep(0.2)

        # --- proteccion termica de azimut ---------------------------------------
        await force(ws, "ant.i2t_drive_az_status", True)
        await asyncio.sleep(0.2)
        r = await check_antenna_movement(hal, AntennaAxis.AZIMUTH, AntennaMoveDirection.UP)
        check(not r.allowed, f"azimut con i2t_drive_az_status forzado: allowed={r.allowed} ({r.reason})")
        await release(ws, "ant.i2t_drive_az_status")
        await asyncio.sleep(0.2)
        r = await check_antenna_movement(hal, AntennaAxis.AZIMUTH, AntennaMoveDirection.UP)
        check(r.allowed, f"azimut con traba termica liberada: allowed={r.allowed} ({r.reason})")

    await hal.disconnect()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ws", default="ws://127.0.0.1:18080")
    ap.add_argument("--modbus-port", type=int, default=15020)
    ap.add_argument("--udp-port", type=int, default=15100)
    args = ap.parse_args()

    asyncio.run(run(args.ws, args.modbus_port, args.udp_port))

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FALLA(S):")
        for f in FAILURES:
            print(f" - {f}")
        sys.exit(1)
    print("OK: check_antenna_movement refleja correctamente los limites de elevacion y azimut de radar_emulator.")


if __name__ == "__main__":
    main()
