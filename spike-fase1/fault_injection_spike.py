"""Spike Fase 1 -- inyeccion de fallos: dispara degradaciones reales en
`radar_emulator` (via su canal de control WS, "el cliente pide, no
decide" -- docs/interfaces/websocket.md) y verifica que
`src/adapters/hal_sim/SimulatedHAL` las refleje correctamente.

Complementa spike-fase0/udp_degradation_spike.py (que probaba el parser
UDP crudo contra paquetes sinteticos y en vivo): esto prueba el camino
completo hasta el adaptador de produccion, no un socket ad-hoc.

Solo ejercita las tres degradaciones cuyo efecto es observable a traves de
`SimulatedHAL.read_antenna_position()` (encoder invalido, congelacion,
silencio) -- las de perdida/rafaga/duplicacion/reordenamiento/jitter/salto
de secuencia son ruido a nivel de paquete que el receptor ya absorbe sin
cambiar el valor expuesto (ver udp_encoder.py), y ya estan cubiertas por
el spike de Fase 0.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

import websockets

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from adapters.hal_sim import SimulatedHAL

FAILURES = []


def check(condition, msg):
    print(f"[{'OK   ' if condition else 'FALLA'}] {msg}")
    if not condition:
        FAILURES.append(msg)
    return condition


async def degrade(ws, kind, **kw):
    await ws.send(json.dumps({"type": "degrade", "actor": "spike-fase1-fault-injection", "kind": kind, **kw}))


async def run(ws_url, modbus_port, udp_port):
    hal = SimulatedHAL(modbus_host="127.0.0.1", modbus_port=modbus_port, udp_bind_host="0.0.0.0", udp_port=udp_port)
    await hal.connect()

    async with websockets.connect(ws_url) as ws:
        await asyncio.wait_for(ws.recv(), timeout=2)  # "session" inicial

        await asyncio.sleep(0.2)
        baseline = await hal.read_antenna_position()
        check(baseline.az_valid and baseline.el_valid, f"baseline: az_valid={baseline.az_valid} el_valid={baseline.el_valid}")

        # --- encoder invalido -------------------------------------------------
        await degrade(ws, "encoder_invalid", active=True)
        await asyncio.sleep(0.2)
        pos = await hal.read_antenna_position()
        check(not pos.az_valid and not pos.el_valid, f"encoder_invalid activo: az_valid={pos.az_valid} el_valid={pos.el_valid}")
        await degrade(ws, "encoder_invalid", active=False)
        await asyncio.sleep(0.2)
        pos = await hal.read_antenna_position()
        check(pos.az_valid and pos.el_valid, f"encoder_invalid desactivado: az_valid={pos.az_valid} el_valid={pos.el_valid}")

        # --- congelacion --------------------------------------------------------
        await degrade(ws, "freeze", active=True)
        await asyncio.sleep(0.15)
        pos_a = await hal.read_antenna_position()
        await asyncio.sleep(0.15)
        pos_b = await hal.read_antenna_position()
        check(
            pos_a.az_deg == pos_b.az_deg and pos_a.el_deg == pos_b.el_deg and pos_b.seq != pos_a.seq,
            f"freeze: posicion constante (az {pos_a.az_deg}=={pos_b.az_deg}) con seq avanzando ({pos_a.seq} -> {pos_b.seq})",
        )
        await degrade(ws, "freeze", active=False)
        await asyncio.sleep(0.2)

        # --- silencio total -------------------------------------------------
        await degrade(ws, "silence", active=True)
        await asyncio.sleep(0.2)  # > STALE_TIMEOUT_S (100 ms) del receptor
        try:
            await hal.read_antenna_position()
            check(False, "silence activo: read_antenna_position() debia lanzar RuntimeError (stream perdido)")
        except RuntimeError as e:
            check(True, f"silence activo: read_antenna_position() lanza RuntimeError ({e})")
        await degrade(ws, "silence", active=False)
        await asyncio.sleep(0.2)
        pos = await hal.read_antenna_position()
        check(pos.az_valid, "silence desactivado: el stream se recupera, read_antenna_position() vuelve a responder")

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
    print("OK: SimulatedHAL refleja correctamente encoder_invalid, freeze y silence disparados en radar_emulator.")


if __name__ == "__main__":
    main()
