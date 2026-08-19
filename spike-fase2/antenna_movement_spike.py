"""Spike Fase 2 -- ejercita `core.control_routines.run_antenna_movement`
(Rutina 5, movimiento de antena) contra una instancia real de
`radar_emulator`, forzando `ant.au_on_status` y los limites/traba termica
via el canal de control WS -- mismo patron que
spike-fase2/general_power_on_spike.py y
spike-fase2/parameter_guard_spike.py.

No confirma magnitud de velocidad (ver docstring de
`antenna_movement.py` -- exigiria una ganancia real que no existe); solo
sentido de giro y que el movimiento efectivamente arranca/se detiene.
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
from core.contracts.safety import AntennaAxis
from core.control_routines import run_antenna_movement
from core.control_routines.antenna_movement import AU_ON_STATUS, ENABLE_DRIVE_SIGNAL, SPEED_REFERENCE_SIGNAL

FAILURES = []


def check(condition, msg):
    print(f"[{'OK   ' if condition else 'FALLA'}] {msg}")
    if not condition:
        FAILURES.append(msg)
    return condition


async def force(ws, signal, value):
    await ws.send(json.dumps({"type": "force", "actor": "spike-fase2-antenna-movement", "signal": signal, "value": value}))


async def release(ws, signal):
    await ws.send(json.dumps({"type": "release", "actor": "spike-fase2-antenna-movement", "signal": signal}))


async def run(ws_url, modbus_port, udp_port):
    hal = SimulatedHAL(modbus_host="127.0.0.1", modbus_port=modbus_port, udp_bind_host="0.0.0.0", udp_port=udp_port)
    await hal.connect()

    async with websockets.connect(ws_url) as ws:
        await asyncio.wait_for(ws.recv(), timeout=2)  # "session" inicial

        for sig in (AU_ON_STATUS, "ant.el_upper_limit_status", "ant.el_lower_limit_status", "ant.i2t_drive_az_status"):
            await release(ws, sig)
        await asyncio.sleep(0.2)

        # --- precondicion: au_on_status en falso -> falla sin escribir nada ---
        before_enable = await hal.read_digital(ENABLE_DRIVE_SIGNAL[AntennaAxis.AZIMUTH])
        before_speed = await hal.read_analog(SPEED_REFERENCE_SIGNAL[AntennaAxis.AZIMUTH])
        result = await run_antenna_movement(hal, AntennaAxis.AZIMUTH, 5.0)
        after_enable = await hal.read_digital(ENABLE_DRIVE_SIGNAL[AntennaAxis.AZIMUTH])
        after_speed = await hal.read_analog(SPEED_REFERENCE_SIGNAL[AntennaAxis.AZIMUTH])
        check(result.outcome == RoutineOutcome.FAILED, f"au_on_status en falso -> outcome={result.outcome}")
        check(
            before_enable.value == after_enable.value and before_speed.value == after_speed.value,
            "no se escribio nada al HAL cuando falla la precondicion au_on_status",
        )

        # --- au_on_status en verdadero, sin limites -> azimut arranca y se detiene ---
        await force(ws, AU_ON_STATUS, True)
        await asyncio.sleep(0.2)

        result = await run_antenna_movement(hal, AntennaAxis.AZIMUTH, 5.0)
        check(result.outcome == RoutineOutcome.SUCCESS, f"azimut +5V sin trabas -> outcome={result.outcome}")

        result = await run_antenna_movement(hal, AntennaAxis.AZIMUTH, 0.0)
        check(result.outcome == RoutineOutcome.SUCCESS, f"azimut detencion -> outcome={result.outcome}")

        # --- traba termica de azimut ya activa antes de empezar -> falla, nada escrito ---
        await force(ws, "ant.i2t_drive_az_status", True)
        await asyncio.sleep(0.2)
        before_speed = await hal.read_analog(SPEED_REFERENCE_SIGNAL[AntennaAxis.AZIMUTH])
        result = await run_antenna_movement(hal, AntennaAxis.AZIMUTH, 5.0)
        after_speed = await hal.read_analog(SPEED_REFERENCE_SIGNAL[AntennaAxis.AZIMUTH])
        check(result.outcome == RoutineOutcome.FAILED, f"traba termica azimut activa de antemano -> outcome={result.outcome}")
        check(before_speed.value == after_speed.value, "referencia de azimut no se toco con la traba termica ya activa")
        await release(ws, "ant.i2t_drive_az_status")
        await asyncio.sleep(0.2)

        # --- traba termica de azimut disparada a mitad de camino -> interrumpido ---
        # sleep corto para dejar que la rutina termine precondicion+escritura y quede
        # dentro de su sleep de sondeo antes de forzar la traba (si no, la carrera la
        # ve la propia guarda de precondicion y da FAILED en vez de INTERRUPTED)
        task = asyncio.create_task(run_antenna_movement(hal, AntennaAxis.AZIMUTH, 5.0))
        await asyncio.sleep(0.05)
        await force(ws, "ant.i2t_drive_az_status", True)
        result = await task
        check(result.outcome == RoutineOutcome.INTERRUPTED, f"traba termica azimut a mitad de camino -> outcome={result.outcome}")
        await asyncio.sleep(0.15)  # el ultimo write_digital de la rutina queda pendiente hasta el siguiente tick (hal.py)
        enable_after = await hal.read_digital(ENABLE_DRIVE_SIGNAL[AntennaAxis.AZIMUTH])
        check(enable_after.value is False, f"variador de azimut deshabilitado tras interrupcion: value={enable_after.value}")
        await release(ws, "ant.i2t_drive_az_status")
        await asyncio.sleep(0.2)

        # --- fin de carrera superior de elevacion, ya activo -> falla ---
        await force(ws, "ant.el_upper_limit_status", True)
        await asyncio.sleep(0.2)
        result = await run_antenna_movement(hal, AntennaAxis.ELEVATION, 5.0)
        check(result.outcome == RoutineOutcome.FAILED, f"fin de carrera superior activo de antemano -> outcome={result.outcome}")
        await release(ws, "ant.el_upper_limit_status")
        await asyncio.sleep(0.2)

        # --- fin de carrera superior de elevacion, disparado a mitad de camino -> interrumpido ---
        task = asyncio.create_task(run_antenna_movement(hal, AntennaAxis.ELEVATION, 5.0))
        await asyncio.sleep(0.05)
        await force(ws, "ant.el_upper_limit_status", True)
        result = await task
        check(result.outcome == RoutineOutcome.INTERRUPTED, f"fin de carrera superior a mitad de camino -> outcome={result.outcome}")
        await release(ws, "ant.el_upper_limit_status")
        await asyncio.sleep(0.2)
        await run_antenna_movement(hal, AntennaAxis.ELEVATION, 0.0)  # deja el eje detenido

        for sig in (AU_ON_STATUS, "ant.el_upper_limit_status", "ant.el_lower_limit_status", "ant.i2t_drive_az_status"):
            await release(ws, sig)

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
    print("OK: run_antenna_movement ejercitado (falla, exito, interrupcion) contra instancia real de radar_emulator.")


if __name__ == "__main__":
    main()
