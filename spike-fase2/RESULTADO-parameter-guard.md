# Resultado — spike guarda de seguridad de parámetros (límites de antena)

Ejecutado 2026-08-19, `parameter_guard_spike.py` vía `uv run` contra una instancia real de
`radar_emulator` (mismo override de puertos que el resto de Fase 1/2: Modbus `15020`, UDP
`15100`, WS `18080`).

## PASA

- Sin ningún límite/traba forzado (valor calculado real de `radar_emulator`):
  `check_antenna_movement` permite elevación (arriba y abajo) y azimut.
- `ant.el_upper_limit_status` forzado a `True` → elevación/arriba rechazado; elevación/abajo
  sigue permitido (el límite superior no bloquea el sentido contrario).
- `ant.el_lower_limit_status` forzado a `True` → elevación/abajo rechazado.
- `ant.i2t_drive_az_status` forzado a `True` → azimut rechazado, con motivo que menciona
  explícitamente que el rearme requiere ciclar la unidad de antena (no hay comando de reset
  independiente, a diferencia de `tx.reset_faults_command`).
- Liberado `ant.i2t_drive_az_status` → azimut vuelve a permitirse.

8/8 verificaciones en `OK`.

## Qué NO prueba este spike

- La parte de PRF × pulse-width de la guarda (plan §4.3): no existe señal HAL ni contrato con
  Scan Worksheet/generador de forma de onda que consultar — PEND-RCP-08.
- Que los valores numéricos de los límites (fin de carrera de elevación, umbral térmico de
  azimut) sean los reales del RD100S — son marcadores de posición del simulador, PEND-RCP-07. La
  guarda no depende de esos números, solo de los booleanos ya calculados por el HAL activo.
- Que la guarda efectivamente impida un movimiento en curso — eso requiere la Rutina 5
  (movimiento de antena, sin implementar) llamando a esta guarda antes/durante el comando de
  velocidad; hoy es una función pura, sin nada que la invoque todavía.

## Sigue pendiente

PEND-RCP-08 (nuevo): guarda de PRF × pulse-width bloqueada por falta de Scan Worksheet y contrato
de forma de onda. PEND-RCP-07 sigue abierto para los valores numéricos de límites/umbrales.
Siguiente paso natural: Rutina 5 (movimiento de antena), que sería la primera en invocar esta
guarda.
