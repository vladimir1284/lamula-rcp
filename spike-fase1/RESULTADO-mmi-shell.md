# Resultado — shell MMI (Control Center) en navegador

Verificado 2026-08-19 con Playwright contra el dev server de Vite (`localhost:5173`) y el
gateway + `radar_emulator` reales corriendo (mismos puertos usados en el resto de Fase 1).

## PASA

- `pnpm run type-check` (`vue-tsc --build`) y `pnpm run lint` (oxlint + eslint) sin errores.
- Página carga sin errores ni warnings de consola (tras corregir CORS y quitar PrimeVue).
- `WS OPEN` visible apenas conecta; llega `SessionMessage` y arranca el stream de
  `AntennaMessage` en vivo (throttle de 10 Hz del gateway) más `HeartbeatMessage` cada segundo —
  el log de mensajes los muestra en tiempo real.
- Botón "Tomar control": clic → `POST /api/control` → `ControlAuthorityState` vuelve `active` con
  el actor del campo de texto → UI se actualiza a "Ceder control" — confirma el pipe completo
  click → REST → gateway → UI, no solo lectura pasiva del WS.
- `GET /api/status` al montar la vista puebla el estado inicial (control, antena, dsp) antes de
  que llegue el primer mensaje WS.

## Hallazgo no relacionado a la MMI en sí — PEND-RCP-02 revertido

`primevue@5.0.1` mostró un banner "Invalid PrimeUI License" en dev: PrimeVue se relicenció a
partir de v5, ya no es MIT libre. Se revirtió a shadcn-vue (Reka UI) en la misma sesión — ver
`README-mmi-shell.md` y D-08 en `decisiones.md`. El costo aceptado: construir a mano los widgets
no estándar (knob de azimut, gauges BITE) que Fase 2 va a necesitar, en vez de tenerlos
batteries-included.

## Qué NO prueba esto

- Ningún componente no estándar (knob, gauge) — Fase 2, no construidos todavía.
- `pnpm run test:unit` / `pnpm run test:e2e` no se corrieron como parte de esta verificación
  (Playwright se usó interactivo vía MCP, no como suite formal); el `e2e/vue.spec.ts` generado
  por el scaffold se actualizó para buscar "Control Center" pero no se ejecutó con
  `playwright test`.
- Tema oscuro/`prefers-color-scheme` — shadcn-vue lo soporta (`darkModeSelector`/`.dark`) pero no
  se ejercitó.
- Persistencia de sesión del lado MMI (recargar la página pierde el log de mensajes, aunque el
  gateway mantenga su propio estado) — consistente con que el gateway tampoco tiene buffer de
  reconexión (ver `RESULTADO-gateway.md`).

## Sigue pendiente

Con esto quedan cubiertos todos los puntos de Fase 1 de `docs/implementacion/fases.md`. Fase 2
(rutinas de control, guarda de seguridad, movimiento de antena, Scan Worksheet, scheduler,
System Visualization/BITE) es el siguiente bloque de trabajo grande.
