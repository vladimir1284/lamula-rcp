# Spike Fase 2 — Scan Controller, alcance acotado

Plan (project-plan.md, tabla de componentes): "Scan Controller & Scheduler | Sequences
interactive and automated volume scans; drives the control routines". Esta primera versión
(`core/scan_controller.py`, `run_scan_cut`) cubre solo la mitad de "secuenciar": dado un corte del
Scan Worksheet manual (`core/contracts/scan.py`, `PpiCut`/`RhiCut`), posiciona el eje fijo y barre
el eje móvil, apoyándose en las Rutinas 5 y 6 ya construidas (`core/control_routines/`).

## Decisión explícita de esta sesión: qué NO hace

- **No sube alta tensión ni empieza a radiar.** `core/control_routines/transmitter_power_on.py`
  se detiene a propósito en `tx.ready_status` — "subir HV/radiar" quedó identificado ahí como
  trabajo que tiene más sentido al arrancar un escaneo, no como parte del encendido, pero sigue
  sin construirse. Es seguridad crítica sin una secuencia decidida (¿antes de posicionar? ¿al
  llegar al inicio del barrido? ¿qué enclavamientos revisar de nuevo?) — no se inventa aquí.
- **No aplica `prf_hz`/`pulse_width_us` a ningún adaptador de forma de onda.** No existe ninguno
  — PEND-RCP-08, bloqueado. Los dos campos viajan en el `cut` sin usarse.

Este controlador es puramente "hacia dónde apunta la antena y durante cuánto tiempo", no "qué
transmite ni qué recibe".

## Algoritmo

1. Determina eje fijo/eje de barrido según `cut.mode` (`PpiCut`: fijo=elevación, barrido=azimut;
   `RhiCut`: fijo=azimut, barrido=elevación).
2. Posiciona el eje fijo con la Rutina 6 (`run_antenna_positioning`). Si no sale `SUCCESS`, propaga
   el outcome tal cual — mismo criterio de no-reintentar que ya usa `antenna_positioning.py`.
3. Posiciona el eje de barrido a su ángulo de inicio, mismo criterio de propagación.
4. Arranca el barrido continuo con la Rutina 5 (`run_antenna_movement`), voltaje con signo según
   `end - start`. Una vez confirmado el arranque, la Rutina 5 ya retorna (no se queda bloqueada
   todo el barrido — es así a propósito, ver su docstring) — el Scan Controller sondea él mismo el
   resto del barrido.
5. Sondeo propio: en cada vuelta, chequea la guarda de seguridad de parámetros
   (`check_antenna_movement`) — si la rechaza, detiene y retorna `INTERRUPTED` (mismo patrón que la
   Rutina 5 cuando la guarda corta un movimiento en curso). Acumula el ángulo recorrido con signo
   (`_signed_delta_deg`, misma fórmula que `antenna_positioning._azimuth_error_deg`, generalizada a
   ambos ejes) hasta alcanzar el ancho total del barrido dentro de `sweep_tolerance_deg`, entonces
   detiene y retorna `SUCCESS`. Si se agota `sweep_timeout_s` sin completar, detiene y retorna
   `FAILED`.

**Detección de fin de barrido por acumulación de delta angular: diseño propio de este repo, sin
nada que imitar del simulador ni del plan** — mismo criterio que ya justificó los parámetros
obligatorios de la Rutina 6. Sin confirmar con el product expert — ver PEND-RCP-10 (propuesta,
pendiente de que el usuario la inserte en `docs/alcance/pendientes.md`).

`sweep_voltage_magnitude`, junto con los `AxisPositioningParams` por eje (`gain_v_per_deg`,
`max_voltage`, `tolerance_deg`, `timeout_s`), son obligatorios sin default — mismo criterio que
`antenna_positioning.py`: no existe ganancia real volt→grados/s confirmada ni relación
PRF/pulse-width/ancho de haz→velocidad de rotación confirmada (PEND-RCP-07/09).

## Bug encontrado y corregido en el camino: codificación con signo de analógicas Modbus

`src/adapters/hal_sim/simulated_hal.py` (`write_analog`/`read_analog`) no convertía entre el
rango crudo con signo (`int16`, `-32768..32767`, ej. `ant.speed_reference_driver_az`) y el
registro Modbus del wire, que es **sin signo** (`0..65535`). `to_raw()` devuelve el valor con
signo tal cual; escribirlo directo con `write_register` fallaba (`struct.error`) para cualquier
voltaje negativo. Nadie lo había disparado porque ningún spike anterior de Fase 1/2 comandó una
analógica negativa (`antenna_movement_spike.py` solo probó `+5.0V`). Corregido con conversión de
complemento a dos de 16 bits en ambos sentidos, en la frontera del wire (`simulated_hal.py`, no en
`signal_catalog.py` — ahí solo vive el escalado ingeniería↔crudo, agnóstico del wire).

## Cómo correrlo

Con `radar_emulator` corriendo (mismo override de puertos que el resto de Fase 1/2 — Modbus
`15020`, UDP `15100`, WS `18080`):

```bash
uv run python spike-fase2/scan_controller_spike.py --ws ws://127.0.0.1:18080 --modbus-port 15020 --udp-port 15100
```

Corre varios minutos reales (barridos completos, no solo confirmar arranque como el resto de
Fase 2) — la conexión WS de control se abre con `ping_interval=None` porque el keepalive por
defecto de la librería cliente cerraba la conexión a mitad de camino (ver
`RESULTADO-scan-controller.md`).

Ver `RESULTADO-scan-controller.md`.
