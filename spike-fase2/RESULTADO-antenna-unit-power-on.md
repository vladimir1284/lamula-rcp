# Resultado — spike rutina "encendido de la unidad de antena"

Ejecutado 2026-08-19, `antenna_unit_power_on_spike.py` vía `uv run` contra una instancia real de
`radar_emulator` (mismo override de puertos que el resto de Fase 1/2).

## PASA

- Radomo abierto (default) → `FAILED` sin escribir `ant.turn_on_off_au_conmand`.
- Radomo cerrado pero `ant.au_on_status`/`drive_az_ok_status`/`drive_el_ok_status` nunca forzados
  (nada los calcula en el simulador) → `FAILED` por timeout, con el comando ya confirmado escrito
  en los pasos.
- Confirmado que el comando queda en `True` sostenido (nivel), no vuelve solo a `False` — la
  rutina no lo trata como pulso.
- Radomo cerrado y las tres señales de éxito forzadas a verdadero → `SUCCESS`.

6/6 verificaciones en `OK`.

## Qué NO prueba este spike

- Ningún comportamiento real de la unidad de antena — el subsistema no tiene ningún bloque de
  lógica en `radar_emulator`; el camino de éxito solo demuestra que la rutina lee correctamente
  las señales que se le fuerzan.
- Que "nivel, no pulso" sea la interpretación correcta del comando en el radar real — sigue
  siendo una inferencia sin confirmar, ver docstring de `antenna_unit_power_on.py`.
- Tiempo real de encendido de la unidad de antena — sin ninguna pista del simulador,
  `confirm_timeout_s` es obligatorio en la rutina, sin default.

## Sigue pendiente

Con esto, las seis rutinas del plan (§4.3) tienen primer borrador implementado y probado contra
el simulador. PEND-RCP-07 (extendido): confirmar con el product expert si
`ant.turn_on_off_au_conmand` es pulso o nivel, y el tiempo real de encendido de la unidad de
antena.
