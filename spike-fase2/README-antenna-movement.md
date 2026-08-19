# Spike Fase 2 — rutina "movimiento de antena" (Rutina 5)

Plan §4.3, Rutina 5 de seis: `core/control_routines/antenna_movement.py`. Primer borrador, mismo
estado que `general_power_on_spike.py` — probado contra el simulador, sin confirmar con el
product expert (PEND-RCP-07).

Ejercita `run_antenna_movement` con precondición (`ant.au_on_status`), la guarda de seguridad de
parámetros (`core/safety_guard/check_antenna_movement`, ver `spike-fase2/parameter_guard_spike.py`)
consultada tanto antes de mover como durante el movimiento, y confirmación de arranque/detención
vía `hal.read_antenna_position()`. Fuerza `ant.au_on_status`, `ant.el_upper_limit_status` e
`ant.i2t_drive_az_status` en vivo por el canal WS de control de `radar_emulator` — mismo mecanismo
que el resto de los spikes de Fase 1/2 —, incluyendo el caso de disparar la traba a **mitad de un
movimiento en curso** (tarea `asyncio` corriendo la rutina + `force` concurrente) para ejercitar
`RoutineOutcome.INTERRUPTED`, no solo el chequeo previo.

## Hallazgo que cambia el diseño propuesto en `rutinas-control.md`

La página describe la rutina como "enviar una velocidad deseada (grados/s)". La señal real
(`ant.speed_reference_driver_az`/`_el`, catálogo vendorizado) está en **voltios** (±10 V) — es una
referencia analógica a un variador, no un valor en grados/s. El simulador la convierte con un
`gain_deg_s_per_volt` marcado como pendiente de confirmar en su propia config; no hay ganancia
real del RD100S para hacer esa conversión en el RCP. La rutina implementada recibe
`voltage_reference` en voltios, no una velocidad en grados/s — ver docstring de
`antenna_movement.py`. Por lo mismo, **no confirma magnitud** de velocidad, solo sentido de giro y
que el eje efectivamente arranca o se detiene.

## Por qué la guarda se consulta también durante el movimiento, no solo antes de empezar

El bloque `axis` de elevación en el simulador lee su propio fin de carrera y se autolimita: el de
azimut **no** lee `ant.i2t_drive_az_status` — calcula la falla térmica pero no corta el drive él
mismo. Sin este sondeo activo, un viaje en azimut que dispara la protección térmica a mitad de
camino seguiría recibiendo la referencia de voltaje indefinidamente del lado del RCP. Ver
docstring de `core/safety_guard/antenna_limits.py`.

## Cómo correrlo

Con `radar_emulator` corriendo (mismo override de puertos que el resto de Fase 1/2):

```bash
uv run python spike-fase2/antenna_movement_spike.py --ws ws://127.0.0.1:18080 --modbus-port 15020 --udp-port 15100
```

Ver `RESULTADO-antenna-movement.md`.
