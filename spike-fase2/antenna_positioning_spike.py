"""Spike Fase 2 -- ejercita `core.control_routines.run_antenna_positioning`
(Rutina 6, la ultima de las seis) contra una instancia real de
`radar_emulator`, mismo patron de `force`/`release` por el canal WS de
control que el resto de los spikes de Fase 2.

`gain_v_per_deg`, `max_voltage`, `tolerance_deg` y `timeout_s` aqui abajo
son valores de prueba elegidos para este spike, NO una recomendacion --
ver docstring de `antenna_positioning.py`: la rutina los exige como
parametros obligatorios precisamente porque no existe ningun valor real
que usar como default.
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
from core.control_routines import run_antenna_positioning
from core.control_routines.antenna_movement import AU_ON_STATUS

# Solo para este spike -- ver advertencia en el docstring del modulo.
GAIN_V_PER_DEG = 0.3
MAX_VOLTAGE = 2.0
TOLERANCE_DEG = 1.0
TIMEOUT_S = 25.0

# La rutina decide "suficientemente cerca" (TOLERANCE_DEG) *antes* de frenar
# -- con desaceleracion limitada (bloque `axis` del simulador) el eje sigue
# recorriendo distancia mientras frena, asi que la posicion final real puede
# quedar mas lejos que TOLERANCE_DEG (ver "Limitacion conocida" en
# antenna_positioning.py). Este margen es solo para que este spike no falle
# por ese sobrepaso esperado -- no es una tolerancia recomendada.
FINAL_CHECK_MARGIN_DEG = 3.0

FAILURES = []


def check(condition, msg):
    print(f"[{'OK   ' if condition else 'FALLA'}] {msg}")
    if not condition:
        FAILURES.append(msg)
    return condition


async def force(ws, signal, value):
    await ws.send(json.dumps({"type": "force", "actor": "spike-fase2-antenna-positioning", "signal": signal, "value": value}))


async def release(ws, signal):
    await ws.send(json.dumps({"type": "release", "actor": "spike-fase2-antenna-positioning", "signal": signal}))


async def run(ws_url, modbus_port, udp_port):
    hal = SimulatedHAL(modbus_host="127.0.0.1", modbus_port=modbus_port, udp_bind_host="0.0.0.0", udp_port=udp_port)
    await hal.connect()

    async with websockets.connect(ws_url) as ws:
        await asyncio.wait_for(ws.recv(), timeout=2)  # "session" inicial

        for sig in (AU_ON_STATUS, "ant.el_upper_limit_status", "ant.el_lower_limit_status", "ant.i2t_drive_az_status"):
            await release(ws, sig)
        await ws.send(json.dumps({"type": "degrade", "actor": "spike-fase2-antenna-positioning", "kind": "encoder_invalid", "active": False}))
        await asyncio.sleep(0.2)

        # radar_emulator es un proceso persistente durante toda la sesion -- no asumir
        # posicion inicial exacta, solo que el eje esta detenido (spikes previos lo dejaron asi).
        baseline = await hal.read_antenna_position()
        check(abs(baseline.az_rate_deg_s) < 0.1 and abs(baseline.el_rate_deg_s) < 0.1, f"baseline detenido: az_rate={baseline.az_rate_deg_s} el_rate={baseline.el_rate_deg_s}")
        az_target = baseline.az_deg + 15.0
        el_target = min(baseline.el_deg + 10.0, 40.0)

        # --- lectura de posicion invalida -> falla sin intentar mover ---------
        await ws.send(json.dumps({"type": "degrade", "actor": "spike-fase2-antenna-positioning", "kind": "encoder_invalid", "active": True}))
        await asyncio.sleep(0.2)
        result = await run_antenna_positioning(
            hal, AntennaAxis.AZIMUTH, 15.0,
            gain_v_per_deg=GAIN_V_PER_DEG, max_voltage=MAX_VOLTAGE, tolerance_deg=TOLERANCE_DEG, timeout_s=TIMEOUT_S,
        )
        check(result.outcome == RoutineOutcome.FAILED, f"encoder invalido -> outcome={result.outcome}")
        await ws.send(json.dumps({"type": "degrade", "actor": "spike-fase2-antenna-positioning", "kind": "encoder_invalid", "active": False}))
        await asyncio.sleep(0.2)

        # --- au_on_status en falso -> la Rutina 5 subyacente rechaza, se propaga ---
        result = await run_antenna_positioning(
            hal, AntennaAxis.AZIMUTH, 15.0,
            gain_v_per_deg=GAIN_V_PER_DEG, max_voltage=MAX_VOLTAGE, tolerance_deg=TOLERANCE_DEG, timeout_s=TIMEOUT_S,
        )
        check(result.outcome == RoutineOutcome.FAILED, f"au_on_status en falso -> outcome={result.outcome}")

        await force(ws, AU_ON_STATUS, True)
        await asyncio.sleep(0.2)

        # --- posicionamiento normal de azimut ----------------------------------
        result = await run_antenna_positioning(
            hal, AntennaAxis.AZIMUTH, az_target,
            gain_v_per_deg=GAIN_V_PER_DEG, max_voltage=MAX_VOLTAGE, tolerance_deg=TOLERANCE_DEG, timeout_s=TIMEOUT_S,
        )
        pos = await hal.read_antenna_position()
        check(result.outcome == RoutineOutcome.SUCCESS, f"azimut -> {az_target:.1f} deg: outcome={result.outcome}")
        check(
            abs(pos.az_deg - az_target) <= FINAL_CHECK_MARGIN_DEG,
            f"azimut final={pos.az_deg:.3f} deg (objetivo {az_target:.1f} +/- {FINAL_CHECK_MARGIN_DEG}, margen por sobrepaso de frenado)",
        )

        # --- posicionamiento normal de elevacion -------------------------------
        result = await run_antenna_positioning(
            hal, AntennaAxis.ELEVATION, el_target,
            gain_v_per_deg=GAIN_V_PER_DEG, max_voltage=MAX_VOLTAGE, tolerance_deg=TOLERANCE_DEG, timeout_s=TIMEOUT_S,
        )
        pos = await hal.read_antenna_position()
        check(result.outcome == RoutineOutcome.SUCCESS, f"elevacion -> {el_target:.1f} deg: outcome={result.outcome}")
        check(
            abs(pos.el_deg - el_target) <= FINAL_CHECK_MARGIN_DEG,
            f"elevacion final={pos.el_deg:.3f} deg (objetivo {el_target:.1f} +/- {FINAL_CHECK_MARGIN_DEG}, margen por sobrepaso de frenado)",
        )

        # --- fin de carrera superior activo de antemano -> guarda rechaza, se propaga ---
        await force(ws, "ant.el_upper_limit_status", True)
        await asyncio.sleep(0.2)
        result = await run_antenna_positioning(
            hal, AntennaAxis.ELEVATION, el_target + 40.0,
            gain_v_per_deg=GAIN_V_PER_DEG, max_voltage=MAX_VOLTAGE, tolerance_deg=TOLERANCE_DEG, timeout_s=TIMEOUT_S,
        )
        check(result.outcome == RoutineOutcome.FAILED, f"fin de carrera activo de antemano -> outcome={result.outcome}")
        await release(ws, "ant.el_upper_limit_status")
        await asyncio.sleep(0.2)

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
    print("OK: run_antenna_positioning ejercitado contra instancia real de radar_emulator.")


if __name__ == "__main__":
    main()
