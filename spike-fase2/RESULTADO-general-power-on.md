# Resultado — spike rutina "general radar power-on"

Ejecutado 2026-08-19, `general_power_on_spike.py` vía `uv run` contra una instancia real de
`radar_emulator` (mismo override de puertos que Fase 1: Modbus `15020`, UDP `15100`, WS `18080`).

## PASA

- Precondiciones (`sys.line_parameters_ok_status`, `sys.environment_ok_status`,
  `sys.standby_system_ok_status`) en falso (default de la semilla) → `run_general_power_on`
  reporta `RoutineOutcome.FAILED` y dos de tres pasos con `ok=False`.
- Con precondiciones en falso, `sys.turn_on_radar_conmand` no se toca — verificado leyendo el
  coil antes y después de correr la rutina (`before == after == False`).
- Forzando las tres precondiciones a `True` vía el canal WS de control
  (`{"type":"force","signal":...,"value":true}`, mismo mecanismo que
  `spike-fase1/fault_injection_spike.py`): `run_general_power_on` reporta
  `RoutineOutcome.SUCCESS` con los 7 pasos (3 precondición + 1 comando + 3 post-pulso) en
  `ok=True`.
- Tras el pulso, `sys.turn_on_radar_conmand` vuelve a `False` — confirma que la rutina lo baja
  ella misma (flanco de subida, `radar_emulator` no tiene lógica propia para este DO).

## Qué NO prueba este spike

- Que la secuencia de precondiciones elegida sea la correcta para hardware real — ver
  PEND-RCP-06 (`docs/alcance/pendientes.md`), sin confirmar con el product expert ni con un
  manual del fabricante.
- Ningún criterio de éxito basado en una señal de confirmación directa — no existe en el catálogo
  RD100S; el spike solo puede confirmar que las precondiciones "no cambiaron para peor" después
  del pulso, no que el radar esté realmente encendido en un sentido más fuerte.
- Las otras cinco rutinas de control.

## Sigue pendiente

PEND-RCP-06 completo. Siguiente rutina candidata: transmisor (tiene `tx.fsm` real del lado del
emulador — primera vez que una rutina de Fase 2 sí tiene que sincronizar contra un estado
simulado con temporizadores, a diferencia de esta).
