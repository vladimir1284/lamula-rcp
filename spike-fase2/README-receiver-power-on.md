# Spike Fase 2 — rutina "encendido del receptor analógico" (Rutina 3)

Plan §4.3, Rutina 3 de seis: `core/control_routines/receiver_power_on.py`. Primer borrador, sin
confirmar con el product expert (PEND-RCP-07).

`docs/interfaces/websocket.md`/`modbus.md` de `radar_emulator` confirman `Turn On RFE`/`Turn Off
RFE` como par de flanco (pulso), igual patrón que Rutinas 1 y 2 — sin la ambigüedad de la Rutina 4.

## Hallazgo: el subsistema `rx` no tiene ningún bloque de lógica en la semilla

A diferencia de las rutinas anteriores, `radar_emulator/config/rd100s.seed.json` no calcula
**ninguna** señal `rx.*` — ni las tres fuentes de alimentación, ni `rx.rfe_on_status`, ni
`rx.stalo_locked_status`. Quedan en `false` salvo que algo las fuerce por el canal WS. Por eso
este spike, a diferencia de los anteriores, fuerza también las señales de éxito, no solo la
precondición — de otro modo el camino de éxito de la rutina sería imposible de alcanzar contra
este simulador, sin que eso diga nada sobre si la implementación está bien.

## Cómo correrlo

Con `radar_emulator` corriendo (mismo override de puertos que el resto de Fase 1/2):

```bash
uv run python spike-fase2/receiver_power_on_spike.py --ws ws://127.0.0.1:18080 --modbus-port 15020 --udp-port 15100
```

Ver `RESULTADO-receiver-power-on.md`.
