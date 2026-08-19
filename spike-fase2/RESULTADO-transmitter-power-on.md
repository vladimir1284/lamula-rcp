# Resultado — spike rutina "encendido del transmisor"

Ejecutado 2026-08-19, `transmitter_power_on_spike.py --full-warmup` vía `uv run` contra una
instancia real de `radar_emulator` (mismo override de puertos que el resto de Fase 1/2: Modbus
`15020`, UDP `15100`, WS `18080` — proceso persistente durante toda la sesión).

## PASA

- Reset a `OFF` forzando `tx.turn_off_tx_command` antes de empezar — necesario: el `tx.fsm` venía
  de un estado previo dentro de la propia sesión (`radar_emulator` es un proceso persistente, no
  se reinicia entre spikes).
- Los seis interlocks en falso (default) → `FAILED` sin escribir `tx.turn_on_tx_command`.
- Interlocks forzados a verdadero, `warmup_timeout_s=2.0` (« 180s de caldeo real) → `FAILED` por
  timeout, con `tx.tx_on_status` ya confirmado en `True` (entró a `STARTING` correctamente antes
  de agotar el timeout corto).
- `tx.turn_off_tx_command` forzado a mitad del caldeo (tarea `asyncio` + `force` concurrente) →
  `INTERRUPTED`, detectado vía la caída de `tx.tx_on_status`.
- **Corrida completa con `warmup_timeout_s=200.0`:** `run_transmitter_power_on` esperó el caldeo
  real (~180 s, `after_ms: 180000` de la semilla) y devolvió `SUCCESS` con `tx.ready_status=True`
  confirmado por lectura directa — el temporizador real del simulador coincide con el marcador de
  posición documentado.

8/8 verificaciones en `OK`. La única falla de la primera corrida (sin reset a `OFF`) fue del
spike, no de la rutina: el `tx.fsm` ya estaba en `READY` desde antes de que este spike corriera
por primera vez en la sesión, así que las aserciones de "recién arrancando" no aplicaban —
corregido agregando el reset explícito al inicio.

## Qué NO prueba este spike

- Que las seis señales usadas como precondición (ni su chequeo antes de `STARTING`, que el
  `tx.fsm` real no exige) sean el criterio correcto para hardware real — sin confirmar con el
  product expert.
- `tx.turn_on_blowers_command`/`turn_on_fps_command`/`turn_on_mps_command` — no los usa esta
  rutina, ver README.
- Subir alta tensión o habilitar salida (`HV_ON`/`RADIATING`) — fuera del alcance elegido para
  esta rutina.
- La caída de un interlock durante `HV_ON`/`RADIATING` (`tx.interlocks_ok` → `READY`) — no aplica,
  esta rutina no llega a esos estados.

## Sigue pendiente

PEND-RCP-07 (extendido): confirmar con el product expert si estas seis señales son la precondición
correcta antes de calentar el transmisor (el simulador no las exige para esta transición, es una
elección conservadora del RCP), el tiempo real de caldeo del magnetrón, y si "encendido del
transmisor" debe incluir subir HV/radiar o quedarse en "listo" como se implementó.
