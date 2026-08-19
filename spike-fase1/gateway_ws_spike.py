"""Spike Fase 1 -- ejercita el gateway RCP<->MMI (`src/adapters/gateway`)
end-to-end: REST + WS + broadcast de eventos, contra un `SimulatedHAL`
conectado a una instancia real de `radar_emulator`.

No levanta el gateway el mismo -- asume que ya esta corriendo
(`python -m adapters.gateway ...`, ver README-gateway.md) para poder
probar WS y REST como dos clientes independientes, igual que un MMI real
haria.
"""

import argparse
import asyncio
import json
import subprocess
import sys

import websockets

FAILURES = []


def check(condition, msg):
    print(f"[{'OK   ' if condition else 'FALLA'}] {msg}")
    if not condition:
        FAILURES.append(msg)
    return condition


async def run(base_http, base_ws):
    async with websockets.connect(f"{base_ws}/ws") as ws:
        session_raw = await asyncio.wait_for(ws.recv(), timeout=3)
        session = json.loads(session_raw)
        check(session["type"] == "session", f"primer mensaje WS es 'session': {session}")

        seen_antenna = False
        for _ in range(5):
            raw = await asyncio.wait_for(ws.recv(), timeout=3)
            msg = json.loads(raw)
            if msg["type"] == "antenna":
                seen_antenna = True
                pos = msg["position"]
                check(0.0 <= pos["az_deg"] < 360.0, f"antenna az_deg={pos['az_deg']:.3f} el_deg={pos['el_deg']:.3f}")
                break
        check(seen_antenna, "recibido al menos un AntennaMessage por WS tras el session")

        # dispara un cambio de control desde otro cliente (REST) mientras seguimos escuchando el WS
        proc = await asyncio.create_subprocess_exec(
            "curl", "-s", "-X", "POST", f"{base_http}/api/control",
            "-H", "Content-Type: application/json",
            "-d", '{"mode":"active","actor":"spike-gateway"}',
            stdout=subprocess.DEVNULL,
        )
        rc = await proc.wait()
        check(rc == 0, "POST /api/control respondio sin error de transporte")

        got_event = False
        for _ in range(20):
            raw = await asyncio.wait_for(ws.recv(), timeout=2)
            msg = json.loads(raw)
            if msg["type"] == "event" and msg["kind"] == "control_mode_changed":
                got_event = True
                check(msg["actor"] == "spike-gateway", f"OperatorEventMessage.actor coincide: {msg}")
                break
        check(got_event, "OperatorEventMessage llega por WS tras el POST /api/control de otro cliente")

    proc = subprocess.run(["curl", "-s", f"{base_http}/api/status"], capture_output=True, text=True)
    status = json.loads(proc.stdout)
    check(status["hal_connected"] is True, f"GET /api/status: hal_connected={status['hal_connected']}")
    check(status["control"]["mode"] == "active", f"GET /api/status: control.mode refleja el cambio anterior: {status['control']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--http-port", type=int, default=18000)
    args = ap.parse_args()

    base_http = f"http://127.0.0.1:{args.http_port}"
    base_ws = f"ws://127.0.0.1:{args.http_port}"
    asyncio.run(run(base_http, base_ws))

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FALLA(S):")
        for f in FAILURES:
            print(f" - {f}")
        sys.exit(1)
    print("OK: gateway REST+WS+broadcast de eventos ejercitado end-to-end.")


if __name__ == "__main__":
    main()
