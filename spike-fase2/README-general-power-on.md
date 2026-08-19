# Spike Fase 2 — rutina de control "general radar power-on"

Primera de las seis rutinas de control del plan (§4.3, §8.2 Fase 2). Se eligió como punto de
entrada de Fase 2 porque `sys.turn_on_radar_conmand` no tiene ningún bloque de lógica en
`radar_emulator` (a diferencia de `tx.fsm`, la máquina de estados completa del transmisor) — deja
sentar el patrón de `src/core/control_routines/` sin arrastrar sincronización contra un FSM del
otro lado.

## Qué implementa `core/control_routines/general_power_on.py`

1. Lee tres precondiciones (`sys.line_parameters_ok_status`, `sys.environment_ok_status`,
   `sys.standby_system_ok_status`). Si alguna es falsa, la rutina termina en `FAILED` sin tocar
   ningún comando.
2. Si las tres están en OK, pulsa `sys.turn_on_radar_conmand` (`True` → 100 ms → `False`) — el DO
   es de flanco de subida, no de nivel (`radar_emulator/docs/interfaces/modbus.md#comandos-por-flanco`).
3. Tras un margen de un tick + holgura, relee las tres precondiciones. Si siguen en OK, termina en
   `SUCCESS`.

**PEND-RCP-06** (`docs/alcance/pendientes.md`): tanto el conjunto/orden de precondiciones como el
criterio de éxito ("las precondiciones siguen en OK") son una inferencia de este repo a partir de
los nombres del catálogo — no hay procedimiento fijado por el plan, manual del fabricante, ni
señal de confirmación tipo "radar encendido" en el catálogo RD100S. Sin confirmar con el product
expert.

## Qué prueba `general_power_on_spike.py`

Contra la misma instancia de `radar_emulator` que Fase 1 (mismo override de puertos —
Modbus `15020`, UDP `15100`, WS `18080`; ver `spike-fase1/README-hal-sim.md`):

- Con las tres precondiciones en falso (default de la semilla): la rutina reporta `FAILED` y
  **no** toca `sys.turn_on_radar_conmand`.
- Forzando las tres a `True` vía el canal WS de control (`force`/`release`, mismo mecanismo que
  `spike-fase1/fault_injection_spike.py`): la rutina reporta `SUCCESS`, y el comando vuelve a
  `False` después del pulso (confirma que es flanco, no nivel, ya que `radar_emulator` no tiene
  lógica que lo baje por sí solo — lo hace la propia rutina).

## Qué NO prueba este spike

- Que la secuencia de tres precondiciones sea la correcta para hardware real — no hay forma de
  validarlo contra este emulador ni contra el plan, ver PEND-RCP-06.
- Las otras cinco rutinas de control, la guarda de seguridad de parámetros, ni nada de scan/BITE
  — quedan para las siguientes tareas de Fase 2.

## Cómo correrlo

Con `radar_emulator` corriendo (mismo override de Fase 1):

```bash
uv run python spike-fase2/general_power_on_spike.py --ws ws://127.0.0.1:18080 --modbus-port 15020 --udp-port 15100
```

Ver `RESULTADO-general-power-on.md`.
