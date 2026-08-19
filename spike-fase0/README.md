# Spike fase 0 — cliente Modbus (pymodbus) y receptor UDP (RD100S-ENC-UDP v1)

Cubre el punto 1 y 2 de "Lo primero dentro de esta fase" en
[fases.md](../docs/implementacion/fases.md). No es código de producción: valida, desde el lado
consumidor (RCP), lo que `radar_emulator` ya expone del lado servidor/emisor.

Corre contra una instancia local de `radar_emulator` con una config derivada de
`config/rd100s.seed.json` (puerto Modbus y destino UDP remapeados a puertos no privilegiados para
no requerir root; ningún otro campo cambia).

```
python3 -m venv .venv
.venv/bin/pip install pymodbus websockets
.venv/bin/python spike-fase0/modbus_client_spike.py --port 15020
.venv/bin/python spike-fase0/udp_encoder_spike.py --port 15100
.venv/bin/python spike-fase0/udp_degradation_spike.py --ws ws://127.0.0.1:18080 --udp-port 15100
```

`udp_degradation_spike.py` necesita el panel WebSocket del emulador arriba (mismo `RD100S_HTTP_PORT`
usado al levantar `radar_emulator`), no solo el emisor UDP.

Ver `RESULTADO.md` para el resultado documentado.
