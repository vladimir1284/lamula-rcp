# Resultado — spike inyección de fallos contra `SimulatedHAL`

Ejecutado 2026-08-19, `fault_injection_spike.py` contra la instancia local de `radar_emulator`
(la misma usada en el resto de Fase 1), disparando comandos `degrade` por su WS de control
(`ws://127.0.0.1:18080`, puerto `RD100S_HTTP_PORT` de esa instancia).

## PASA

- Baseline: `az_valid=True`, `el_valid=True`.
- `encoder_invalid` activo → `az_valid=False`, `el_valid=False`; desactivado → vuelven a `True`.
- `freeze` activo → dos lecturas separadas 150 ms tienen el mismo `az_deg`/`el_deg` con `seq`
  avanzando (972468 → 972482 en la corrida) — confirma que `EncoderReceiver` no confunde
  "paquetes siguen llegando" con "el HAL sigue viendo movimiento real".
- `silence` activo → pasado el `STALE_TIMEOUT_S` (100 ms) de `udp_encoder.py`,
  `read_antenna_position()` lanza `RuntimeError` en vez de devolver la última posición conocida
  en silencio; desactivado, el stream se recupera y la siguiente lectura responde normal.

## Qué NO prueba este spike

- Pérdida/ráfaga/duplicación/reordenamiento/jitter/salto de secuencia — ya cubiertas por
  `spike-fase0/udp_degradation_spike.py` a nivel de paquete; no cambian el valor expuesto por
  `SimulatedHAL`, así que no hay nada nuevo que verificar en el adaptador.
- Degradaciones del lado Modbus (`force`/`release`/`propagation` sobre una señal DI/AI/DO/AO vía
  el mismo canal WS de `radar_emulator`) — `read_digital`/`read_analog` no tienen un camino de
  código distinto para un valor forzado vs. uno automático; sería repetir el spike de Fase 0
  (`modbus_client_spike.py`) sin nada nuevo que ejercitar.
- El gateway (`src/adapters/gateway`) no participó en esta corrida — se probó `SimulatedHAL`
  directo para aislar el adaptador. El gateway ya reenvía lo que `read_antenna_position()`
  devuelva (`RESULTADO-gateway.md`), incluida la ausencia de `antenna` en `/api/status` cuando el
  stream está perdido.

## Sigue pendiente dentro de Fase 1

Shell MMI (scaffold Vue3+PrimeVue) es lo único que falta de los puntos de Fase 1 marcados en
`docs/implementacion/fases.md`.
