# Spike Fase 1 — stream DSP conectado al gateway

Tercer punto de "Lo primero dentro de esta fase": conectar el stub de stream DSP
(`spike-fase0/dsp_moment_stream_spike.py`, PEND-RCP-05) al gateway
(`src/adapters/gateway`), en vez de dejarlo como script suelto de dos procesos.

`src/adapters/dsp/MomentStreamReceiver` es un servidor TCP de fondo dentro del gateway: escucha
el mismo framing que el stub emite (JSON de `RadialMoments` precedido de un largo de 4 bytes) y
mantiene contadores/estado resumido — no expone los momentos completos.

**Decisión 2026-08-19:** el estado del stream DSP se expone solo como `DspStreamStatus` dentro de
`GET /api/status` (`core/contracts/mmi.py`, contrato ya congelado, extendido con este campo) —
no como mensajes WS de momentos. Streaming de momentos reales (reflectividad, velocidad) a la
MMI queda para cuando se diseñe la vista PPI (Fase 2/3): resolverlo antes sería inventar una
forma de PPI sin acuerdo del equipo, justo lo que el contrato existe para evitar.

## Cómo correrlo

Con el gateway corriendo (ver `README-gateway.md`, agregar `--dsp-port 15551` o el que se use):

```bash
uv run python spike-fase1/dsp_gateway_spike.py --http-port 18000 --dsp-port 15551
```

Internamente invoca `spike-fase0/dsp_moment_stream_spike.py --role dsp` como si fuera un DSP real
conectándose a transmitir un volumen, y verifica que `GET /api/status` refleje el resultado. Ver
`RESULTADO-dsp-gateway.md`.
