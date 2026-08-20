"""Spike Fase 2 -- ejercita `core.scan_controller.run_scan_cut` (Scan
Controller, alcance acotado -- ver docstring del modulo) contra una
instancia real de `radar_emulator`, mismo patron de `force`/`release` por
el canal WS de control que el resto de los spikes de Fase 2.

Los parametros de posicionamiento/barrido de aqui abajo son valores de
prueba elegidos para que este spike converja en un tiempo razonable, NO una
recomendacion -- mismo criterio que `antenna_positioning_spike.py`.
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

import websockets

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from adapters.hal_sim import SimulatedHAL
from core.contracts.control import RoutineOutcome
from core.contracts.scan import AxisPositioningParams, PpiCut, RhiCut
from core.control_routines.antenna_movement import AU_ON_STATUS
from core.scan_controller import run_scan_cut

# Solo para este spike -- ver advertencia en el docstring del modulo.
POSITIONING = AxisPositioningParams(gain_v_per_deg=0.3, max_voltage=2.0, tolerance_deg=1.0, timeout_s=25.0)
SWEEP_VOLTAGE = 1.5
SWEEP_TOLERANCE_DEG = 2.0
SWEEP_TIMEOUT_S = 40.0

FAILURES = []


def check(condition, msg):
    print(f"[{'OK   ' if condition else 'FALLA'}] {msg}")
    if not condition:
        FAILURES.append(msg)
    return condition


async def force(ws, signal, value):
    await ws.send(json.dumps({"type": "force", "actor": "spike-fase2-scan-controller", "signal": signal, "value": value}))


async def release(ws, signal):
    await ws.send(json.dumps({"type": "release", "actor": "spike-fase2-scan-controller", "signal": signal}))


async def run(ws_url, modbus_port, udp_port):
    hal = SimulatedHAL(modbus_host="127.0.0.1", modbus_port=modbus_port, udp_bind_host="0.0.0.0", udp_port=udp_port)
    await hal.connect()

    # ping_interval=None: este spike corre minutos reales (barridos completos,
    # no solo confirmar arranque como el resto de Fase 2) -- el keepalive por
    # defecto de `websockets` cerraba la conexion de control a mitad de
    # camino sin que el emulador (que no implementa su propio heartbeat, ver
    # src/adapters/ws/server.ts) tuviera ningun problema real.
    async with websockets.connect(ws_url, ping_interval=None) as ws:
        await asyncio.wait_for(ws.recv(), timeout=2)  # "session" inicial

        for sig in (AU_ON_STATUS, "ant.el_upper_limit_status", "ant.el_lower_limit_status", "ant.i2t_drive_az_status"):
            await release(ws, sig)
        await asyncio.sleep(0.2)

        # --- au_on_status en falso -> falla limpio, propagado desde la Rutina 5 ---
        cut = RhiCut(azimuth_deg=45.0, elevation_start_deg=0.0, elevation_end_deg=15.0, prf_hz=500.0, pulse_width_us=1.0, moments=["UZ"])
        result = await run_scan_cut(
            hal, cut,
            azimuth_positioning=POSITIONING, elevation_positioning=POSITIONING,
            sweep_voltage_magnitude=SWEEP_VOLTAGE, sweep_tolerance_deg=SWEEP_TOLERANCE_DEG, sweep_timeout_s=SWEEP_TIMEOUT_S,
        )
        check(result.outcome == RoutineOutcome.FAILED, f"au_on_status en falso -> outcome={result.outcome}")

        await force(ws, AU_ON_STATUS, True)
        await asyncio.sleep(0.2)

        # --- RhiCut simple, sin wrap: azimut fijo, barre elevacion 0 -> 15 ---
        result = await run_scan_cut(
            hal, cut,
            azimuth_positioning=POSITIONING, elevation_positioning=POSITIONING,
            sweep_voltage_magnitude=SWEEP_VOLTAGE, sweep_tolerance_deg=SWEEP_TOLERANCE_DEG, sweep_timeout_s=SWEEP_TIMEOUT_S,
        )
        pos = await hal.read_antenna_position()
        check(result.outcome == RoutineOutcome.SUCCESS, f"RhiCut az=45 el 0->15 -> outcome={result.outcome}")
        check(abs(pos.el_deg - 15.0) <= 4.0, f"elevacion final={pos.el_deg:.3f} deg (objetivo 15 +/- 4, margen por frenado/deteccion)")
        check(abs(pos.az_deg - 45.0) <= 4.0, f"azimut se mantuvo fijo en 45: final={pos.az_deg:.3f} deg")

        # --- PpiCut simple, sin vuelta completa: elevacion fija, barre azimut 90 -> 180 ---
        cut2 = PpiCut(elevation_deg=10.0, azimuth_start_deg=90.0, azimuth_end_deg=180.0, prf_hz=500.0, pulse_width_us=1.0, moments=["UZ"])
        result = await run_scan_cut(
            hal, cut2,
            azimuth_positioning=POSITIONING, elevation_positioning=POSITIONING,
            sweep_voltage_magnitude=SWEEP_VOLTAGE, sweep_tolerance_deg=SWEEP_TOLERANCE_DEG, sweep_timeout_s=SWEEP_TIMEOUT_S,
        )
        pos = await hal.read_antenna_position()
        check(result.outcome == RoutineOutcome.SUCCESS, f"PpiCut el=10 az 90->180 -> outcome={result.outcome}")
        check(abs(pos.el_deg - 10.0) <= 4.0, f"elevacion se mantuvo fija en 10: final={pos.el_deg:.3f} deg")
        az_error = ((pos.az_deg - 180.0 + 180.0) % 360.0) - 180.0
        check(abs(az_error) <= 4.0, f"azimut final={pos.az_deg:.3f} deg (objetivo 180 +/- 4, margen por frenado/deteccion)")

        # --- interrupcion: traba termica de azimut a mitad de un barrido de azimut ---
        cut3 = PpiCut(elevation_deg=10.0, azimuth_start_deg=180.0, azimuth_end_deg=270.0, prf_hz=500.0, pulse_width_us=1.0, moments=["UZ"])
        task = asyncio.create_task(
            run_scan_cut(
                hal, cut3,
                azimuth_positioning=POSITIONING, elevation_positioning=POSITIONING,
                sweep_voltage_magnitude=SWEEP_VOLTAGE, sweep_tolerance_deg=SWEEP_TOLERANCE_DEG, sweep_timeout_s=SWEEP_TIMEOUT_S,
            )
        )
        # espera a que el barrido este realmente en curso (no solo el
        # posicionamiento previo, que tambien mueve azimut) antes de forzar
        # la traba -- se detecta que el azimut ya avanzo unos grados mas
        # alla del punto de partida (180), en vez de adivinar un sleep fijo.
        deadline = time.monotonic() + 30.0
        in_sweep = False
        while time.monotonic() < deadline:
            pos = await hal.read_antenna_position()
            if pos.az_deg > 185.0:
                in_sweep = True
                break
            await asyncio.sleep(0.3)
        check(in_sweep, "barrido de azimut detectado en curso antes de forzar la traba termica")
        await force(ws, "ant.i2t_drive_az_status", True)
        result = await task
        check(result.outcome == RoutineOutcome.INTERRUPTED, f"traba termica azimut a mitad del barrido -> outcome={result.outcome}")
        await release(ws, "ant.i2t_drive_az_status")
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
    print("OK: run_scan_cut ejercitado (falla, exito PPI/RHI, interrupcion) contra instancia real de radar_emulator.")


if __name__ == "__main__":
    main()
