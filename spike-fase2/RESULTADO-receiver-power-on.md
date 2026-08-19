# Resultado — spike rutina "encendido del receptor analógico"

Ejecutado 2026-08-19, `receiver_power_on_spike.py` vía `uv run` contra una instancia real de
`radar_emulator` (mismo override de puertos que el resto de Fase 1/2).

## PASA

- Las tres fuentes de alimentación en falso (default) → `FAILED` sin escribir
  `rx.turn_on_rfe_conmand`.
- Fuentes forzadas a verdadero pero `rx.rfe_on_status`/`rx.stalo_locked_status` nunca forzados
  (nada los calcula en el simulador) → `FAILED` por timeout, con el pulso ya confirmado como
  enviado en los pasos.
- Fuentes, `rfe_on_status` y `stalo_locked_status` todos forzados a verdadero → `SUCCESS`.

5/5 verificaciones en `OK`.

## Qué NO prueba este spike

- Ningún comportamiento real del receptor — el subsistema `rx` no tiene ningún bloque de lógica
  en `radar_emulator`, así que el camino de éxito solo demuestra que la rutina lee correctamente
  las señales que se le fuerzan, no que el encendido real del RFE/STALO funcione de ninguna forma.
- Tiempo real de enganche del oscilador local — sin ninguna pista, ni siquiera un marcador de
  posición del simulador (a diferencia de la Rutina 2). `confirm_timeout_s` es obligatorio en la
  rutina, sin default.
- Que las tres fuentes de alimentación sean la precondición correcta, o que haga falta algún
  enclavamiento adicional — sin confirmar con el product expert.

## Sigue pendiente

PEND-RCP-07 (extendido): confirmar con el product expert el tiempo real de enganche del STALO y
si hace falta algún enclavamiento además de las tres fuentes de alimentación.
