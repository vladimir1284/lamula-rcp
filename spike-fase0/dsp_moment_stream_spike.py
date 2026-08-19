"""Spike -- stub de stream de momentos RCP<->DSP (PEND-RCP-05).

No hay, al momento de escribir esto, implementacion de referencia ni
simulador del lado DSP equivalente a `radar_emulator` para el HAL. El
contrato ya esta congelado como esquema (`src/core/contracts/dsp.py`) pero
sin validar contra nada real. Este script es un stub propio -- no una
implementacion del formato real del proyecto DSP, que sigue sin acordarse --
para no bloquear la ingestion DSP/DRX de Fase 1 mientras tanto.

Trae ambos lados:

    python3 spike-fase0/dsp_moment_stream_spike.py --role rcp --port 15551 &
    python3 spike-fase0/dsp_moment_stream_spike.py --role dsp --port 15551

`--role dsp` genera un volumen sintetico (dos elevaciones, pocos radiales
cada una, momentos UZ y V) y lo manda por TCP como JSON de `RadialMoments`
(model_dump_json), cada mensaje precedido por un largo de 4 bytes
big-endian -- framing propio de este stub, no un protocolo acordado con DSP.
`--role rcp` lo recibe y valida cada radial contra el esquema Pydantic ya
congelado, mas el framing de volumen/elevacion (RadialStatus).

En cuanto exista una implementacion de referencia real del lado DSP, este
script se descarta o se adapta al formato real -- ver PEND-RCP-05 en
docs/alcance/pendientes.md.
"""

import argparse
import socket
import struct
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent / "src"))

from core.contracts.dsp import MomentId, MomentProfile, RadialMoments, RadialStatus

TIMEOUT_S = 10.0
ELEVATIONS_DEG = [0.5, 1.5]
RADIALS_PER_ELEVATION = 4
GATES = 8


def check(condition, msg, failures):
    status = "OK   " if condition else "FALLA"
    print(f"[{status}] {msg}")
    if not condition:
        failures.append(msg)
    return condition


def send_frame(sock, body: bytes):
    sock.sendall(struct.pack(">I", len(body)) + body)


def recv_exact(sock, size):
    buf = b""
    while len(buf) < size:
        chunk = sock.recv(size - len(buf))
        if not chunk:
            raise ConnectionError("conexion cerrada por el otro lado a mitad de mensaje")
        buf += chunk
    return buf


def recv_frame(sock):
    (length,) = struct.unpack(">I", recv_exact(sock, 4))
    return recv_exact(sock, length)


def synthetic_volume():
    t_us = 0
    for elev_n, elev_deg in enumerate(ELEVATIONS_DEG):
        for radial_n in range(RADIALS_PER_ELEVATION):
            if elev_n == 0 and radial_n == 0:
                status = RadialStatus.START_OF_VOLUME
            elif radial_n == 0:
                status = RadialStatus.START_OF_ELEVATION
            elif elev_n == len(ELEVATIONS_DEG) - 1 and radial_n == RADIALS_PER_ELEVATION - 1:
                status = RadialStatus.END_OF_VOLUME
            elif radial_n == RADIALS_PER_ELEVATION - 1:
                status = RadialStatus.END_OF_ELEVATION
            else:
                status = RadialStatus.INTERMEDIATE

            azimuth_deg = radial_n * (360.0 / RADIALS_PER_ELEVATION)
            t_us += 1000
            yield RadialMoments(
                azimuth_deg=azimuth_deg,
                elevation_deg=elev_deg,
                azimuth_resolution_deg=360.0 / RADIALS_PER_ELEVATION,
                elevation_number=elev_n,
                volume_number=0,
                radial_status=status,
                capture_t_us=t_us,
                moments={
                    MomentId.UZ: MomentProfile(
                        first_gate_range_m=0.0,
                        gate_spacing_m=250.0,
                        values=[10.0 + g for g in range(GATES)],
                    ),
                    MomentId.V: MomentProfile(
                        first_gate_range_m=0.0,
                        gate_spacing_m=250.0,
                        values=[0.5 * g for g in range(GATES)],
                    ),
                },
            )


def run_dsp(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT_S)
    sock.connect((host, port))
    print(f"DSP (stub): conectado a {host}:{port}")

    n = 0
    for radial in synthetic_volume():
        send_frame(sock, radial.model_dump_json().encode("utf-8"))
        n += 1
    sock.close()
    print(f"DSP (stub): {n} radiales enviados, conexion cerrada.")


def run_rcp(host, port):
    failures = []
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(1)
    print(f"RCP (consumidor): escuchando en {host}:{port}, esperando DSP...")

    conn, addr = srv.accept()
    conn.settimeout(TIMEOUT_S)
    print(f"RCP (consumidor): conexion aceptada de {addr}")

    radials = []
    try:
        while True:
            try:
                body = recv_frame(conn)
            except ConnectionError:
                break
            radial = RadialMoments.model_validate_json(body)
            radials.append(radial)
    finally:
        conn.close()
        srv.close()

    check(len(radials) > 0, "al menos un radial recibido", failures)
    check(radials[0].radial_status == RadialStatus.START_OF_VOLUME, "primer radial es start_of_volume", failures)
    check(radials[-1].radial_status == RadialStatus.END_OF_VOLUME, "ultimo radial es end_of_volume", failures)
    check(
        all(MomentId.UZ in r.moments and MomentId.V in r.moments for r in radials),
        "todos los radiales traen UZ y V",
        failures,
    )
    check(
        all(len(r.moments[MomentId.UZ].values) == GATES for r in radials),
        f"perfil UZ de cada radial tiene {GATES} gates",
        failures,
    )

    print()
    if failures:
        print(f"{len(failures)} FALLA(S):")
        for f in failures:
            print(f" - {f}")
        sys.exit(1)
    print(f"OK: {len(radials)} radiales recibidos y validados contra RadialMoments (stub, no DSP real).")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--role", choices=["rcp", "dsp"], required=True)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=15551)
    args = ap.parse_args()

    if args.role == "rcp":
        run_rcp(args.host, args.port)
    else:
        run_dsp(args.host, args.port)


if __name__ == "__main__":
    main()
