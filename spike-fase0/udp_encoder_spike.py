"""Spike UDP fase 0 — receptor RD100S-ENC-UDP v1 contra radar_emulator.

Parsea el paquete de 36 octetos, sigue la envolvente de `seq` (mod 2^32),
detecta reinicio del emisor (`seq` y `t_us` retrocediendo juntos) y declara
perdida de stream por timeout. No es codigo de produccion.

Formato (docs/interfaces/udp-encoder.md de radar_emulator), little-endian:
u16 magic | u8 version | u8 reserved0 | u32 seq | u64 t_us |
i32 az_mdeg | i32 el_mdeg | i32 az_rate | i32 el_rate | u16 status | u16 reserved1
"""

import argparse
import socket
import struct
import time

MAGIC = 0x5244
VERSION = 0x01
PKT_STRUCT = struct.Struct("<HBBIQiiiiHH")
assert PKT_STRUCT.size == 36

STATUS_BITS = {
    0: "AZ_VALID",
    1: "EL_VALID",
    2: "AZ_REF_OK",
    3: "EL_REF_OK",
    4: "AZ_FAULT",
    5: "EL_FAULT",
    6: "SIM",
    7: "DEGRADED",
}

TIMEOUT_S = 0.1  # 100 ms, diez periodos nominales a 100 Hz (recomendacion del contrato)


def decode_status(word):
    return sorted(name for bit, name in STATUS_BITS.items() if word & (1 << bit))


def parse(datagram):
    if len(datagram) != 36:
        return None
    fields = PKT_STRUCT.unpack(datagram)
    magic, version, _reserved0, seq, t_us, az_mdeg, el_mdeg, az_rate, el_rate, status, _r1 = fields
    if magic != MAGIC or version != VERSION:
        return None
    return dict(
        seq=seq, t_us=t_us, az_mdeg=az_mdeg, el_mdeg=el_mdeg,
        az_rate=az_rate, el_rate=el_rate, status=status,
    )


def seq_delta(prev, curr):
    """Delta con envolvente en 2^32, con signo (negativo = retroceso)."""
    raw = (curr - prev) & 0xFFFFFFFF
    if raw >= 0x80000000:
        raw -= 0x100000000
    return raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bind", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=15100)
    ap.add_argument("--count", type=int, default=200, help="paquetes validos a recibir antes de reportar")
    args = ap.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.bind, args.port))
    sock.settimeout(TIMEOUT_S)

    print(f"Escuchando UDP en {args.bind}:{args.port}, timeout de perdida de stream = {TIMEOUT_S * 1000:.0f} ms")

    prev = None
    seen = 0
    gaps = 0
    dup_or_reorder = 0
    resets = 0
    malformed = 0
    timeouts = 0
    last_status = None

    t_start = time.monotonic()
    while seen < args.count and (time.monotonic() - t_start) < 20:
        try:
            datagram, _addr = sock.recvfrom(4096)
        except socket.timeout:
            timeouts += 1
            print(f"[timeout] sin datagrama en {TIMEOUT_S * 1000:.0f} ms -> stream declarado perdido")
            continue

        pkt = parse(datagram)
        if pkt is None:
            malformed += 1
            continue  # descarte silencioso, tal como exige el contrato (magic/version/longitud)

        seen += 1

        if pkt["status"] != last_status:
            print(f"status = {pkt['status']:#06x} -> {decode_status(pkt['status'])}")
            last_status = pkt["status"]

        if prev is not None:
            d_seq = seq_delta(prev["seq"], pkt["seq"])
            d_t = pkt["t_us"] - prev["t_us"]  # sin envolvente: u64, no se espera que desborde en una prueba corta

            if d_seq < 0 and d_t < 0:
                resets += 1
                print(f"[reset] seq {prev['seq']} -> {pkt['seq']}, t_us {prev['t_us']} -> {pkt['t_us']}: reinicio del emisor")
            elif d_seq == 0:
                dup_or_reorder += 1
            elif d_seq < 0:
                dup_or_reorder += 1
            elif d_seq > 1:
                gaps += d_seq - 1

        prev = pkt

        if seen <= 3 or seen % 50 == 0:
            print(
                f"seq={pkt['seq']:>10} t_us={pkt['t_us']:>14} "
                f"az={pkt['az_mdeg']/1000:.3f}deg el={pkt['el_mdeg']/1000:.3f}deg "
                f"az_rate={pkt['az_rate']} el_rate={pkt['el_rate']}"
            )

    sock.close()

    print()
    print(f"OK: {seen} paquetes validos, {malformed} descartados (magic/version/longitud), "
          f"{gaps} huecos de seq, {dup_or_reorder} dup/reorden, {resets} reinicio(s) detectado(s), "
          f"{timeouts} timeout(s) de {TIMEOUT_S * 1000:.0f} ms sin datagrama.")

    if seen == 0:
        raise SystemExit("FALLA: no se recibio ningun paquete valido")


if __name__ == "__main__":
    main()
