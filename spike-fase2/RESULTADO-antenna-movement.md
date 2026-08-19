# Resultado — spike rutina "movimiento de antena"

Ejecutado 2026-08-19, `antenna_movement_spike.py` vía `uv run` contra una instancia real de
`radar_emulator` (mismo override de puertos que el resto de Fase 1/2: Modbus `15020`, UDP
`15100`, WS `18080`).

## PASA

- `ant.au_on_status` en falso (default) → `run_antenna_movement` reporta `FAILED` sin escribir
  nada al HAL (`enable_drive_az_conmand`/`speed_reference_driver_az` sin cambios).
- `au_on_status` en verdadero, sin trabas: comanda azimut a +5 V → `SUCCESS`, con
  `hal.read_antenna_position().az_rate_deg_s` confirmando giro en el sentido pedido. Comandar
  0 V después → `SUCCESS` (eje detenido, `|az_rate_deg_s| <= 0.05`).
- `ant.i2t_drive_az_status` forzado a verdadero **antes** de iniciar → `FAILED`, referencia de
  azimut sin tocar (la guarda rechaza en la precondición, igual que Rutina 1 con sus tres
  `sys.*_ok_status`).
- `ant.i2t_drive_az_status` forzado a verdadero **a mitad de un movimiento en curso** (tarea
  `asyncio` + `force` concurrente) → `INTERRUPTED`, y tras un margen de un tick
  `ant.enable_drive_az_conmand` queda en `False` — confirma que la rutina se autoprotege
  deshabilitando el variador, ya que el simulador no lo hace por sí mismo para este eje.
- Mismo patrón para `ant.el_upper_limit_status`: activo de antemano → `FAILED`; disparado a mitad
  de camino → `INTERRUPTED`.

10/10 verificaciones en `OK`.

## Qué NO prueba este spike

- Magnitud de velocidad alcanzada — no hay ganancia real volt→grados/s del RD100S (ver
  README-antenna-movement.md); solo se confirma sentido y arranque/detención.
- Elevación con `ant.i2t_drive_el_status` — esa señal no tiene ningún bloque que la calcule en el
  simulador (sin cablear), la guarda ya la excluye a propósito (ver
  `core/safety_guard/antenna_limits.py`).
- Que la secuencia/preconciones elegidas (`au_on_status` como única precondición explícita, sin
  chequear `ant.drive_az_ok_status`/`drive_el_ok_status`, también sin cablear en el simulador) sean
  las correctas para hardware real — sin confirmar con el product expert, PEND-RCP-07.
- Rutina 6 (posicionamiento) — depende de esta rutina pero es diseño enteramente nuevo, sin nada
  que imitar del simulador.

## Sigue pendiente

PEND-RCP-07 (extendido): confirmar con el product expert la precondición elegida, si
`drive_{az,el}_ok_status` debería usarse y con qué semántica, y — nuevo hallazgo — la ganancia
real volt→grados/s del RD100S para que el RCP pueda traducir una velocidad deseada en grados/s a
la referencia de voltaje que el hardware real espera.
