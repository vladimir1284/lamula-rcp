# Resultado — spike stream DSP conectado al gateway

Ejecutado 2026-08-19, `dsp_gateway_spike.py` contra el gateway real corriendo
(`python -m adapters.gateway --dsp-port 15551 ...`) invocando
`spike-fase0/dsp_moment_stream_spike.py --role dsp` como subproceso.

## PASA

- Antes de que el emisor se conecte, `GET /api/status` → `dsp.connected=false`,
  `radials_received=0`.
- `adapters.dsp.MomentStreamReceiver` acepta la conexión TCP del stub, decodifica los 8 radiales
  del volumen sintético (mismo framing que `spike-fase0/RESULTADO-dsp.md` ya validó standalone) y
  actualiza contadores en tiempo real.
- `GET /api/status` después: `radials_received=8`, `last_radial_status=end_of_volume`,
  `last_volume_number`/`last_elevation_number` reflejan el último radial recibido.
- `connected` vuelve a `false` cuando el emisor cierra la conexión al terminar el volumen — no se
  trata como fallo (`ConnectionError`/`IncompleteReadError` se absorben en
  `MomentStreamReceiver._handle_client`).

## Qué NO prueba este spike

- Un emisor que mantenga la conexión abierta transmitiendo múltiples volúmenes seguidos (el stub
  siempre manda un volumen y cierra) — el receptor sí lo soportaría (bucle `while True` sobre la
  misma conexión), pero no hay emisor de prueba que lo ejercite todavía.
- Reconexión tras una caída a mitad de volumen.
- Los momentos completos no llegan a la MMI — decisión explícita de esta sesión, ver
  `README-dsp-gateway.md`.

## Sigue pendiente dentro de Fase 1

Shell MMI (scaffold Vue3+PrimeVue) e inyección de fallos siguen sin empezar. El streaming real de
momentos a la MMI (vista PPI) es Fase 2/3, no Fase 1.
