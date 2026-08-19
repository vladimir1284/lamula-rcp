# Spike Fase 1 — gateway RCP↔MMI (`src/adapters/gateway`)

Segundo punto de "Lo primero dentro de esta fase" de
[fases.md](../docs/implementacion/fases.md#fase-1--foundations--simulator-semanas-4-10):
esqueleto del gateway + primer "pipe de datos en vivo sim→WS→PPI". `src/adapters/gateway/app.py`
expone en FastAPI el sobre REST/WS ya congelado en `src/core/contracts/mmi.py`, sobre un
`SimulatedHAL` (ver `README-hal-sim.md`).

Superficie de esta primera versión:

- `GET /api/status` → `SystemStatusSnapshot` (autoridad de control, `hal_connected`, última
  posición de antena).
- `POST /api/control` → `SetControlModeRequest` in, `ControlAuthorityState` out; hace broadcast
  de un `OperatorEventMessage` a todos los WS conectados.
- `WS /ws` → al conectar manda `SessionMessage`; después, `AntennaMessage` a 10 Hz (throttle
  deliberado frente a los 100 Hz del encoder UDP) y `HeartbeatMessage` cada segundo.

**Qué NO tiene todavía:** autenticación, persistencia de sesión, stream de DSP/momentos (sigue
en el stub `spike-fase0/dsp_moment_stream_spike.py`, no conectado aquí), ni buffer de eventos
para un cliente que se reconecta a mitad de sesión.

## Cómo correrlo

Con `radar_emulator` corriendo (ver `README-hal-sim.md`):

```bash
cd lamula-rcp
PYTHONPATH=src uv run python -m adapters.gateway --modbus-port 15020 --udp-port 15100 --http-port 18000
```

Y en otra terminal:

```bash
uv run python spike-fase1/gateway_ws_spike.py --http-port 18000
```

Ver `RESULTADO-gateway.md` para el resultado documentado.
