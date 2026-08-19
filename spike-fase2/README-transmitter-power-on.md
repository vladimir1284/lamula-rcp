# Spike Fase 2 — rutina "encendido del transmisor" (Rutina 2)

Plan §4.3, Rutina 2 de seis: `core/control_routines/transmitter_power_on.py`. Primer borrador,
mismo estado que las demás — probado contra el simulador, sin confirmar con el product expert
(PEND-RCP-07).

Única de las seis rutinas donde el simulador reproduce una secuencia interna con temporizadores
propios (`tx.fsm`, tipo `state_machine`: `OFF -> STARTING -> WARMUP -> READY -> HV_ON ->
RADIATING`, más `FAULT`). Este spike fuerza los seis interlocks reales y `tx.turn_off_tx_command`
vía el canal WS de control — mismo mecanismo que el resto de Fase 1/2 — e incluye una corrida
completa esperando el caldeo real del magnetrón (`after_ms: 180000` en la semilla, ~3 minutos) con
`--full-warmup`.

## Alcance elegido: OFF a READY, no más allá

El plan nombra seis rutinas, ninguna llamada "subir alta tensión" o "empezar a radiar" — eso
tiene más sentido como parte de arrancar un escaneo que como parte de un encendido que se hace
una vez. Esta rutina se detiene en `tx.ready_status`; subir HV y habilitar salida
(`run_transmitter_hv_on`, no implementada) queda para cuando exista el Scan Controller. Ver
docstring de `transmitter_power_on.py` para el razonamiento completo.

## Hallazgos frente a `docs/operacion/rutinas-control.md`

- La transición real `OFF -> STARTING` del `tx.fsm` **no exige ningún interlock** — solo
  `rising(tx.turn_on_tx_command) and not tx.turn_off_tx_command`. Los interlocks solo los exige
  la transición `READY -> HV_ON`, fuera del alcance de esta rutina. La rutina implementada los
  chequea igual, como precondición propia del RCP más estricta que el simulador (mismo criterio
  que `general_power_on.py`), no porque el simulador la exija.
- Son **seis** interlocks reales, no siete: el simulador los agrega en `tx.interlocks_ok`, señal
  interna sin mapeo Modbus (`kind: VIRT`) — el RCP tiene que leer y combinar las seis por su
  cuenta. `tx.interlock_ok_status` (una de las seis) ya es, ella misma,
  `ant.radome_closed_status and sys.standby_system_ok_status` — "radomo cerrado" y "sistema en
  espera" del doc son la misma señal agregada, no dos independientes.
- `tx.turn_on_blowers_command`/`turn_on_fps_command`/`turn_on_mps_command` están en el catálogo
  pero ningún bloque de `radar_emulator` los usa — el `tx.fsm` enciende esos subsistemas como
  efecto automático de entrar a `STARTING`. Puede ser una simplificación del simulador o el orden
  real; sin confirmar, esta rutina no los escribe.

## Cómo correrlo

Con `radar_emulator` corriendo (mismo override de puertos que el resto de Fase 1/2):

```bash
uv run python spike-fase2/transmitter_power_on_spike.py --ws ws://127.0.0.1:18080 --modbus-port 15020 --udp-port 15100
# agregar --full-warmup para incluir la espera real de ~180s del caldeo
```

Ver `RESULTADO-transmitter-power-on.md`.
