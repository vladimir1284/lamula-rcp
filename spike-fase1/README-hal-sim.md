# Spike Fase 1 — HAL-simulador (`src/adapters/hal_sim`) contra `radar_emulator`

Primer punto de "Lo primero dentro de esta fase" de
[fases.md](../docs/implementacion/fases.md#fase-1--foundations--simulator-semanas-4-10):
adaptador simulador del HAL. `src/adapters/hal_sim/SimulatedHAL` implementa
`HardwareAbstractionLayer` (`src/core/contracts/hal.py`, ya congelado) con un cliente Modbus TCP
(una sola conexión, diez unit IDs, `pymodbus`) más un receptor UDP de encoder
(`RD100S-ENC-UDP v1`).

`hal_sim_spike.py` no es la prueba unitaria del adaptador — es la prueba de humo end-to-end
contra una instancia real de `radar_emulator`, en el mismo espíritu que
`spike-fase0/modbus_client_spike.py` y `spike-fase0/udp_encoder_spike.py`.

## Catálogo de señales

`src/adapters/hal_sim/rd100s_signal_catalog.json` es una **copia vendorizada**, no una lectura
en vivo del repo `radar_emulator` (decisión 2026-08-19, ver
[pendientes.md](../docs/alcance/pendientes.md)) — 111 de las 116 señales de
`radar_emulator/config/rd100s.seed.json` (se excluyen las 5 de kind `VIRT`: posición/velocidad
de antena, que llegan por UDP, no por Modbus, y `tx.interlocks_ok`, interno al emulador). Si
`radar_emulator` cambia su mapa de señales, esta copia hay que resincronizarla a mano.

## Cómo levantar el emulador para correr el spike

`radar_emulator` (repo sibling) expone Modbus en el puerto `502` y UDP hacia `controller:5100`
por defecto en la semilla — puertos privilegiados/hostname que no sirven para una prueba local
sin root. Hace falta una config derivada con esos dos campos remapeados, nada más (mismo patrón
que ya usaron los spikes de Fase 0 — ver `spike-fase0/RESULTADO.md`):

```bash
# config derivada de radar_emulator/config/rd100s.seed.json con:
#   transports.modbus_tcp.port = 15020
#   transports.encoder_udp.dest_host = "127.0.0.1", dest_port = 15100
cd /path/a/radar_emulator
RD100S_CONFIG=/ruta/a/rd100s.override.json pnpm dev
```

Con el emulador corriendo:

```bash
cd lamula-rcp
uv run python spike-fase1/hal_sim_spike.py --modbus-port 15020 --udp-port 15100
```

Ver `RESULTADO-hal-sim.md` para el resultado documentado.
