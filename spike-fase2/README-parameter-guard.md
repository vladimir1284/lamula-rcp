# Spike Fase 2 — guarda de seguridad de parámetros (límites de antena)

Plan §4.3/§4.4: `Parameter-Safety Guard` — "antenna limit checks and prevention of pulse-width ×
PRF combinations that would damage the klystron/magnetron", "low safety responsibility", solo
lectura de estado, complementa el enclavamiento de hardware.

Este spike solo cubre la **primera mitad**: `core/safety_guard/check_antenna_movement` contra
`ant.el_upper_limit_status` / `ant.el_lower_limit_status` (fin de carrera de elevación) y
`ant.i2t_drive_az_status` (protección térmica de azimut) — las tres son señales reales que
`radar_emulator` ya calcula (ver docstring de `core/safety_guard/antenna_limits.py`). Se disparan
en vivo vía el canal de control WS (`force`/`release`, mismo mecanismo que
`spike-fase1/fault_injection_spike.py` y `spike-fase2/general_power_on_spike.py`).

**No cubre** la parte de PRF × pulse-width del plan: no existe hoy ninguna señal HAL ni campo en
`core/contracts/dsp.py` que la guarda pueda consultar — depende del Scan Worksheet (sin
implementar) y de un contrato con el generador de forma de onda que tampoco existe. Ver
PEND-RCP-08 en `docs/alcance/pendientes.md`.

## Hallazgo que motivó una corrección de doc

Al verificar contra `radar_emulator/config/rd100s.seed.json` (no solo el catálogo vendorizado) se
confirmó que `docs/operacion/rutinas-control.md` (Rutina 5) tenía la protección térmica
invertida: decía "elevación tiene protección térmica, azimut no". Es al revés — azimut tiene el
único bloque `i2t` real de la semilla; `ant.i2t_drive_el_status` existe como señal pero ningún
bloque la calcula (sin cablear). Corregido en el mismo commit que este spike.

## Cómo correrlo

Con `radar_emulator` corriendo (mismo override de puertos que el resto de Fase 1/2):

```bash
uv run python spike-fase2/parameter_guard_spike.py --ws ws://127.0.0.1:18080 --modbus-port 15020 --udp-port 15100
```

Ver `RESULTADO-parameter-guard.md`.
