# Spike Fase 2 — System Status & BITE Manager

Plan §4.4: "Aggregates subsystem status; manages BITE/fault messages, filtering and history;
surfaces ORPG-link health". `core/bite/manager.py`. A diferencia de las seis rutinas de control,
esto no tiene un procedimiento operativo que confirmar con el product expert — es agregación
mecánica de señales de estado ya existentes, no una secuencia nueva. Sí quedan simplificaciones
documentadas abajo.

## Cómo se eligió qué monitorear

Todas las señales `*_ok_status` del catálogo vendorizado (sanas en `True`, convención consistente
en `sys.*`/`tx.*`/`rx.*`/`ant.*`), más `*_fault_status`/`*_over_current_status` (sanas en `False`),
más dos excepciones fuera de ese patrón de sufijo:
`ant.i2t_drive_az_status`/`ant.i2t_drive_el_status` (protección térmica, mismo hallazgo que
`core/safety_guard/antenna_limits.py`).

**Deliberadamente excluidas:** señales de estado positivo (`tx.tx_on_status`, `ant.au_on_status`,
`rx.rfe_on_status`, `ant.el_upper_limit_status`, etc.) — su "malo" depende del contexto operativo
(un transmisor apagado no es una falla si nadie lo encendió), no del nombre. Incluirlas dispararía
una falla permanente en reposo, no algo útil para el operador.

**Salud del enlace ORPG (parte del plan §4.4) queda fuera** — esa interfaz no existe todavía
(PEND-RCP-04).

**Filtrado por subsistema, no por severidad** — el catálogo no tiene ningún metadato de
severidad; inventar una escala sin respaldo del product expert sería el mismo error ya evitado en
`antenna_positioning.py`.

## Qué prueba este spike

- Primer `poll()` reporta como `FAULT` cualquier señal monitoreada que ya esté en mal estado
  (la semilla de `radar_emulator` arranca con casi todas las `*_ok_status` no cableadas en
  `False` — quince de las veinte señales monitoreadas aparecieron en falla desde el primer poll).
- Un segundo `poll()` sin cambios no genera eventos nuevos (no repite la misma falla en cada
  ciclo).
- Forzar una señal de `False` a `True` genera `CLEARED` y la saca de `active_faults()`.
- Forzar `tx.mps_fault_status` (patrón `*_fault_status`, sana en `False`) a `True` genera `FAULT`.
- `history(subsystem=...)` filtra correctamente por prefijo de `signal_id`.

8/8 verificaciones en `OK`, contra una instancia real de `radar_emulator`.

## Qué NO hace todavía

- No está integrado al gateway (`adapters/gateway/app.py`) ni expuesto por REST/WS a la MMI —
  esta pieza es solo el núcleo en `core/bite/`, análogo a como `core/safety_guard/` se construyó
  antes de que la Rutina 5 lo consumiera. Cablearlo al gateway (snapshot en `/api/status`, o
  mensajes WS para el BITE Message Window) queda para cuando se construya esa parte de la MMI.
- No hay ninguna noción de severidad — todo evento es "falla"/"despejada" sin escala de
  criticidad.

## Cómo correrlo

Con `radar_emulator` corriendo (mismo override de puertos que el resto de Fase 1/2):

```bash
uv run python spike-fase2/bite_manager_spike.py --ws ws://127.0.0.1:18080 --modbus-port 15020 --udp-port 15100
```

Ver `RESULTADO-bite-manager.md`.
