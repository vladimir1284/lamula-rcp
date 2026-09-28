#!/usr/bin/env bash
# Banco de integracion C0: RCP real <-> DSP real, con fuente sintetica.
#
# Es la primera fase del plan de integracion de los tres proyectos (P-13 del
# repo lamula-drx, PEND-RCP-13 de este). C0 levanta los binarios de verdad de
# este repo y del DSP y los hace hablar entre si por sockets de verdad. Lo
# unico que no es real es el origen de las muestras: en vez de una ZedBoard,
# el ejemplo `drx_faker` del repo del DSP conecta y emite rayos sinteticos por
# el cable DRx<->DSP. Sustituir ese proceso por la placa es la fase B; no hace
# falta cambiar nada de lo demas para ello.
#
# Lo que este banco SI prueba: framing y transporte de los dos enlaces, el
# camino descendente config + START desde el RCP, el ensamblado de radiales
# del DSP, la decodificacion de momentos del RCP y la reconexion de cada lado.
# Lo que NO prueba: nada de hardware -- ni cadencia, ni jitter, ni
# contrapresion reales, ni por supuesto JESD204B o el frontal analogico.
#
# Uso:
#   tools/hil/run-c0.sh [segundos]     (por defecto 15)
#
# Requiere el repo del DSP en ../lamula-dsp (mismo supuesto que el pin de
# contrato, contract/vendor/UPSTREAM.toml) y cargo en el PATH.

set -euo pipefail

DURATION="${1:-15}"
RCP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DSP_ROOT="${LAMULA_DSP_ROOT:-$(cd "$RCP_ROOT/../lamula-dsp" && pwd)}"

DRX_PORT="${DRX_PORT:-15500}"
DSP_TO_RCP_PORT="${DSP_TO_RCP_PORT:-15551}"
HTTP_PORT="${HTTP_PORT:-18000}"

PY="$RCP_ROOT/.venv/bin/python"
[ -x "$PY" ] || PY="python3"

LOG_DIR="$(mktemp -d)"
PIDS=()

cleanup() {
  for pid in "${PIDS[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup EXIT

echo "== C0: compilando el DSP =="
(cd "$DSP_ROOT" && cargo build --bin lamula-dsp --example drx_faker)

echo "== C0: arrancando el gateway del RCP (consumidor, escucha en :$DSP_TO_RCP_PORT) =="
(
  cd "$RCP_ROOT"
  PYTHONPATH="$RCP_ROOT/src:$RCP_ROOT" "$PY" -m adapters.gateway \
    --dsp-port "$DSP_TO_RCP_PORT" \
    --http-port "$HTTP_PORT" \
    --dsp-bench-profile "$RCP_ROOT/tools/hil/profile-c0.json"
) >"$LOG_DIR/rcp.log" 2>&1 &
PIDS+=($!)

# `LAMULA_DSP_SSI_COUNTS_PER_TURN` tiene que valer lo mismo que el
# `COUNTS_PER_TURN` del drx_faker (65536), o los grados que publique el DSP no
# se corresponderan con el azimut que emite la fuente.
echo "== C0: arrancando el DSP (escucha al DRx en :$DRX_PORT, conecta al RCP) =="
(
  cd "$DSP_ROOT"
  LAMULA_DSP_DRX_ADDR="127.0.0.1:$DRX_PORT" \
  LAMULA_DSP_RCP_ADDR="127.0.0.1:$DSP_TO_RCP_PORT" \
  LAMULA_DSP_FULL_SCALE_COUNTS=32767 \
  LAMULA_DSP_SSI_COUNTS_PER_TURN=65536 \
  LAMULA_DSP_SSI_ZERO_OFFSET_DEG=0.0 \
  LAMULA_DSP_DRX_NCO_FS_HZ=250000000.0 \
  LAMULA_DSP_DRX_NCO_WORD_BITS=32 \
  LAMULA_DSP_DRX_TRIGGER_FS_HZ=250000000.0 \
  LAMULA_DSP_TX_IF_HZ=60000000.0 \
  LAMULA_DSP_RX_IF_HZ=60000000.0 \
  LAMULA_DSP_AFC_TAU_S=2.0 \
  LAMULA_DSP_AFC_AMP_THRESHOLD=0.01 \
  LAMULA_DSP_SIMULATED_SOURCE=true \
  cargo run --quiet --bin lamula-dsp
) >"$LOG_DIR/dsp.log" 2>&1 &
PIDS+=($!)

echo "== C0: arrancando el DRx de mentira (productor, conecta al DSP) =="
(
  cd "$DSP_ROOT"
  cargo run --quiet --example drx_faker -- "127.0.0.1:$DRX_PORT"
) >"$LOG_DIR/drx.log" 2>&1 &
PIDS+=($!)

echo "== C0: corriendo $DURATION s; logs en $LOG_DIR =="
sleep "$DURATION"

status_json="$(curl -sf "http://127.0.0.1:$HTTP_PORT/api/status" || true)"
if [ -z "$status_json" ]; then
  echo "FALLO: el gateway del RCP no responde en :$HTTP_PORT"
  echo "--- rcp.log ---"; tail -30 "$LOG_DIR/rcp.log" || true
  exit 1
fi

radials="$("$PY" -c "import json,sys; print(json.loads(sys.argv[1])['dsp']['radials_received'])" "$status_json")"
connected="$("$PY" -c "import json,sys; print(json.loads(sys.argv[1])['dsp']['connected'])" "$status_json")"

echo
echo "DSP conectado al RCP: $connected"
echo "Radiales recibidos por el RCP: $radials"

if [ "$connected" != "True" ] || [ "$radials" -eq 0 ]; then
  echo "FALLO: la cadena no entrego radiales."
  echo "--- dsp.log (ultimas 30) ---"; tail -30 "$LOG_DIR/dsp.log" || true
  echo "--- drx.log (ultimas 10) ---"; tail -10 "$LOG_DIR/drx.log" || true
  echo "--- rcp.log (ultimas 20) ---"; tail -20 "$LOG_DIR/rcp.log" || true
  exit 1
fi

echo "OK: cadena drx_faker -> DSP -> RCP viva, con configuracion bajada desde el RCP."
