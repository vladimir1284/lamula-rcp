"""Spike Fase 1 -- ejercita `src/adapters/hal_sim/SimulatedHAL` contra una instancia
real de `radar_emulator` (Modbus TCP + UDP RD100S-ENC-UDP v1).

No es una prueba unitaria del adaptador (eso vive en pytest cuando se decida
como mockear Modbus/UDP); es la prueba de humo end-to-end que corrio contra
el emulador real de verdad, igual que `modbus_client_spike.py` y
`udp_encoder_spike.py` de Fase 0 -- ver `README-hal-sim.md` para como
levantar el emulador con los puertos no privilegiados de esta prueba.
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from adapters.hal_sim import SimulatedHAL

FAILURES = []


def check(condition, msg):
    print(f"[{'OK   ' if condition else 'FALLA'}] {msg}")
    if not condition:
        FAILURES.append(msg)
    return condition


async def run(modbus_host, modbus_port, udp_bind_host, udp_port):
    hal = SimulatedHAL(
        modbus_host=modbus_host,
        modbus_port=modbus_port,
        udp_bind_host=udp_bind_host,
        udp_port=udp_port,
    )
    await hal.connect()
    check(hal.is_connected(), "conectado a Modbus")

    r = await hal.read_digital("tx.tx_on_status")
    check(r.value in (True, False), f"read_digital tx.tx_on_status = {r.value}, quality={r.quality}")

    r = await hal.read_analog("tx.mps_output_voltage_sample")
    check(0.0 <= r.value <= 30.0, f"read_analog tx.mps_output_voltage_sample = {r.value:.3f} kV, quality={r.quality}")

    await hal.write_digital("tx.turn_on_tx_command", True)
    check(True, "write_digital tx.turn_on_tx_command(True) no lanzo excepcion")

    await hal.write_analog("tx.voltage_reference_mps", 5.0)
    await asyncio.sleep(0.15)  # tick_ms=50 + margen -- hal.py: no asumir read-your-write inmediato
    r = await hal.read_analog("tx.voltage_reference_mps")
    check(abs(r.value - 5.0) < 0.01, f"write_analog(5.0V) + read-back tras tick = {r.value:.4f} V")

    try:
        await hal.write_digital("tx.tx_on_status", True)
        check(False, "write_digital sobre DI de solo lectura debia lanzar ValueError")
    except ValueError:
        check(True, "write_digital sobre DI de solo lectura lanza ValueError (guard del adaptador)")

    try:
        await hal.read_digital("no.existe")
        check(False, "read_digital de senal inexistente debia lanzar KeyError")
    except KeyError:
        check(True, "read_digital de senal inexistente lanza KeyError")

    await asyncio.sleep(0.3)  # dar tiempo a que llegue al menos un paquete UDP (100 Hz nominal)
    pos = await hal.read_antenna_position()
    check(
        0.0 <= pos.az_deg < 360.0,
        f"read_antenna_position az_deg={pos.az_deg:.3f} el_deg={pos.el_deg:.3f} seq={pos.seq}",
    )

    await hal.disconnect()
    check(not hal.is_connected(), "disconnect() deja is_connected() en False")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--modbus-host", default="127.0.0.1")
    ap.add_argument("--modbus-port", type=int, default=15020)
    ap.add_argument("--udp-bind-host", default="0.0.0.0")
    ap.add_argument("--udp-port", type=int, default=15100)
    args = ap.parse_args()

    asyncio.run(run(args.modbus_host, args.modbus_port, args.udp_bind_host, args.udp_port))

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FALLA(S):")
        for f in FAILURES:
            print(f" - {f}")
        sys.exit(1)
    print("OK: SimulatedHAL ejercitado contra instancia real de radar_emulator.")


if __name__ == "__main__":
    main()
