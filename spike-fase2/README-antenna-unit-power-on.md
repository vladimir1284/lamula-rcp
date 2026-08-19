# Spike Fase 2 — rutina "encendido de la unidad de antena" (Rutina 4)

Plan §4.3, Rutina 4 de seis, última en implementarse:
`core/control_routines/antenna_unit_power_on.py`. Primer borrador, sin confirmar con el product
expert (PEND-RCP-07). Con esto, las seis rutinas del plan quedan implementadas como primer
borrador.

## Hallazgo: `ant.turn_on_off_au_conmand` tratado como nivel, no pulso

`docs/operacion/rutinas-control.md` (Rutina 4) ya señalaba que el catálogo tiene una sola orden
para esta rutina, no un par Encender/Apagar como las demás — posible indicio de que es un
interruptor de nivel, no un pulso. La lista de "Comandos por flanco" de
`radar_emulator/docs/interfaces/modbus.md` (Tx, RFE, Radar) confirma que **no** incluye a este
comando. Se trata como nivel — mismo criterio ya aplicado a `ant.enable_drive_az/el_conmand` en
`antenna_movement.py` — pero sigue siendo una inferencia, no una confirmación; si el radar real
lo maneja como pulso, esta implementación queda mal. Este spike confirma que la rutina en efecto
deja el comando en `True` sostenido, no que lo baje sola.

## Igual que el receptor: el subsistema no tiene ningún bloque de lógica en la semilla

Ni `ant.au_on_status` ni `ant.drive_az_ok_status`/`drive_el_ok_status` los calcula nada en
`radar_emulator` — este spike fuerza también las señales de éxito, no solo la precondición
(`ant.radome_closed_status`), mismo motivo que en `spike-fase2/RESULTADO-receiver-power-on.md`.

## Cómo correrlo

Con `radar_emulator` corriendo (mismo override de puertos que el resto de Fase 1/2):

```bash
uv run python spike-fase2/antenna_unit_power_on_spike.py --ws ws://127.0.0.1:18080 --modbus-port 15020 --udp-port 15100
```

Ver `RESULTADO-antenna-unit-power-on.md`.
