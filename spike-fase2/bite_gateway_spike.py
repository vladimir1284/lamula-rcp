"""Spike Fase 2 -- ejercita el cableado del System Status & BITE Manager al
gateway (`src/adapters/gateway`): `GET /api/status.active_bite_faults` y
`BiteEventMessage` por WS, contra una instancia real de `radar_emulator`.

No levanta el gateway el mismo -- asume que ya esta corriendo
(`python -m adapters.gateway ...`, ver README-gateway.md de spike-fase1),
mismo patron que `spike-fase1/gateway_ws_spike.py`. Fuerza
`tx.mps_fault_status` directo contra el canal de control WS de
`radar_emulator` (no contra el gateway -- el gateway no tiene endpoint
para eso, es deliberado, ver AGENTS.md/D-06).
"""

import argparse
import asyncio
import json
import sys

import websockets

FAILURES = []


def check(condition, msg):
    print(f"[{'OK   ' if condition else 'FALLA'}] {msg}")
    if not condition:
        FAILURES.append(msg)
    return condition


async def run(base_http, base_ws, emulator_ws_url):
    async with websockets.connect(f"{base_ws}/ws") as gw_ws:
        session_raw = await asyncio.wait_for(gw_ws.recv(), timeout=3)
        check(json.loads(session_raw)["type"] == "session", "primer mensaje WS del gateway es 'session'")

        async with websockets.connect(emulator_ws_url) as emu_ws:
            await asyncio.wait_for(emu_ws.recv(), timeout=2)  # "session" del emulador
            await emu_ws.send(json.dumps({"type": "release", "actor": "spike-fase2-bite-gateway", "signal": "tx.mps_fault_status"}))
            await asyncio.sleep(0.2)

            await emu_ws.send(json.dumps({"type": "force", "actor": "spike-fase2-bite-gateway", "signal": "tx.mps_fault_status", "value": True}))

            got_fault_event = False
            for _ in range(30):
                raw = await asyncio.wait_for(gw_ws.recv(), timeout=3)
                msg = json.loads(raw)
                if msg["type"] == "bite_event" and msg["signal_id"] == "tx.mps_fault_status" and msg["transition"] == "fault":
                    got_fault_event = True
                    break
            check(got_fault_event, "BiteEventMessage(fault) para tx.mps_fault_status llega por el WS del gateway")

            proc = await asyncio.create_subprocess_exec("curl", "-s", f"{base_http}/api/status", stdout=asyncio.subprocess.PIPE)
            out, _ = await proc.communicate()
            status = json.loads(out)
            check(
                any(f["signal_id"] == "tx.mps_fault_status" for f in status["active_bite_faults"]),
                f"GET /api/status.active_bite_faults incluye tx.mps_fault_status: {status['active_bite_faults']}",
            )

            await emu_ws.send(json.dumps({"type": "release", "actor": "spike-fase2-bite-gateway", "signal": "tx.mps_fault_status"}))

            got_cleared_event = False
            for _ in range(30):
                raw = await asyncio.wait_for(gw_ws.recv(), timeout=3)
                msg = json.loads(raw)
                if msg["type"] == "bite_event" and msg["signal_id"] == "tx.mps_fault_status" and msg["transition"] == "cleared":
                    got_cleared_event = True
                    break
            check(got_cleared_event, "BiteEventMessage(cleared) llega por el WS del gateway al liberar la señal forzada")

            proc = await asyncio.create_subprocess_exec("curl", "-s", f"{base_http}/api/status", stdout=asyncio.subprocess.PIPE)
            out, _ = await proc.communicate()
            status = json.loads(out)
            check(
                not any(f["signal_id"] == "tx.mps_fault_status" for f in status["active_bite_faults"]),
                "GET /api/status.active_bite_faults ya no incluye tx.mps_fault_status tras liberarla",
            )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--http-port", type=int, default=18000)
    ap.add_argument("--emulator-ws", default="ws://127.0.0.1:18080")
    args = ap.parse_args()

    base_http = f"http://127.0.0.1:{args.http_port}"
    base_ws = f"ws://127.0.0.1:{args.http_port}"
    asyncio.run(run(base_http, base_ws, args.emulator_ws))

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FALLA(S):")
        for f in FAILURES:
            print(f" - {f}")
        sys.exit(1)
    print("OK: BITE cableado al gateway (REST + WS) ejercitado end-to-end.")


if __name__ == "__main__":
    main()
