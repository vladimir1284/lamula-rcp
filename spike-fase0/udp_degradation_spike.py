"""Spike UDP fase 0 (2/2) — degradaciones en vivo desde radar_emulator.

A diferencia de udp_encoder_spike.py (parser contra paquetes sinteticos), esto
dispara cada degradacion de docs/interfaces/udp-encoder.md#6 via el canal
"degrade" del WebSocket del emulador y observa la reaccion real del receptor.

Diseno: un solo hilo lector corre sin parar durante toda la prueba y acumula
(t_llegada_monotonico, paquete) en una lista compartida. Cada fase de la
prueba solo anota el instante en que envio el comando "degrade" y recorta la
lista por rango de tiempo despues. Un drain_for() por fase (abrir/cerrar el
socket en ventanas) es fragil: dejaba backlog sin leer entre fases y
contaminaba la ventana siguiente. No es codigo de produccion.
"""

import argparse
import asyncio
import json
import socket
import struct
import threading
import time

import websockets

PKT_STRUCT = struct.Struct("<HBBIQiiiiHH")
MAGIC = 0x5244


def parse(datagram):
    if len(datagram) != 36:
        return None
    magic, version, _r0, seq, t_us, az, el, azr, elr, status, _r1 = PKT_STRUCT.unpack(datagram)
    if magic != MAGIC or version != 1:
        return None
    return dict(seq=seq, t_us=t_us, az=az, el=el, azr=azr, elr=elr, status=status)


def seq_delta(prev, curr):
    raw = (curr - prev) & 0xFFFFFFFF
    return raw - 0x100000000 if raw >= 0x80000000 else raw


class ContinuousReceiver:
    def __init__(self, sock):
        self.sock = sock
        self.log = []  # [(t_monotonic, pkt_dict)]
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def start(self):
        self.sock.settimeout(0.05)
        self._thread.start()

    def _loop(self):
        while not self._stop.is_set():
            try:
                datagram, _ = self.sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                return
            pkt = parse(datagram)
            if pkt is not None:
                self.log.append((time.monotonic(), pkt))

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=1)

    def window(self, t0, t1):
        return [(t, p) for t, p in self.log if t0 <= t < t1]


async def degrade(ws, kind, **kw):
    msg = {"type": "degrade", "actor": "spike-fase0", "kind": kind, **kw}
    await ws.send(json.dumps(msg))


async def phase(ws, rx, label, action, settle_s):
    """Ejecuta `action` (o None para solo observar baseline), espera settle_s,
    y devuelve (t_inicio, t_fin) para recortar rx.log despues."""
    print(f"\n== {label} ==")
    t0 = time.monotonic()
    if action is not None:
        await action()
    await asyncio.sleep(settle_s)
    t1 = time.monotonic()
    return t0, t1


async def run(ws_url, udp_port, window_s):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", udp_port))
    rx = ContinuousReceiver(sock)
    rx.start()

    async with websockets.connect(ws_url) as ws:
        await asyncio.wait_for(ws.recv(), timeout=2)  # mensaje "session" inicial

        t0, t1 = await phase(ws, rx, "baseline (sin degradacion)", None, window_s)
        report_baseline(rx.window(t0, t1), t1 - t0)

        t0, t1 = await phase(ws, rx, "perdida de paquetes (30%)", lambda: degrade(ws, "loss", value=0.3), window_s)
        await degrade(ws, "loss", value=0.0)
        report_loss(rx.window(t0, t1), expected_p=0.3)

        t0, t1 = await phase(ws, rx, "rafaga de corte (300 ms)", lambda: degrade(ws, "burst", value=300), 0.6)
        report_burst(rx.window(t0 - 0.05, t1))

        t0, t1 = await phase(ws, rx, "duplicacion (100%)", lambda: degrade(ws, "duplicate", value=1.0), window_s)
        await degrade(ws, "duplicate", value=0.0)
        report_duplicate(rx.window(t0, t1))

        t0, t1 = await phase(ws, rx, "congelacion (freeze)", lambda: degrade(ws, "freeze", active=True), window_s)
        await degrade(ws, "freeze", active=False)
        report_freeze(rx.window(t0, t1))

        t0, t1 = await phase(
            ws, rx, "encoder invalido (AZ_VALID/EL_VALID a cero)",
            lambda: degrade(ws, "encoder_invalid", active=True), window_s,
        )
        await degrade(ws, "encoder_invalid", active=False)
        report_encoder_invalid(rx.window(t0, t1))

        t_before0, t_before1 = time.monotonic() - 0.2, time.monotonic()
        await asyncio.sleep(0.2)
        t_jump = time.monotonic()
        await degrade(ws, "seq_jump", value=500)
        await asyncio.sleep(window_s)
        print("\n== salto de secuencia (delta +500) ==")
        report_seq_jump(rx.window(t_before0, t_before1), rx.window(t_jump, time.monotonic()))

        t0, t1 = await phase(ws, rx, "silencio total", lambda: degrade(ws, "silence", active=True), 0.5)
        await degrade(ws, "silence", active=False)
        report_silence(rx.window(t0, t1))

        t0, t1 = await phase(ws, rx, "estado final restaurado, muestra de verificacion", None, 0.3)
        report_baseline(rx.window(t0, t1), t1 - t0)

    rx.stop()
    sock.close()


def report_baseline(pkts, window_s):
    n = len(pkts)
    rate = n / window_s if window_s else 0
    print(f"{n} paquetes en {window_s:.1f}s (~{rate:.0f} Hz, nominal 100 Hz)")
    assert n > 0, "FALLA: no llego ningun paquete en baseline"


def report_loss(pkts, expected_p):
    seqs = [p["seq"] for _, p in pkts]
    gaps = sum(max(0, seq_delta(seqs[i - 1], seqs[i]) - 1) for i in range(1, len(seqs)))
    total_expected = gaps + len(seqs)
    observed_p = gaps / total_expected if total_expected else 0
    print(f"{len(pkts)} recibidos, {gaps} huecos de seq detectados -> perdida observada ~{observed_p:.0%} (pedida {expected_p:.0%})")
    assert gaps > 0, "FALLA: no se detecto ningun hueco de seq con 30% de perdida pedido"


def report_burst(pkts):
    if len(pkts) < 2:
        print("FALLA: muy pocos paquetes para medir el corte")
        return
    times = [t for t, _ in pkts]
    gaps = [times[i] - times[i - 1] for i in range(1, len(times))]
    max_gap = max(gaps)
    print(f"mayor hueco entre llegadas tras iniciar la rafaga: {max_gap * 1000:.0f} ms (pedido: ~300 ms de corte)")
    assert max_gap > 0.2, "FALLA: la rafaga no produjo un corte medible en el flujo"


def report_duplicate(pkts):
    seqs = [p["seq"] for _, p in pkts]
    dup_count = sum(1 for i in range(1, len(seqs)) if seqs[i] == seqs[i - 1])
    print(f"{len(pkts)} paquetes, {dup_count} con seq repetida consecutiva (duplicacion 100% pedida)")
    assert dup_count > 0, "FALLA: no se detecto ninguna duplicacion con probabilidad 1.0"


def report_freeze(pkts):
    if len(pkts) < 2:
        print("FALLA: muy pocos paquetes para evaluar congelacion")
        return
    azs = {p["az"] for _, p in pkts}
    els = {p["el"] for _, p in pkts}
    seqs = [p["seq"] for _, p in pkts]
    seq_advancing = all(seq_delta(seqs[i - 1], seqs[i]) >= 1 for i in range(1, len(seqs)))
    degraded = all(p["status"] & (1 << 7) for _, p in pkts)  # DEGRADED bit
    print(f"az constante={len(azs) == 1} el constante={len(els) == 1} seq avanzando={seq_advancing} DEGRADED=1 en todos={degraded}")
    assert len(azs) == 1 and len(els) == 1 and seq_advancing, (
        "FALLA: la congelacion no coincide con el contrato (posicion constante + seq avanzando)"
    )


def report_encoder_invalid(pkts):
    if not pkts:
        print("FALLA: no llego ningun paquete")
        return
    az_valid = [(p["status"] & 1) != 0 for _, p in pkts]
    el_valid = [(p["status"] & 2) != 0 for _, p in pkts]
    print(f"AZ_VALID=0 en {az_valid.count(False)}/{len(pkts)}, EL_VALID=0 en {el_valid.count(False)}/{len(pkts)}")
    assert not any(az_valid) and not any(el_valid), "FALLA: AZ_VALID/EL_VALID no bajaron a cero"


def report_seq_jump(before, after):
    if not before or not after:
        print("FALLA: faltan paquetes antes o despues del salto para medir el delta")
        return
    last_before = before[-1][1]["seq"]
    first_after = after[0][1]["seq"]
    delta = seq_delta(last_before, first_after)
    print(f"seq antes={last_before}, seq despues={first_after}, delta observado={delta} (pedido +500, mas el avance normal)")
    assert delta >= 490, f"FALLA: salto de secuencia no se aplico (delta {delta}, esperado >=490)"


def report_silence(pkts):
    print(f"{len(pkts)} paquetes recibidos durante 500 ms de silencio pedido")
    assert len(pkts) == 0, f"FALLA: llegaron {len(pkts)} paquetes durante el silencio"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ws", default="ws://127.0.0.1:18080")
    ap.add_argument("--udp-port", type=int, default=15100)
    ap.add_argument("--window", type=float, default=1.0)
    args = ap.parse_args()
    asyncio.run(run(args.ws, args.udp_port, args.window))
    print("\nOK: las ocho degradaciones de la seccion 6 del contrato se verificaron en vivo.")


if __name__ == "__main__":
    main()
