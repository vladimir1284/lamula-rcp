# Resultado — spike gateway RCP↔MMI (REST + WS)

Ejecutado 2026-08-19, `python -m adapters.gateway` contra el mismo `radar_emulator` local usado
en `RESULTADO-hal-sim.md`, y `gateway_ws_spike.py` como cliente independiente (REST + WS a la
vez, imitando lo que haría un MMI real).

## PASA

- `GET /api/status`: `hal_connected=true`, `control` y `antenna` con la forma de
  `SystemStatusSnapshot`.
- `POST /api/control`: cambia `ControlAuthority` (D-07) y responde `ControlAuthorityState`;
  reflejado correctamente en `GET /api/status` después.
- `WS /ws`: primer mensaje es `SessionMessage`; siguen `AntennaMessage` a 10 Hz leyendo
  `SimulatedHAL.read_antenna_position()` (dato real del encoder UDP del emulador, no
  sintético) y `HeartbeatMessage` cada segundo.
- Broadcast de `OperatorEventMessage`: un `POST /api/control` desde un cliente HTTP separado
  llega por el WS de otro cliente ya conectado, con el `actor` correcto — confirma el "pipe en
  vivo" extremo a extremo (HAL real → gateway → WS), no solo REST aislado.

## Qué NO prueba este spike

- Múltiples WS conectados a la vez (broadcast solo se probó con un conectado).
- Reconexión de un cliente WS a mitad de sesión — no hay buffer de eventos, un evento emitido
  mientras un cliente estaba desconectado se pierde para ese cliente.
- El stream de DSP/momentos — sigue sin conectarse al gateway; el stub
  (`spike-fase0/dsp_moment_stream_spike.py`) es independiente todavía.
- Ningún test automatizado en CI — este spike depende de un `radar_emulator` real corriendo,
  igual que el resto de Fase 0/1.

## Sigue pendiente dentro de Fase 1

Esqueleto de la MMI (Vue3 + PrimeVue) que consuma este WS/REST para el "primer pipe sim→WS→PPI"
completo (hoy el pipe llega hasta el WS, no hay todavía un PPI real dibujando); conectar el
stream DSP/DRX; inyección de fallos.
