# Spike Fase 2 — rutina "posicionamiento de antena" (Rutina 6, última)

Plan §4.3, Rutina 6 de seis: `core/control_routines/antenna_positioning.py`. Con esto quedan las
seis rutinas del plan implementadas como primer borrador (ninguna confirmada con el product
expert — PEND-RCP-06/07).

A diferencia de las otras cinco, aquí no hay **ningún** valor real ni siquiera aproximado que
tomar del simulador — `radar_emulator` no modela ningún lazo de posicionamiento. Por eso
`gain_v_per_deg`, `max_voltage`, `tolerance_deg` y `timeout_s` son parámetros obligatorios de la
rutina, sin default: inventar un número aquí y esconderlo como constante sería fabricar un dato
sin ningún respaldo. Este spike los pasa como valores de prueba explícitos (`GAIN_V_PER_DEG=0.3`,
`MAX_VOLTAGE=2.0 V`, `TOLERANCE_DEG=1.0°`), no como recomendación.

Se apoya en la Rutina 5 (`run_antenna_movement`) en cada paso: mide posición vía
`hal.read_antenna_position()`, calcula error (con distancia angular corta para azimut, que gira
continuo), pide un voltaje proporcional al error, y repite hasta entrar en tolerancia. Propaga tal
cual lo que devuelva la Rutina 5 (`FAILED`/`INTERRUPTED`) si la guarda de seguridad de parámetros
rechaza, o si el encoder reporta lectura inválida.

## Limitación conocida, no resuelta aquí

Control proporcional simple, sin frenado anticipado por distancia de parada: como la
desaceleración del bloque `axis` del simulador está limitada, el eje sigue recorriendo distancia
mientras frena una vez que la rutina decide "ya estoy en tolerancia" — puede terminar más lejos
del objetivo que `tolerance_deg`. Es exactamente la pregunta que `rutinas-control.md` deja abierta
para el experto. Con valores de voltaje/ganancia bajos (los de este spike) el sobrepaso es
pequeño; con valores más altos podría no serlo — no se intenta resolver con una fórmula de
frenado inventada sin un valor real de aceleración.

## Cómo correrlo

Con `radar_emulator` corriendo (mismo override de puertos que el resto de Fase 1/2):

```bash
uv run python spike-fase2/antenna_positioning_spike.py --ws ws://127.0.0.1:18080 --modbus-port 15020 --udp-port 15100
```

Ver `RESULTADO-antenna-positioning.md`.
