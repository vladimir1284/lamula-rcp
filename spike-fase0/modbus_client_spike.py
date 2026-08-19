"""Spike Modbus fase 0 — cliente pymodbus contra radar_emulator.

Interroga los diez unit IDs de la semilla RD100S sobre una sola conexion TCP,
ejercitando FC01/03/05/06/15/16 segun el mapa de docs/interfaces/modbus.md de
radar_emulator. No es codigo de produccion.
"""

import argparse
import sys
import time

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

# El emulador no aplica escrituras al instante: quedan pendientes y se
# consumen en el siguiente tick (signal-store.ts, D-15 "flanco no nivel"),
# tick_ms=50 en la semilla. Un read-back inmediato es una condicion de
# carrera, no un fallo del servidor. Se espera un tick completo + margen.
TICK_SETTLE_S = 0.12

# unit_id -> (di_count, do_count, ai_count, ao_count), direcciones por
# "Regla de mapeo por defecto": DI en 0.., DO en 16.., AI/AO en 0..
UNITS = {
    1: dict(label="tx/ADAM 4051", di=16, do=0, ai=0, ao=0),
    2: dict(label="tx/ADAM 4024", di=4, do=0, ai=0, ao=4),
    3: dict(label="tx/ADAM 4069", di=0, do=8, ai=0, ao=0),
    4: dict(label="tx/ADAM 4117", di=0, do=0, ai=8, ao=0),
    11: dict(label="ant/ADAM 4051", di=16, do=0, ai=0, ao=0),
    12: dict(label="ant/ADAM 4024", di=4, do=0, ai=0, ao=4),
    13: dict(label="ant/ADAM 4069", di=0, do=8, ai=0, ao=0),
    14: dict(label="ant/ADAM 4117", di=0, do=0, ai=8, ao=0),
    21: dict(label="rx/ADAM 4150", di=7, do=8, ai=0, ao=0),
    31: dict(label="sys/ADAM 4055", di=8, do=8, ai=0, ao=0),
}

DO_BASE = 16
failures = []


def check(condition, msg):
    status = "OK " if condition else "FALLA"
    print(f"[{status}] {msg}")
    if not condition:
        failures.append(msg)


def spike(client):
    for unit_id, spec in UNITS.items():
        label = f"unit {unit_id} ({spec['label']})"

        if spec["di"]:
            r = client.read_coils(0, count=spec["di"], device_id=unit_id)
            check(not r.isError() and len(r.bits) >= spec["di"], f"{label}: FC01 lee {spec['di']} DI")

        if spec["ai"]:
            r = client.read_holding_registers(0, count=spec["ai"], device_id=unit_id)
            check(
                not r.isError() and len(r.registers) == spec["ai"],
                f"{label}: FC03 lee {spec['ai']} AI",
            )

        if spec["do"]:
            r = client.read_coils(DO_BASE, count=spec["do"], device_id=unit_id)
            check(not r.isError(), f"{label}: FC01 lee {spec['do']} DO (baseline)")

            # FC05 write single coil + read-back
            target = DO_BASE
            new_val = not r.bits[0]
            w = client.write_coil(target, new_val, device_id=unit_id)
            time.sleep(TICK_SETTLE_S)
            rb = client.read_coils(target, count=1, device_id=unit_id)
            check(
                not w.isError() and not rb.isError() and rb.bits[0] == new_val,
                f"{label}: FC05 write_coil({target}, {new_val}) + read-back",
            )

            # FC15 write multiple coils + read-back
            pattern = [bool(i % 2) for i in range(spec["do"])]
            w = client.write_coils(DO_BASE, pattern, device_id=unit_id)
            time.sleep(TICK_SETTLE_S)
            rb = client.read_coils(DO_BASE, count=spec["do"], device_id=unit_id)
            check(
                not w.isError() and not rb.isError() and list(rb.bits[: spec["do"]]) == pattern,
                f"{label}: FC15 write_coils(pattern) + read-back",
            )

        if spec["ao"]:
            r = client.read_holding_registers(0, count=spec["ao"], device_id=unit_id)
            check(not r.isError(), f"{label}: FC03 lee {spec['ao']} AO (baseline)")

            # FC06 write single register + read-back
            new_val = (r.registers[0] + 1234) % 65536
            w = client.write_register(0, new_val, device_id=unit_id)
            time.sleep(TICK_SETTLE_S)
            rb = client.read_holding_registers(0, count=1, device_id=unit_id)
            check(
                not w.isError() and not rb.isError() and rb.registers[0] == new_val,
                f"{label}: FC06 write_register(0, {new_val}) + read-back",
            )

            # FC16 write multiple registers + read-back
            pattern = [(1000 + i) for i in range(spec["ao"])]
            w = client.write_registers(0, pattern, device_id=unit_id)
            time.sleep(TICK_SETTLE_S)
            rb = client.read_holding_registers(0, count=spec["ao"], device_id=unit_id)
            check(
                not w.isError() and not rb.isError() and list(rb.registers) == pattern,
                f"{label}: FC16 write_registers(pattern) + read-back",
            )

    # Regla dura de modbus.md: escribir una DI de solo lectura debe dar excepcion,
    # no aceptarse en silencio. Unit 1, addr 0 (tx.tx_on_status).
    try:
        w = client.write_coil(0, True, device_id=1)
        check(w.isError(), "unit 1: FC05 sobre DI de solo lectura devuelve excepcion Modbus")
    except ModbusException:
        check(True, "unit 1: FC05 sobre DI de solo lectura devuelve excepcion Modbus")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=15020)
    args = ap.parse_args()

    client = ModbusTcpClient(args.host, port=args.port)
    if not client.connect():
        print(f"No se pudo conectar a {args.host}:{args.port}", file=sys.stderr)
        sys.exit(2)

    try:
        spike(client)
    finally:
        client.close()

    print()
    if failures:
        print(f"{len(failures)} FALLA(S):")
        for f in failures:
            print(f" - {f}")
        sys.exit(1)
    print(f"OK: {len(UNITS)} unit IDs interrogados sobre una sola conexion TCP, FC01/03/05/06/15/16 verificados.")


if __name__ == "__main__":
    main()
