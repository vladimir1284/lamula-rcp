# Shell MMI (`mmi/`) — Control Center

Último punto de "Lo primero dentro de esta fase": shell de la MMI (Control Center, conectar, log
de mensajes). Vive en `mmi/`, no en `spike-fase1/` — es código de producción, scaffolded con
`create-vue` (Vue 3 + TS + Vite + Pinia + Vue Router + Vitest + Playwright + ESLint/Prettier, D-08)
más `shadcn-vue` para los componentes.

## PEND-RCP-02 revertido durante el scaffold

Se instaló primero PrimeVue (la decisión tomada horas antes en esta misma sesión). Al levantar el
dev server apareció un banner "Invalid PrimeUI License": `primevue@5.0.1` — la última versión al
momento de instalar — se relicenció bajo la marca "PrimeUI" y ya no es MIT libre sin condiciones.
Ver [D-08 en decisiones.md](../docs/alcance/decisiones.md#d-08-stack-python-312-fastapi-pydantic-v2-asyncio-vue-3-ts-vite-en-frontend)
para el detalle y la reversión a shadcn-vue (Reka UI, MIT).

## Qué trae hoy

- `src/composables/useGateway.ts`: cliente del gateway (`src/adapters/gateway`) — REST
  (`fetchStatus`, `setControlMode`) + WS en vivo vía `useWebSocket` de VueUse.
- `src/types/mmi.ts`: copia manual de `core/contracts/mmi.py` — no hay pipeline de codegen
  Pydantic→TypeScript todavía (plan §5, D-08); si el contrato Python cambia, actualizar a mano.
- `src/views/ControlCenterView.vue`: única vista — estado de conexión (WS + DSP), autoridad de
  control con botón tomar/ceder y campo de actor, posición de antena en vivo, log de mensajes
  (últimos 200).
- CORS abierto (`allow_origins=["*"]`) agregado a `src/adapters/gateway/app.py` — necesario para
  que el dev server de Vite (`localhost:5173`) hable con el gateway (`localhost:8000`); marcado
  PEND para revisar si Fase 4 (empaquetado) exige restringir orígenes en el sistema air-gapped.

## Cómo correrlo

Con `radar_emulator` y el gateway corriendo (ver `README-gateway.md`, gateway en el puerto 8000
para que coincida con los defaults hardcodeados en `useGateway.ts`):

```bash
cd mmi
pnpm install
pnpm run dev
```

Ver `RESULTADO-mmi-shell.md` para la verificación en navegador.
