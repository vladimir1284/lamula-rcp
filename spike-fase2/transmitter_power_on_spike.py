"""Spike Fase 2 -- ejercita `core.control_routines.run_transmitter_power_on`
(Rutina 2, encendido del transmisor) contra una instancia real de
`radar_emulator`, forzando los seis interlocks y `tx.turn_off_tx_command`
via el canal de control WS -- mismo patron que el resto de los spikes de
Fase 1/2.

Incluye una corrida completa esperando el caldeo real del magnetron
(`after_ms: 180000` en `tx.fsm` de la semilla) para confirmar que
`run_transmitter_power_on` detecta `tx.ready_status` correctamente contra
el temporizador real del simulador, no solo contra un timeout corto -- esta
corrida sola tarda poco mas de tres minutos.
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
from core.control_routines import run_transmitter_power_on
from core.control_routines.transmitter_power_on import COMMAND_ON, INTERLOCK_SIGNALS, READY_STATUS, TX_ON_STATUS

FAILURES = []


def check(condition, msg):
    print(f"[{'OK   ' if condition else 'FALLA'}] {msg}")
    if not condition:
        FAILURES.append(msg)
    return condition


async def force(ws, signal, value):
    await ws.send(json.dumps({"type": "force", "actor": "spike-fase2-transmitter-power-on", "signal": signal, "value": value}))


async def release(ws, signal):
    await ws.send(json.dumps({"type": "release", "actor": "spike-fase2-transmitter-power-on", "signal": signal}))


async def run(ws_url, modbus_port, udp_port, full_warmup):
    hal = SimulatedHAL(modbus_host="127.0.0.1", modbus_port=modbus_port, udp_bind_host="0.0.0.0", udp_port=udp_port)
    await hal.connect()

    async with websockets.connect(ws_url) as ws:
        await asyncio.wait_for(ws.recv(), timeout=2)  # "session" inicial

        for signal_id in INTERLOCK_SIGNALS:
            await release(ws, signal_id)
        await release(ws, "tx.turn_off_tx_command")
        await asyncio.sleep(0.2)

        # radar_emulator es persistente durante toda la sesion -- tx.fsm puede venir de
        # antes de este spike en cualquier estado (incluso ya READY). Forzar apagado para
        # arrancar siempre desde OFF, sea el estado previo el que sea.
        await force(ws, "tx.turn_off_tx_command", True)
        await asyncio.sleep(0.3)
        reset_check = await hal.read_digital(TX_ON_STATUS)
        check(reset_check.value is False, f"reset a OFF antes de empezar: tx_on_status={reset_check.value}")
        await release(ws, "tx.turn_off_tx_command")
        await asyncio.sleep(0.2)

        # --- interlocks en falso (default) -> falla sin escribir nada ---------
        before = await hal.read_digital(COMMAND_ON)
        result = await run_transmitter_power_on(hal, warmup_timeout_s=2.0)
        after = await hal.read_digital(COMMAND_ON)
        check(result.outcome == RoutineOutcome.FAILED, f"interlocks en falso -> outcome={result.outcome}")
        check(before.value == after.value, f"comando {COMMAND_ON} no se toco (before={before.value} after={after.value})")

        # --- interlocks en verdadero, timeout corto -> arranca pero no llega a listo ---
        for signal_id in INTERLOCK_SIGNALS:
            await force(ws, signal_id, True)
        await asyncio.sleep(0.2)

        result = await run_transmitter_power_on(hal, warmup_timeout_s=2.0)
        check(result.outcome == RoutineOutcome.FAILED, f"timeout corto (2s < 180s de caldeo real) -> outcome={result.outcome}")
        check(
            any(s.signal_id == TX_ON_STATUS and s.ok for s in result.steps),
            "tx_on_status confirmado (entro a STARTING) antes de agotar el timeout corto",
        )

        # --- interrupcion a mitad de camino: turn_off_tx_command forzado durante el caldeo ---
        task = asyncio.create_task(run_transmitter_power_on(hal, warmup_timeout_s=10.0))
        await asyncio.sleep(0.3)
        await force(ws, "tx.turn_off_tx_command", True)
        result = await task
        check(result.outcome == RoutineOutcome.INTERRUPTED, f"turn_off_tx_command forzado durante el caldeo -> outcome={result.outcome}")
        await release(ws, "tx.turn_off_tx_command")
        await asyncio.sleep(0.3)

        if full_warmup:
            # --- corrida completa: esperar el caldeo real (~180 s) --------------
            result = await run_transmitter_power_on(hal, warmup_timeout_s=200.0)
            check(result.outcome == RoutineOutcome.SUCCESS, f"caldeo completo real -> outcome={result.outcome}")
            ready = await hal.read_digital(READY_STATUS)
            check(ready.value is True, f"tx.ready_status tras la corrida completa: value={ready.value}")
        else:
            print("[SKIP ] corrida completa de caldeo real (~180s) -- pasar --full-warmup para incluirla")

        try:
            for signal_id in INTERLOCK_SIGNALS:
                await release(ws, signal_id)
            await release(ws, "tx.turn_off_tx_command")
        except websockets.exceptions.ConnectionClosed:
            # el keepalive del server puede vencer tras los ~180s de espera de --full-warmup;
            # la limpieza de senales forzadas es best-effort, no afecta lo ya verificado arriba.
            print("[WARN ] conexion WS cerrada por keepalive antes de poder liberar senales forzadas")

    await hal.disconnect()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ws", default="ws://127.0.0.1:18080")
    ap.add_argument("--modbus-port", type=int, default=15020)
    ap.add_argument("--udp-port", type=int, default=15100)
    ap.add_argument("--full-warmup", action="store_true", help="incluir la corrida completa (~180s de espera real)")
    args = ap.parse_args()

    asyncio.run(run(args.ws, args.modbus_port, args.udp_port, args.full_warmup))

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FALLA(S):")
        for f in FAILURES:
            print(f" - {f}")
        sys.exit(1)
    print("OK: run_transmitter_power_on ejercitado contra instancia real de radar_emulator.")


if __name__ == "__main__":
    main()
