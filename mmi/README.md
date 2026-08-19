# mmi

MMI (Man-Machine Interface) del RCP. Vue 3 + TypeScript + Vite, Pinia + Vue Router,
[shadcn-vue](https://www.shadcn-vue.com/) (Reka UI) + Tailwind v4 — stack fijado en
[D-08](../docs/alcance/decisiones.md#d-08-stack-python-312-fastapi-pydantic-v2-asyncio-vue-3-ts-vite-en-frontend).

Consume el gateway RCP↔MMI (`src/adapters/gateway`, ver
`../spike-fase1/README-gateway.md`) por REST/WS. `src/composables/useGateway.ts` apunta a
`http(s)://127.0.0.1:8000` por defecto — sin empaquetado/despliegue decidido todavía para la MMI
(D-09 solo cubre el backend).

`src/types/mmi.ts` es una copia manual de `core/contracts/mmi.py`: no hay pipeline de codegen
Pydantic→TypeScript (plan §5) todavía. Si el contrato Python cambia, actualizar ese archivo a
mano.

## Desarrollo

```sh
pnpm install
pnpm run dev          # requiere el gateway corriendo en :8000 (ver README-gateway.md)
pnpm run type-check
pnpm run lint
pnpm run test:unit
pnpm run test:e2e     # requiere `pnpm exec playwright install` la primera vez
```
