"""Spike Fase 2 -- ejercita `core.control_routines.run_receiver_power_on`
(Rutina 3, encendido del receptor analogico) contra una instancia real de
`radar_emulator`, forzando las tres fuentes de alimentacion y (a
diferencia de las rutinas anteriores) tambien las senales de exito
(`rx.rfe_on_status`/`rx.stalo_locked_status`) via el canal WS de control --
el subsistema `rx` no tiene ningun bloque de logica en la semilla, ver
docstring de `receiver_power_on.py`.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

import websockets

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from adapters.hal_sim import SimulatedHAL
from core.contracts.control import RoutineOutcome
from core.control_routines import run_receiver_power_on
from core.control_routines.receiver_power_on import COMMAND_ON, POWER_SUPPLY_SIGNALS, RFE_ON_STATUS, STALO_LOCKED_STATUS

FAILURES = []


def check(condition, msg):
    print(f"[{'OK   ' if condition else 'FALLA'}] {msg}")
    if not condition:
        FAILURES.append(msg)
    return condition


async def force(ws, signal, value):
    await ws.send(json.dumps({"type": "force", "actor": "spike-fase2-receiver-power-on", "signal": signal, "value": value}))


async def release(ws, signal):
    await ws.send(json.dumps({"type": "release", "actor": "spike-fase2-receiver-power-on", "signal": signal}))


async def run(ws_url, modbus_port, udp_port):
    hal = SimulatedHAL(modbus_host="127.0.0.1", modbus_port=modbus_port, udp_bind_host="0.0.0.0", udp_port=udp_port)
    await hal.connect()

    async with websockets.connect(ws_url) as ws:
        await asyncio.wait_for(ws.recv(), timeout=2)  # "session" inicial

        for signal_id in (*POWER_SUPPLY_SIGNALS, RFE_ON_STATUS, STALO_LOCKED_STATUS):
            await release(ws, signal_id)
        await asyncio.sleep(0.2)

        # --- fuentes de alimentacion en falso (default, sin bloque que las calcule) -> falla ---
        before = await hal.read_digital(COMMAND_ON)
        result = await run_receiver_power_on(hal, confirm_timeout_s=1.0)
        after = await hal.read_digital(COMMAND_ON)
        check(result.outcome == RoutineOutcome.FAILED, f"fuentes de alimentacion en falso -> outcome={result.outcome}")
        check(before.value == after.value, f"comando {COMMAND_ON} no se toco (before={before.value} after={after.value})")

        # --- fuentes OK pero exito nunca forzado -> falla por timeout (nada calcula rfe_on/stalo) ---
        for signal_id in POWER_SUPPLY_SIGNALS:
            await force(ws, signal_id, True)
        await asyncio.sleep(0.2)

        result = await run_receiver_power_on(hal, confirm_timeout_s=1.0)
        check(
            result.outcome == RoutineOutcome.FAILED,
            f"fuentes OK, RFE/STALO nunca forzados (nada los calcula) -> outcome={result.outcome}",
        )
        pulse_step = next(s for s in result.steps if s.signal_id == COMMAND_ON)
        check(pulse_step.ok, "el pulso a turn_on_rfe_conmand si se envio (precondicion paso)")

        # --- fuentes OK y exito forzado -> confirma la lectura de la rutina, no logica del emulador ---
        await force(ws, RFE_ON_STATUS, True)
        await force(ws, STALO_LOCKED_STATUS, True)
        await asyncio.sleep(0.2)

        result = await run_receiver_power_on(hal, confirm_timeout_s=1.0)
        check(result.outcome == RoutineOutcome.SUCCESS, f"RFE/STALO forzados a verdadero -> outcome={result.outcome}")

        for signal_id in (*POWER_SUPPLY_SIGNALS, RFE_ON_STATUS, STALO_LOCKED_STATUS):
            await release(ws, signal_id)

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
    print("OK: run_receiver_power_on ejercitado contra instancia real de radar_emulator.")


if __name__ == "__main__":
    main()
