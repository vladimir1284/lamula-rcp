# Spike Fase 2 — BITE cableado al gateway

Cablea `core/bite/manager.py` (ver `spike-fase2/RESULTADO-bite-manager.md`) al gateway
(`src/adapters/gateway/app.py`), mismo patrón de "estado resumido en REST + evento por WS" que
`DspStreamStatus` (D-10, Fase 1) y `OperatorEventMessage`.

## Qué se agregó

- `core/contracts/mmi.py`: `BiteFaultSummary` (para `SystemStatusSnapshot.active_bite_faults`) y
  `BiteEventMessage` (nuevo tipo del sobre WS, `type: "bite_event"`). `since_wall` en
  `BiteFaultSummary` la asigna el gateway al detectar la falla — el `at_us` monotónico de
  `BiteEvent` (core) no se convierte, se asigna una hora de pared nueva al cruzar la frontera
  hacia la MMI (AGENTS.md "dos relojes"), igual criterio que `ControlAuthorityState.since_wall`.
- `adapters/gateway/app.py`: una tarea de fondo (`_bite_poll_loop`, no atada a ninguna conexión
  WS particular) sondea `BiteManager` cada `BITE_POLL_PERIOD_S=0.5s` y hace broadcast de un
  `BiteEventMessage` por cada transición nueva. `GET /api/status.active_bite_faults` expone el
  snapshot de fallas activas.

**Por qué un solo poller de fondo, no dentro del loop por conexión WS:** el loop de
`AntennaMessage`/`HeartbeatMessage` corre una vez por cada cliente conectado; si `BiteManager.poll()`
corriera ahí, con N clientes se llamaría N veces por ciclo sobre el mismo estado mutable
compartido — condición de carrera real, no hipotética. Con cero clientes conectados tampoco se
sondearía nunca. Una tarea única evita ambos problemas.

## Cómo correrlo

Con `radar_emulator` corriendo (ver `README-hal-sim.md` de spike-fase1) y el gateway:

```bash
cd lamula-rcp
PYTHONPATH=src uv run python -m adapters.gateway --modbus-port 15020 --udp-port 15100 --http-port 18000
```

Y en otra terminal:

```bash
uv run python spike-fase2/bite_gateway_spike.py --http-port 18000
```

Ver `RESULTADO-bite-gateway.md`.
