"""Emisor/consumidor sintetico del stream de momentos RCP<->DSP.

Nacio como stub con framing inventado en este repo, porque el proyecto DSP no
tenia contrato. Ya lo tiene: `DSP<->RCP v0.1`, vendorizado en `contract/vendor/`
y anclado por hash. Este script se porto a ese formato, asi que lo que ejercita
ahora es el contrato acordado y no una invencion local.

Lo que sigue sin ser: una implementacion de referencia del proyecto DSP. Es un
generador de volumenes sinteticos para no bloquear el trabajo de Fase 1/2 del
RCP. Valida formato y framing; NO valida cadencia, contrapresion con radiales de
3680 celdas a PRF alta, ni reconexion. Para eso hace falta el simulador de senal
del proyecto DSP, que no existe todavia.

    python3 spike-fase0/dsp_moment_stream_spike.py --role rcp --port 15551 &
    python3 spike-fase0/dsp_moment_stream_spike.py --role dsp --port 15551
"""

import argparse
import pathlib
import socket
import struct
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from adapters.dsp.wire import decode_moment_ray, frame, parse_frame_header  # noqa: E402
from contract.vendor import dsp_rcp_v0_1 as wire  # noqa: E402
from core.contracts.dsp import MomentId, RadialStatus  # noqa: E402

TIMEOUT_S = 10.0
ELEVATIONS_DEG = [0.5, 1.5]
RADIALS_PER_ELEVATION = 4
GATES = 8
AZIMUTH_WIDTH_DEG = 360.0 / RADIALS_PER_ELEVATION


def check(condition, msg, failures):
    status = "OK   " if condition else "FALLA"
    print(f"[{status}] {msg}")
    if not condition:
        failures.append(msg)
    return condition


def recv_exact(sock, size):
    buf = b""
    while len(buf) < size:
        chunk = sock.recv(size - len(buf))
        if not chunk:
            raise ConnectionError("conexion cerrada por el otro lado a mitad de mensaje")
        buf += chunk
    return buf


def recv_message(sock):
    """Cabecera comun de 12 B, luego `payload_len` bytes. Devuelve (tipo, cuerpo)."""
    header = parse_frame_header(recv_exact(sock, wire.Header.SIZE))
    return header.msg_type, recv_exact(sock, header.payload_len)


def synthetic_volume():
    """Volumen sintetico como cuerpos de `moment_ray` ya empaquetados."""
    base_utc_ns = int(time.time() * 1e9)
    base_mono_ns = time.monotonic_ns()

    for elev_n, elev_deg in enumerate(ELEVATIONS_DEG):
        for radial_n in range(RADIALS_PER_ELEVATION):
            flags = 0
            if radial_n == 0:
                flags |= wire.RayFlag.SWEEP_START
                if elev_n == 0:
                    flags |= wire.RayFlag.VOLUME_START
            if radial_n == RADIALS_PER_ELEVATION - 1:
                flags |= wire.RayFlag.SWEEP_END
                if elev_n == len(ELEVATIONS_DEG) - 1:
                    flags |= wire.RayFlag.VOLUME_END

            az_start = radial_n * AZIMUTH_WIDTH_DEG
            offset_ns = (elev_n * RADIALS_PER_ELEVATION + radial_n) * 1_000_000

            header = wire.MomentRay(
                seq=elev_n * RADIALS_PER_ELEVATION + radial_n,
                acq_time_utc_ns=base_utc_ns + offset_ns,
                acq_monotonic_ns=base_mono_ns + offset_ns,
                volume_seq=0,
                sweep_seq=elev_n,
                ray_index=radial_n,
                n_gates=GATES,
                n_pulses=64,
                bins_valid=GATES,
                n_moments=2,
                sweep_mode=wire.SweepMode.PPI,
                prf_mode=wire.DealiasMode.NONE,
                ray_flags=flags,
                pad0=0,
                az_start_deg=az_start,
                az_end_deg=az_start + AZIMUTH_WIDTH_DEG,
                el_start_deg=elev_deg,
                el_end_deg=elev_deg,
                fixed_angle_deg=elev_deg,
                start_range_m=125.0,
                gate_spacing_m=250.0,
                prf_hz=600.0,
                nyquist_velocity=8.3,
                unambiguous_range_m=249_827.0,
                noise_floor_dbm=-113.0,
                radar_constant_db=68.5,
            )

            payload = b""
            for kind, values in (
                (wire.MomentKind.UZ, [10.0 + g for g in range(GATES)]),
                (wire.MomentKind.V, [0.5 * g for g in range(GATES)]),
            ):
                payload += wire.MomentField(
                    kind=kind,
                    data_type=wire.DataType.F32,
                    flags=0,
                    pad0=0,
                    n_gates=GATES,
                    scale=1.0,
                    offset=0.0,
                ).pack()
                payload += struct.pack(f"<{GATES}f", *values)

            yield header.pack() + payload


def run_dsp(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT_S)
    sock.connect((host, port))
    print(f"DSP (sintetico): conectado a {host}:{port}")

    n = 0
    for body in synthetic_volume():
        sock.sendall(frame(wire.MsgType.MOMENT_RAY, body))
        n += 1

    # Un status por el mismo enlace: el consumidor tiene que tolerarlo.
    status = wire.Status(uptime_s=1, phase=wire.Phase.RUNNING)
    sock.sendall(frame(wire.MsgType.STATUS, status.pack()))
    sock.close()
    print(f"DSP (sintetico): {n} radiales + 1 status enviados, conexion cerrada.")


def run_rcp(host, port):
    failures = []
    expected = len(ELEVATIONS_DEG) * RADIALS_PER_ELEVATION

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.settimeout(TIMEOUT_S)
    srv.bind((host, port))
    srv.listen(1)
    print(f"RCP (consumidor): escuchando en {host}:{port}, esperando DSP...")

    conn, addr = srv.accept()
    conn.settimeout(TIMEOUT_S)
    print(f"RCP (consumidor): conexion aceptada de {addr}")

    radials, others = [], 0
    try:
        while True:
            msg_type, body = recv_message(conn)
            if msg_type == wire.MsgType.MOMENT_RAY:
                radials.append(decode_moment_ray(body))
            else:
                others += 1
    except (ConnectionError, TimeoutError, socket.timeout):
        pass
    finally:
        conn.close()
        srv.close()

    print()
    check(len(radials) == expected, f"{expected} radiales decodificados", failures)
    check(others == 1, "el status por el mismo enlace no rompe el consumidor", failures)
    if radials:
        check(
            radials[0].radial_status is RadialStatus.START_OF_VOLUME,
            "el primer radial abre volumen",
            failures,
        )
        check(
            radials[-1].radial_status is RadialStatus.END_OF_VOLUME,
            "el ultimo radial cierra volumen",
            failures,
        )
        check(
            all(
                set(r.moments) == {MomentId.UZ, MomentId.V}
                and len(r.moments[MomentId.UZ].values) == GATES
                for r in radials
            ),
            f"todos traen UZ y V con {GATES} celdas",
            failures,
        )
        check(
            all(r.acq_time_utc.tzinfo is not None for r in radials),
            "la hora de pared llega con zona, medida en el emisor",
            failures,
        )
        check(
            all(
                b.acq_monotonic_us > a.acq_monotonic_us
                for a, b in zip(radials, radials[1:])
            ),
            "el reloj monotono crece radial a radial",
            failures,
        )

    print()
    if failures:
        print(f"{len(failures)} FALLA(S):")
        for f in failures:
            print(f" - {f}")
        return 1
    print("OK: formato de cable DSP<->RCP v0.1 ejercitado de extremo a extremo.")
    print("    Emisor sintetico de este repo, NO una implementacion de referencia del DSP.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--role", choices=["rcp", "dsp"], required=True)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=15551)
    args = ap.parse_args()

    if args.role == "dsp":
        run_dsp(args.host, args.port)
        return 0
    return run_rcp(args.host, args.port)


if __name__ == "__main__":
    raise SystemExit(main())
