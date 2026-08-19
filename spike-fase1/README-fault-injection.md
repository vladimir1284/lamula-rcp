# Spike Fase 1 — inyección de fallos contra `SimulatedHAL`

Cuarto punto de "Lo primero dentro de esta fase": `HAL + adaptador simulador (HW + stream
DSP/DRX + inyección de fallos)`. `radar_emulator` ya trae su propio canal de control WS
(`docs/interfaces/websocket.md` de ese repo) con comandos `degrade` para forzar cada una de las
ocho degradaciones del contrato `RD100S-ENC-UDP v1` (§6). Este spike los dispara en vivo y
verifica que `src/adapters/hal_sim/SimulatedHAL` los refleje correctamente — no un test contra un
socket ad-hoc, sino contra el adaptador de producción.

Solo cubre las tres degradaciones observables directamente en
`SimulatedHAL.read_antenna_position()`:

- **`encoder_invalid`** → `az_valid`/`el_valid` caen a `False`.
- **`freeze`** → posición constante entre dos lecturas mientras `seq` sigue avanzando.
- **`silence`** → `read_antenna_position()` lanza `RuntimeError` pasado el `STALE_TIMEOUT_S`
  (100 ms) del receptor (`udp_encoder.py`), y se recupera solo al reactivarse el stream.

Pérdida/ráfaga/duplicación/reordenamiento/jitter/salto de secuencia son ruido a nivel de paquete
que `EncoderReceiver` ya absorbe sin cambiar el valor expuesto — ya están cubiertas por
`spike-fase0/udp_degradation_spike.py` contra el parser crudo; no hace falta repetirlas aquí.

## Cómo correrlo

Con `radar_emulator` corriendo (mismo override de puertos que el resto de Fase 1):

```bash
uv run python spike-fase1/fault_injection_spike.py --ws ws://127.0.0.1:18080 --modbus-port 15020 --udp-port 15100
```

Ver `RESULTADO-fault-injection.md`.
