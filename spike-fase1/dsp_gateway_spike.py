"""Spike Fase 1 -- conecta el stub de stream DSP (`spike-fase0/dsp_moment_stream_spike.py
--role dsp`) al gateway real (`src/adapters/gateway`, `adapters.dsp.MomentStreamReceiver`)
y verifica que `GET /api/status` refleje el estado resumido del stream.

Asume que el gateway ya esta corriendo (ver spike-fase1/README-gateway.md).
No manda el stub el mismo -- lo invoca como subproceso, igual que un DSP
real que se conecta cuando quiere empezar a transmitir un volumen.
"""

import argparse
import json
import subprocess
import sys
import time

FAILURES = []


def check(condition, msg):
    print(f"[{'OK   ' if condition else 'FALLA'}] {msg}")
    if not condition:
        FAILURES.append(msg)
    return condition


def get_status(base_http):
    proc = subprocess.run(["curl", "-s", f"{base_http}/api/status"], capture_output=True, text=True)
    return json.loads(proc.stdout)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--http-port", type=int, default=18000)
    ap.add_argument("--dsp-port", type=int, default=15551)
    args = ap.parse_args()

    base_http = f"http://127.0.0.1:{args.http_port}"

    before = get_status(base_http)
    check(before["dsp"]["connected"] is False, f"antes del emisor: dsp.connected=False ({before['dsp']})")

    proc = subprocess.run(
        [sys.executable, "spike-fase0/dsp_moment_stream_spike.py", "--role", "dsp", "--port", str(args.dsp_port)],
        capture_output=True, text=True,
    )
    check(proc.returncode == 0, f"stub --role dsp termino sin error: {proc.stdout.strip()}")

    time.sleep(0.3)
    after = get_status(base_http)
    dsp = after["dsp"]
    check(dsp["radials_received"] > before["dsp"]["radials_received"], f"radials_received crecio: {dsp}")
    check(dsp["last_radial_status"] == "end_of_volume", f"ultimo radial visto es end_of_volume: {dsp}")
    check(dsp["connected"] is False, "connected vuelve a False tras cerrar el emisor (fin de volumen)")

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FALLA(S):")
        for f in FAILURES:
            print(f" - {f}")
        sys.exit(1)
    print("OK: stream DSP conectado al gateway, estado resumido visible en /api/status.")


if __name__ == "__main__":
    main()
