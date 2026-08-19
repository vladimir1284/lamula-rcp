"""Spike RDA<->ORPG fase 0 -- handshake minimo de login + Loopback Test (Msg 11/12).

Cubre el punto 3 de "Lo primero dentro de esta fase" en
docs/implementacion/fases.md, bloqueado por PEND-RCP-04 (sin ORPG real ni stub
CM_TCP). Este script ES el stub CM_TCP que faltaba: implementa ambos lados
(--role rda y --role orpg) para poder correr el handshake en dos procesos
locales cuando no hay ORPG real disponible. Contra un ORPG real, solo el lado
--role rda hace falta -- el rol --role orpg deja de usarse.

Formato de mensajes (CTM_Header de 12 bytes, MSG_Header de 16 bytes, payload
del Loopback Test de 104 bytes) tomado, byte a byte, del proyecto legacy
RDA_Backend_Py (2013, ingesta de radares cubanos al ORPG), que a su vez cita
como fuente el "Interface Control Document for the RDA/RPG (ICD 2620002F),
Open Build 10, 25 March 2008, WSR-88D ROC" -- el mismo ICD fijo que
AGENTS.md exige no reinterpretar. No es codigo de produccion; no reemplaza
congelar el contrato RCP<->ORPG como esquema (docs/implementacion/fases.md,
Fase 0 punto 4, sigue pospuesto).

Hallazgo a discutir con LAMULA ORPG antes de dar esto por definitivo: el
legacy RDA_Backend_Py, al recibir un mensaje entrante tipo 12, responde
reenviando su propio tipo 12 (RDA_TCPServer.process_Data) en vez de validar
el eco del Loopback Test que el ICD describe (RDA emite 11, RPG debe
devolver 12 con el mismo payload, RDA valida). Este spike implementa la
interpretacion del ICD (la logica-espejo del legacy no se copia), no la
resuelve -- es la ambiguedad a confirmar con el equipo, no localmente.
"""

import argparse
import calendar
import struct
import socket
import sys
import time

CTM_HEADER_FMT = ">3I"
CTM_HEADER_SIZE = 12  # bytes

MSG_HEADER_FMT = ">H2B2HI2H"
MSG_HEADER_SIZE = 16  # bytes
MSG_HEADER_SIZE_HW = 8  # halfwords

CTM_LOGIN_REQUEST = 0
CTM_LOGIN_ACK = 1
CTM_DATA = 2
CTM_DATA_ACK = 3
CTM_KEEPALIVE = 4

LOOPBACK_TEST_RDA_RPG = 11  # RDA -> RPG (legacy CODE_messages.py)
LOOPBACK_TEST_RPG_RDA = 12  # RPG -> RDA, eco esperado

LBT_SIZE_HW = 52  # halfwords, legacy Loopback_Test.py: message_size + 51 valores
LBT_PATTERN = list(range(LBT_SIZE_HW - 1))
LBT_PAYLOAD = struct.pack(">%iH" % LBT_SIZE_HW, LBT_SIZE_HW, *LBT_PATTERN)

# Placeholder de la fuente legacy (RDA_TCPServer.py: self.password="passwd").
# PEND: credencial real del ICD para el canal RDA<->ORPG, no inventar una propia.
PASSWORD = "passwd"

TIMEOUT_S = 10.0


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


def julian_date_msec():
    now = time.localtime()
    midnight = time.struct_time((now.tm_year, now.tm_mon, now.tm_mday, 0, 0, 0, 0, 0, -1))
    sec_of_day = time.mktime(now) - time.mktime(midnight)
    jd = calendar.timegm(now) // 86400
    ms_of_day = int(sec_of_day * 1000)
    return jd, ms_of_day


def send_ctm(sock, typ, par, body=b""):
    sock.sendall(struct.pack(CTM_HEADER_FMT, typ, par, len(body)) + body)


def recv_ctm(sock):
    header = recv_exact(sock, CTM_HEADER_SIZE)
    typ, par, length = struct.unpack(CTM_HEADER_FMT, header)
    body = recv_exact(sock, length) if length else b""
    return typ, par, body


def build_msg(msg_type, payload, seq, channel=0, n_segments=1, segment_n=1):
    jd, mo = julian_date_msec()
    size_hw = MSG_HEADER_SIZE_HW + len(payload) // 2
    header = struct.pack(MSG_HEADER_FMT, size_hw, channel, msg_type, seq, jd, mo, n_segments, segment_n)
    return header + payload


def parse_msg(stream):
    header = stream[:MSG_HEADER_SIZE]
    size_hw, channel, msg_type, seq, jd, mo, n_segments, segment_n = struct.unpack(MSG_HEADER_FMT, header)
    payload = stream[MSG_HEADER_SIZE:]
    return msg_type, payload


def run_rda(host, port):
    failures = []
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(1)
    print(f"RDA (stub): escuchando en {host}:{port}, esperando ORPG...")

    conn, addr = srv.accept()
    conn.settimeout(TIMEOUT_S)
    print(f"RDA (stub): conexion aceptada de {addr}")

    try:
        typ, par, body = recv_ctm(conn)
        check(typ == CTM_LOGIN_REQUEST, f"login request recibido (CTM.Typ={typ}, esperado {CTM_LOGIN_REQUEST})", failures)
        words = body.decode("ascii", errors="replace").split()
        password = words[-1][:-1] if words else ""
        if not check(password == PASSWORD, "password de login coincide con la esperada", failures):
            send_ctm(conn, CTM_LOGIN_ACK, 0, b"rejected")
            raise SystemExit(1)

        ack_body = f"{words[0]} {words[1]} connected".encode("ascii")
        send_ctm(conn, CTM_LOGIN_ACK, 0, ack_body)
        print("RDA (stub): login ack enviado")

        seq = 1
        msg11 = build_msg(LOOPBACK_TEST_RDA_RPG, LBT_PAYLOAD, seq)
        send_ctm(conn, CTM_DATA, 0, msg11)
        print("RDA (stub): Msg 11 (Loopback Test) enviado")

        typ, par, body = recv_ctm(conn)
        check(typ == CTM_DATA, f"respuesta recibida como CTM.Typ={typ} (esperado {CTM_DATA})", failures)
        msg_type, payload = parse_msg(body)
        check(msg_type == LOOPBACK_TEST_RPG_RDA, f"eco recibido es Msg {msg_type} (esperado {LOOPBACK_TEST_RPG_RDA})", failures)
        check(payload == LBT_PAYLOAD, "payload del eco identico al Msg 11 enviado", failures)
    finally:
        conn.close()
        srv.close()

    print()
    if failures:
        print(f"{len(failures)} FALLA(S):")
        for f in failures:
            print(f" - {f}")
        sys.exit(1)
    print("OK: handshake de login + Loopback Test (Msg 11/12) completo del lado RDA.")


def run_orpg(host, port):
    failures = []
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT_S)
    sock.connect((host, port))
    print(f"ORPG (stub CM_TCP): conectado a {host}:{port}")

    try:
        # legacy RDA_TCPServer.process_Login hace password = words[-1][:-1]:
        # espera un byte de relleno (no whitespace) pegado a la password, no
        # un separador -- si no, .split() se lo come y sobra un caracter real.
        login_body = f"RDA1 CHAN1 {PASSWORD}".encode("ascii") + b"\x00"
        send_ctm(sock, CTM_LOGIN_REQUEST, 0, login_body)

        typ, par, body = recv_ctm(sock)
        check(typ == CTM_LOGIN_ACK, f"login ack recibido (CTM.Typ={typ}, esperado {CTM_LOGIN_ACK})", failures)
        print("ORPG (stub CM_TCP):", body.decode("ascii", errors="replace"))

        typ, par, body = recv_ctm(sock)
        check(typ == CTM_DATA, f"Msg 11 recibido como CTM.Typ={typ} (esperado {CTM_DATA})", failures)
        msg_type, payload = parse_msg(body)
        check(msg_type == LOOPBACK_TEST_RDA_RPG, f"mensaje recibido es Msg {msg_type} (esperado {LOOPBACK_TEST_RDA_RPG})", failures)

        echo = build_msg(LOOPBACK_TEST_RPG_RDA, payload, seq=1)
        send_ctm(sock, CTM_DATA, 0, echo)
        print("ORPG (stub CM_TCP): Msg 12 (eco del Loopback Test) enviado")
    finally:
        sock.close()

    print()
    if failures:
        print(f"{len(failures)} FALLA(S):")
        for f in failures:
            print(f" - {f}")
        sys.exit(1)
    print("OK: handshake de login + Loopback Test (Msg 11/12) completo del lado ORPG (stub).")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--role", choices=["rda", "orpg"], required=True)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=10010)
    args = ap.parse_args()

    if args.role == "rda":
        run_rda(args.host, args.port)
    else:
        run_orpg(args.host, args.port)


if __name__ == "__main__":
    main()
