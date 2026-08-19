"""Spike Fase 2 -- ejercita `core.control_routines.run_general_power_on` contra una
instancia real de `radar_emulator` (Modbus TCP + su canal de control WS para forzar
las tres precondiciones, igual patron que spike-fase1/fault_injection_spike.py).

`sys.turn_on_radar_conmand` no tiene ningun bloque de logica en el emulador (a
diferencia de `tx.fsm`), asi que este spike solo puede confirmar "el pulso se
envio y las precondiciones siguen en OK" -- no que la secuencia elegida sea la
correcta para hardware real. Ver PEND-RCP-06 (docs/alcance/pendientes.md) y el
docstring de `general_power_on.py`.
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
from core.control_routines import run_general_power_on
from core.control_routines.general_power_on import COMMAND_ON, PRECONDITIONS

FAILURES = []


def check(condition, msg):
    print(f"[{'OK   ' if condition else 'FALLA'}] {msg}")
    if not condition:
        FAILURES.append(msg)
    return condition


async def force(ws, signal, value):
    await ws.send(json.dumps({"type": "force", "actor": "spike-fase2-general-power-on", "signal": signal, "value": value}))


async def release(ws, signal):
    await ws.send(json.dumps({"type": "release", "actor": "spike-fase2-general-power-on", "signal": signal}))


async def run(ws_url, modbus_port, udp_port):
    hal = SimulatedHAL(modbus_host="127.0.0.1", modbus_port=modbus_port, udp_bind_host="0.0.0.0", udp_port=udp_port)
    await hal.connect()

    async with websockets.connect(ws_url) as ws:
        await asyncio.wait_for(ws.recv(), timeout=2)  # "session" inicial

        # --- precondiciones en falso (default de la semilla): la rutina debe fallar sin comandar nada ---
        for signal_id in PRECONDITIONS:
            await release(ws, signal_id)
        await asyncio.sleep(0.2)

        before = await hal.read_digital(COMMAND_ON)
        result = await run_general_power_on(hal)
        after = await hal.read_digital(COMMAND_ON)

        check(result.outcome == RoutineOutcome.FAILED, f"precondiciones en falso -> outcome={result.outcome}")
        check(
            not all(s.ok for s in result.steps),
            f"al menos un paso reporta ok=False: {[(s.signal_id, s.ok) for s in result.steps]}",
        )
        check(
            after.value == before.value == False,  # noqa: E712 -- comparacion explicita de bool de dominio
            f"comando {COMMAND_ON} no se toco cuando fallan precondiciones (before={before.value} after={after.value})",
        )

        # --- precondiciones en verdadero: la rutina debe pulsar el comando y reportar exito ---
        for signal_id in PRECONDITIONS:
            await force(ws, signal_id, True)
        await asyncio.sleep(0.2)

        result = await run_general_power_on(hal)
        post = await hal.read_digital(COMMAND_ON)

        check(result.outcome == RoutineOutcome.SUCCESS, f"precondiciones en verdadero -> outcome={result.outcome}")
        check(all(s.ok for s in result.steps), f"todos los pasos reportan ok=True: {[(s.signal_id, s.ok) for s in result.steps]}")
        check(
            post.value == False,  # noqa: E712
            f"comando {COMMAND_ON} vuelve a False tras el pulso (flanco, no nivel) -- post={post.value}",
        )

        for signal_id in PRECONDITIONS:
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
    print("OK: run_general_power_on ejercitado (falla y exito) contra instancia real de radar_emulator.")


if __name__ == "__main__":
    main()
