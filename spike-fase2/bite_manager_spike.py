"""Spike Fase 2 -- ejercita `core.bite.BiteManager` contra una instancia
real de `radar_emulator`, forzando senales de falla via el canal WS de
control -- mismo patron que el resto de los spikes de Fase 1/2.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

import websockets

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from adapters.hal_sim import SimulatedHAL
from core.bite import BiteManager
from core.contracts.bite import BiteTransition

FAILURES = []


def check(condition, msg):
    print(f"[{'OK   ' if condition else 'FALLA'}] {msg}")
    if not condition:
        FAILURES.append(msg)
    return condition


async def force(ws, signal, value):
    await ws.send(json.dumps({"type": "force", "actor": "spike-fase2-bite-manager", "signal": signal, "value": value}))


async def release(ws, signal):
    await ws.send(json.dumps({"type": "release", "actor": "spike-fase2-bite-manager", "signal": signal}))


async def run(ws_url, modbus_port, udp_port):
    hal = SimulatedHAL(modbus_host="127.0.0.1", modbus_port=modbus_port, udp_bind_host="0.0.0.0", udp_port=udp_port)
    await hal.connect()
    bite = BiteManager()

    async with websockets.connect(ws_url) as ws:
        await asyncio.wait_for(ws.recv(), timeout=2)  # "session" inicial

        # las tres precondiciones sys.* estan en falso por default (semilla) -- primer poll
        # debe reportarlas como falla ya presente, no silenciosamente.
        for sig in ("sys.line_parameters_ok_status", "sys.environment_ok_status", "sys.standby_system_ok_status"):
            await release(ws, sig)
        await asyncio.sleep(0.2)

        events = await bite.poll(hal)
        check(
            {e.signal_id for e in events} >= {"sys.line_parameters_ok_status", "sys.environment_ok_status", "sys.standby_system_ok_status"},
            f"primer poll reporta las tres precondiciones sys.* ya en falla: {[e.signal_id for e in events]}",
        )
        check(all(e.transition == BiteTransition.FAULT for e in events), "todas marcadas como FAULT en el primer poll")
        check(len(bite.active_faults()) == len(events), f"active_faults() coincide tras el primer poll: {len(bite.active_faults())}")

        # segundo poll sin cambios -> ningun evento nuevo (no repetir la misma falla)
        events2 = await bite.poll(hal)
        check(events2 == [], f"poll sin cambios no genera eventos nuevos: {events2}")

        # arreglar una precondicion -> evento CLEARED, sale de active_faults
        await force(ws, "sys.line_parameters_ok_status", True)
        await asyncio.sleep(0.2)
        events3 = await bite.poll(hal)
        check(
            any(e.signal_id == "sys.line_parameters_ok_status" and e.transition == BiteTransition.CLEARED for e in events3),
            f"line_parameters_ok_status forzado a verdadero -> evento CLEARED: {events3}",
        )
        check(
            "sys.line_parameters_ok_status" not in {f.signal_id for f in bite.active_faults()},
            "line_parameters_ok_status ya no aparece en active_faults()",
        )

        # falla del transmisor (bad_when_true) -- fuerzo mps_fault_status
        await force(ws, "tx.mps_fault_status", True)
        await asyncio.sleep(0.2)
        events4 = await bite.poll(hal)
        check(
            any(e.signal_id == "tx.mps_fault_status" and e.transition == BiteTransition.FAULT for e in events4),
            f"tx.mps_fault_status forzado a verdadero -> evento FAULT: {events4}",
        )

        # filtrado por subsistema
        tx_history = bite.history(subsystem="tx")
        check(all(e.signal_id.startswith("tx.") for e in tx_history) and len(tx_history) > 0, f"history(subsystem='tx') filtra correctamente: {[e.signal_id for e in tx_history]}")
        sys_history = bite.history(subsystem="sys")
        check(all(e.signal_id.startswith("sys.") for e in sys_history) and len(sys_history) > 0, f"history(subsystem='sys') filtra correctamente: {[e.signal_id for e in sys_history]}")

        # limpieza
        await release(ws, "tx.mps_fault_status")
        for sig in ("sys.line_parameters_ok_status", "sys.environment_ok_status", "sys.standby_system_ok_status"):
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
    print("OK: BiteManager ejercitado contra instancia real de radar_emulator.")


if __name__ == "__main__":
    main()
