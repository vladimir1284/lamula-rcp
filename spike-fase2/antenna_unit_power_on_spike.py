"""Spike Fase 2 -- ejercita `core.control_routines.run_antenna_unit_power_on`
(Rutina 4, encendido de la unidad de antena) contra una instancia real de
`radar_emulator`. Igual que el receptor (Rutina 3), el subsistema de
unidad de antena no tiene ningun bloque de logica en la semilla -- se
fuerzan tambien las senales de exito (`ant.au_on_status`,
`ant.drive_az_ok_status`, `ant.drive_el_ok_status`), no solo la
precondicion, via el canal WS de control.
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
from core.control_routines import run_antenna_unit_power_on
from core.control_routines.antenna_unit_power_on import AU_ON_STATUS, COMMAND_ON, DRIVE_OK_SIGNALS, RADOME_CLOSED_STATUS

FAILURES = []


def check(condition, msg):
    print(f"[{'OK   ' if condition else 'FALLA'}] {msg}")
    if not condition:
        FAILURES.append(msg)
    return condition


async def force(ws, signal, value):
    await ws.send(json.dumps({"type": "force", "actor": "spike-fase2-antenna-unit-power-on", "signal": signal, "value": value}))


async def release(ws, signal):
    await ws.send(json.dumps({"type": "release", "actor": "spike-fase2-antenna-unit-power-on", "signal": signal}))


async def run(ws_url, modbus_port, udp_port):
    hal = SimulatedHAL(modbus_host="127.0.0.1", modbus_port=modbus_port, udp_bind_host="0.0.0.0", udp_port=udp_port)
    await hal.connect()

    async with websockets.connect(ws_url) as ws:
        await asyncio.wait_for(ws.recv(), timeout=2)  # "session" inicial

        for signal_id in (RADOME_CLOSED_STATUS, AU_ON_STATUS, *DRIVE_OK_SIGNALS):
            await release(ws, signal_id)
        await asyncio.sleep(0.2)

        # --- radomo abierto (default) -> falla sin escribir el comando --------
        before = await hal.read_digital(COMMAND_ON)
        result = await run_antenna_unit_power_on(hal, confirm_timeout_s=1.0)
        after = await hal.read_digital(COMMAND_ON)
        check(result.outcome == RoutineOutcome.FAILED, f"radomo abierto -> outcome={result.outcome}")
        check(before.value == after.value, f"comando {COMMAND_ON} no se toco (before={before.value} after={after.value})")

        # --- radomo cerrado pero au_on/drives nunca forzados -> falla por timeout ---
        await force(ws, RADOME_CLOSED_STATUS, True)
        await asyncio.sleep(0.2)

        result = await run_antenna_unit_power_on(hal, confirm_timeout_s=1.0)
        check(
            result.outcome == RoutineOutcome.FAILED,
            f"radomo cerrado, au_on/drives nunca forzados (nada los calcula) -> outcome={result.outcome}",
        )
        command_step = next(s for s in result.steps if s.signal_id == COMMAND_ON)
        check(command_step.ok, "el comando si se escribio a nivel alto (precondicion paso)")
        await asyncio.sleep(0.15)
        after_command = await hal.read_digital(COMMAND_ON)
        check(after_command.value is True, f"comando queda en nivel alto (no es un pulso): value={after_command.value}")

        # --- radomo cerrado y exito forzado -> confirma la lectura de la rutina ---
        await force(ws, AU_ON_STATUS, True)
        for signal_id in DRIVE_OK_SIGNALS:
            await force(ws, signal_id, True)
        await asyncio.sleep(0.2)

        result = await run_antenna_unit_power_on(hal, confirm_timeout_s=1.0)
        check(result.outcome == RoutineOutcome.SUCCESS, f"au_on/drives forzados a verdadero -> outcome={result.outcome}")

        for signal_id in (RADOME_CLOSED_STATUS, AU_ON_STATUS, *DRIVE_OK_SIGNALS):
            await release(ws, signal_id)
        await hal.write_digital(COMMAND_ON, False)  # deja el comando como estaba, no fue un force

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
    print("OK: run_antenna_unit_power_on ejercitado contra instancia real de radar_emulator.")


if __name__ == "__main__":
    main()
