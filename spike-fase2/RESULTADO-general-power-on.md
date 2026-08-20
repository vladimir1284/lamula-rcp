# Resultado — spike rutina "general radar power-on"

Ejecutado 2026-08-19, `general_power_on_spike.py` vía `uv run` contra una instancia real de
`radar_emulator` (mismo override de puertos que Fase 1: Modbus `15020`, UDP `15100`, WS `18080`).

## PASA (2026-08-19, versión pre-`sys.fsm`)

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

## Qué NO probaba esta primera corrida

- Que la secuencia de precondiciones elegida fuera la correcta para hardware real — ver
  PEND-RCP-06 (`docs/alcance/pendientes.md`), sin confirmar con el product expert ni con un
  manual del fabricante.
- Ningún criterio de éxito basado en una señal de confirmación directa — no existía en el
  catálogo RD100S de entonces; el spike solo podía confirmar que las precondiciones "no
  cambiaron para peor" después del pulso.
- Las otras cinco rutinas de control.

## Re-ejecutado 2026-08-20, tras el upgrade al procedimiento confirmado por el experto

`radar_emulator` ya trae `sys.fsm` real (`config/rd100s.seed.json`, 119 señales, sube de 116) y
`general_power_on.py` ya implementa las cuatro precondiciones + confirmación directa post-pulso +
chequeo de Cabinet Fans (ver PEND-RCP-06 en `docs/alcance/pendientes.md`). Corrido contra una
instancia fresca de `radar_emulator` (mismos puertos, config derivada regenerada desde la semilla
actual — la derivada vieja estaba desfasada, sin `sys.fsm`).

**Todo en verde:**

- Precondiciones en falso (`sys.standby_system_ok_status`, `sys.line_parameters_ok_status`,
  `sys.environment_ok_status`, `sys.remote_mode_ok_status` — las cuatro, no tres) →
  `RoutineOutcome.FAILED`, comando no tocado.
- Las cuatro en verdadero → `RoutineOutcome.SUCCESS`, 11 pasos en `ok=True` (4 precondición + 1
  comando + `system_on_ok_status`/`mdb_fan_ok_status` + 4 Cabinet Fans reales, no la señal virtual
  `sys.cabinet_fans_ok`), comando vuelve a `False` tras el pulso (flanco, no nivel).
- Liberando un solo Cabinet Fan tras el encendido → `RoutineOutcome.INTERRUPTED` (no `FAILED`):
  el radar quedó encendido pero con una falla de post-chequeo, mismo patrón que la caída de
  interlock en caliente de `transmitter_power_on.py`.

## Qué NO prueba este spike

- Las dos asunciones de mapeo de "Cabinet Fan" en `radar_emulator` (PEND-27/PEND-28 de ese
  proyecto) — el spike confirma que las señales responden como se espera, no que el mapeo sea
  correcto contra hardware real.
- Las otras cinco rutinas de control (ver sus propios `RESULTADO-*.md`).

## Sigue pendiente

PEND-RCP-06 queda resuelto del lado de código+simulador. Sigue abierto PEND-RCP-07 (rutinas 2–6,
`docs/operacion/rutinas-control.md` sin revisión completa del product expert).
