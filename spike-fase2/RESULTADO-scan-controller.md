# Resultado — spike Scan Controller (alcance acotado)

Ejecutado 2026-08-20, `scan_controller_spike.py` vía `uv run` contra una instancia real de
`radar_emulator` (config derivada regenerada desde la semilla actual — Modbus `15020`, UDP
`15100`, WS/HTTP `18080`, proceso levantado y apagado solo para este spike, no compartido con
otras sesiones).

## PASA — 9/9 verificaciones

- `ant.au_on_status` en falso → `FAILED` limpio, propagado desde la precondición de la Rutina 5
  (nada movido).
- `RhiCut` simple sin wrap (azimut fijo=45°, elevación 0°→15°) → `SUCCESS`; elevación final
  14,6° (objetivo 15° ± 4°, margen esperado por frenado/detección de fin de barrido); azimut se
  mantuvo fijo en ~45,9°.
- `PpiCut` simple sin vuelta completa (elevación fija=10°, azimut 90°→180°) → `SUCCESS`; elevación
  se mantuvo fija en ~11°; azimut final ~179° (objetivo 180° ± 4°).
- Interrupción: traba térmica de azimut (`ant.i2t_drive_az_status`) forzada a mitad de un barrido
  de azimut (180°→270°) — detectada en curso (azimut > 185°) antes de forzar la traba → outcome
  `INTERRUPTED`.

## Bug encontrado y corregido (no es del Scan Controller, es del HAL simulado)

`src/adapters/hal_sim/simulated_hal.py`: `write_analog`/`read_analog` no manejaban la codificación
con signo (`int16`) de analógicas con rango crudo negativo (ej. `ant.speed_reference_driver_az`,
`-32768..32767`) contra el registro Modbus, que en el wire es sin signo (`0..65535`). Se manifestó
al primer intento de comandar un voltaje negativo (posicionamiento corrigiendo "hacia atrás") —
`struct.error: 'H' format requires 0 <= number <= 65535`. Nunca disparado antes porque ningún
spike de Fase 1/2 había comandado una analógica negativa. Corregido con conversión de complemento
a dos de 16 bits en la frontera del wire (ver README). **No estaba en el alcance original de esta
tarea, pero bloqueaba cualquier corte que requiriera corrección negativa — casi todos.**

## Detalle operativo: keepalive WS del cliente de prueba

La conexión WS de control por defecto (`websockets.connect` sin parámetros) se cerró sola a mitad
de la prueba (`ConnectionClosedError: ... keepalive ping timeout`) — este spike corre varios
minutos reales (barridos completos), a diferencia del resto de Fase 2 que solo confirma arranque
(segundos). El emulador no implementa ningún hearteat propio (`radar_emulator/src/adapters/ws/
server.ts` no tiene lógica de ping/timeout) — es enteramente el keepalive por defecto de la
librería cliente Python. Corregido abriendo la conexión con `ping_interval=None` en el spike.
Reproducible dos veces exactas antes de la corrección, no volvió a aparecer después.

## Qué NO prueba este spike

- Que `sweep_voltage_magnitude`/`AxisPositioningParams` de prueba sean valores razonables para el
  radar real — arbitrarios, elegidos solo para que el spike converja en un tiempo manejable.
- Vuelta completa de PPI (`azimuth_end_deg == 360`, ver comentario en `PpiCut` de
  `core/contracts/scan.py`) — no se ejercitó ese caso límite del acumulador de delta angular en
  este spike; la lógica es la misma que el caso parcial (acumula hasta alcanzar el ancho total
  pedido), pero no hay verificación específica del caso de 360° exactos.
- HV/radiar y aplicación de PRF/pulse-width — deliberadamente fuera de alcance, ver README.
- Sobrepaso de frenado con voltajes de barrido más altos que los de prueba — misma limitación ya
  conocida de la Rutina 6, heredada aquí porque el Scan Controller usa `run_antenna_positioning`
  para los pasos de posicionamiento previos al barrido.

## Sigue pendiente

Propuesta de entrada nueva para `docs/alcance/pendientes.md` (no escrita aquí — a insertar por
quien integre este trabajo):

> **PEND-RCP-10 · Scan Controller: alcance acotado a movimiento de antena, sin confirmar (Fase 2)**
>
> `core/scan_controller.py` (`run_scan_cut`) secuencia solo el movimiento de antena de un corte del
> Scan Worksheet (posicionar eje fijo + barrer eje móvil, apoyado en las Rutinas 5/6). Deliberadamente
> no sube alta tensión ni radía (ver docstring del módulo — `transmitter_power_on.py` se detuvo en
> `tx.ready_status` a propósito, sin que exista todavía una secuencia decidida para lo que sigue) ni
> aplica `prf_hz`/`pulse_width_us` a ningún adaptador (PEND-RCP-08, bloqueado). La detección de fin de
> barrido (acumulación de delta angular hasta alcanzar el ancho total pedido) es diseño propio de este
> repo sin nada que imitar del simulador ni del plan — mismo criterio que ya justificó los parámetros
> obligatorios de la Rutina 6. Probado como primer borrador contra una instancia real de
> `radar_emulator` (`spike-fase2/RESULTADO-scan-controller.md`): `RhiCut`/`PpiCut` simples,
> interrupción por guarda de seguridad a mitad de barrido. Sin confirmar con el product expert.
> **Acción pendiente explícita:** decidir con el experto la secuencia de HV/radiar al arrancar un
> escaneo (candidato natural para donde `transmitter_power_on.py` se detuvo), y si la detección de
> fin de barrido por acumulación de delta es aceptable o si el radar real ofrece una señal de
> posición de referencia distinta. Extiende PEND-RCP-07/09 (ganancia volt→grados/s, relación
> PRF/pulse-width/ancho de haz→velocidad de rotación) a este nuevo consumidor.
