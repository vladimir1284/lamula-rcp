# Resultado — spike HAL-simulador (`SimulatedHAL`) contra `radar_emulator`

Ejecutado 2026-08-19, `hal_sim_spike.py` vía `uv run` contra una instancia local real de
`radar_emulator` (no un stub propio — a diferencia de PEND-RCP-04/05, `radar_emulator` sí existe
y corre, esta es la primera prueba de Fase 1 con una implementación de referencia real del otro
lado).

## PASA

- `connect()`/`disconnect()`/`is_connected()` sobre `AsyncModbusTcpClient` (pymodbus 3.15).
- `read_digital` sobre una DI (`tx.tx_on_status`, unit 1, coil 0) — valor y `quality=ok`.
- `read_analog` sobre una AI (`tx.mps_output_voltage_sample`, unit 4, holding 0) — escalado raw
  int16 → kV vía `SignalSpec.to_engineering` (PEND-06 heredado: linealidad no confirmada contra
  hardware real).
- `write_digital` sobre una DO (`tx.turn_on_tx_command`, unit 3, coil 16) sin excepción.
- `write_analog` sobre una AO (`tx.voltage_reference_mps`, unit 2, holding 0) + read-back tras
  esperar > 1 tick (`tick_ms=50` de la semilla) — confirma la advertencia ya documentada en
  `hal.py` y en `spike-fase0/RESULTADO.md`: sin ese margen el read-back da el valor viejo.
- Guard del adaptador: `write_digital`/`write_analog` sobre una señal de solo lectura lanza
  `ValueError` **antes** de tocar el wire (no depende de la excepción Modbus del servidor para
  esto, aunque el servidor también la daría — ver `spike-fase0/modbus_client_spike.py`).
- `signal_catalog.get()` sobre un id inexistente lanza `KeyError` en vez de fallar en silencio.
- `read_antenna_position()` vía el receptor UDP de fondo (`asyncio.DatagramProtocol`) — posición,
  `seq` y bits de estado decodificados del paquete `RD100S-ENC-UDP v1` real emitido por el
  emulador.

## Qué NO prueba este spike

- Los 111 puntos del catálogo uno por uno — solo se ejercitó una DI, una DO, una AI y una AO como
  representantes de cada `kind`. No hay todavía una prueba exhaustiva de las 10 unit IDs (esa ya
  la hizo `spike-fase0/modbus_client_spike.py` desde el lado cliente puro, sin pasar por
  `SimulatedHAL`).
- Reinicio del emisor UDP ni pérdida de stream — `EncoderReceiver` implementa la detección
  (`resets_detected`, `STALE_TIMEOUT_S`) pero no se forzó ninguno de los dos aquí.
- Ningún test unitario con Modbus/UDP mockeados — pytest-asyncio no es dependencia todavía; esta
  prueba de humo depende de un `radar_emulator` real corriendo, igual que los spikes de Fase 0.

## Sigue pendiente

Decidir si vale la pena una suite pytest con mocks para CI (no bloquea Fase 1: el spike de humo
contra el emulador real ya prueba el camino completo) y ejercitar el resto del catálogo cuando el
resto del adaptador (interlocks, comandos por flanco Tx/RFE/Radar) se conecte a lógica de
dominio real más arriba en el core.
