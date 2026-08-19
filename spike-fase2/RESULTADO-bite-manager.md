# Resultado — spike System Status & BITE Manager

Ejecutado 2026-08-19, `bite_manager_spike.py` vía `uv run` contra una instancia real de
`radar_emulator` (mismo override de puertos que el resto de Fase 1/2).

## PASA

- Primer `poll()` reportó 15 de las 20 señales monitoreadas ya en `FAULT` (la mayoría de las
  `*_ok_status` de `tx`/`rx`/`ant` no están cableadas en la semilla, arrancan en `False` —
  hallazgo ya conocido de spikes anteriores, aquí se confirma que `BiteManager` lo refleja bien
  desde el primer poll en vez de quedarse callado).
- Segundo `poll()` sin cambios → sin eventos nuevos.
- `sys.line_parameters_ok_status` forzado a verdadero → `CLEARED`, sale de `active_faults()`.
- `tx.mps_fault_status` forzado a verdadero → `FAULT` (confirma la polaridad "sana en `False`").
- `history(subsystem="tx")` y `history(subsystem="sys")` filtran correctamente.

8/8 verificaciones en `OK`.

## Qué NO prueba este spike

- Ningún cableado real al gateway/MMI — ver README, esto es solo el núcleo.
- Las dos excepciones de polaridad (`ant.i2t_drive_az_status`/`i2t_drive_el_status`) no se
  ejercitaron aquí directamente — ya están cubiertas por
  `spike-fase2/RESULTADO-parameter-guard.md` contra la misma señal real de azimut; la de
  elevación sigue sin bloque que la calcule (siempre `False`, nunca dispara).

## Sigue pendiente

Cablear al gateway cuando se construya System Visualization en la MMI (snapshot en
`/api/status` o mensajes WS para el BITE Message Window + historial). Sin PEND nuevo — no hay
ninguna decisión operativa pendiente de confirmar con el product expert para esta pieza.
