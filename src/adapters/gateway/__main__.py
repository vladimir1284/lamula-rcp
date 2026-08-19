"""Entrypoint del gateway: `python -m adapters.gateway [opciones]`.

Levanta `SimulatedHAL` contra una instancia de `radar_emulator` y sirve el
gateway FastAPI (REST + WS) sobre ella. Ver spike-fase1/README-hal-sim.md
para como levantar el emulador con puertos no privilegiados.
"""

from __future__ import annotations

import argparse

import uvicorn

from adapters.hal_sim import SimulatedHAL

from .app import create_app


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--modbus-host", default="127.0.0.1")
    ap.add_argument("--modbus-port", type=int, default=15020)
    ap.add_argument("--udp-bind-host", default="0.0.0.0")
    ap.add_argument("--udp-port", type=int, default=15100)
    ap.add_argument("--http-host", default="0.0.0.0")
    ap.add_argument("--http-port", type=int, default=8000)
    args = ap.parse_args()

    hal = SimulatedHAL(
        modbus_host=args.modbus_host,
        modbus_port=args.modbus_port,
        udp_bind_host=args.udp_bind_host,
        udp_port=args.udp_port,
    )
    app = create_app(hal)
    uvicorn.run(app, host=args.http_host, port=args.http_port)


if __name__ == "__main__":
    main()
