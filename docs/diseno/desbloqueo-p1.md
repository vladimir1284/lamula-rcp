# Desbloqueo E5 / E7 / F1 / F3 — propuestas verificadas contra DSP y DRx

Complementa [`pendientes-p1.md`](pendientes-p1.md). F2 ya se corrigió ahí (no bloqueado,
`request_spectrum` vendorizado desde commit `6a09656`). Esto cubre las 4 vistas que sí siguen
bloqueadas, con propuesta concreta por vista en vez de "esperar conversación" genérico —
verificado contra `lamula-dsp` y `lamula-drx`, no solo contra el propio doc de RCP.

## E5 — Trigger Setup general (`Mt`)

**Verificado:** `lamula-drx/docs/alcance/decisiones.md:254-271` (D-13, 21-sep-2026) confirma que el
generador de triggers vive **autónomo en fabric DRx** — "el RCP no puede comandar esto en vivo por
1GbE". Arquitectura ya decidida, no hay pregunta abierta ahí. El contrato DSP↔RCP no trae
`delay`/`width` por trigger (solo `trigger_period_cmd_ns`/`trigger_period_meas_ns`, ya cubiertos
por E12) — los "cuatro pares fijos" son constantes de diseño de hardware, no telemetría.

**Propuesta:** no es un pedido de campo de contrato, es una pregunta de hecho única. Pedir al
equipo DSP/DRx los 4 valores numéricos de retardo/anchura fijos (probablemente ya documentados en
algún ICD de hardware fuera de este repo). Con esos 4 números, `TriggerTimingTable` se construye
como tabla estática (spec, no dato en vivo), citando la fuente. No bloquea nada más — se puede
pedir en paralelo mientras se hace E3/E12.

## E7 — Burst Pulse & AFC (`Mb`)

**Verificado:** el lazo AFC está **cerrado y cableado de punta a punta dentro de DSP**
(`lamula-dsp/docs/algorithms/roadmap.md:536-577`, `crates/burst::AfcLoop`, `AfcUpdate`). Pero
`contract/schema/dsp_rcp_v0_1.toml` no tiene un solo campo `afc_*` — confirmado por grep, cero
resultados. No es que DSP no tenga el dato: lo tiene y lo descarta antes del wire.

**Propuesta:** pedido concreto y acotado al proyecto DSP, no "conversación abierta" — exponer en
`status` (o `moment_ray`) los campos que `AfcUpdate` ya produce internamente: `afc_state`
(`Disabled/Manual/NoBurst/Wait/Track/Locked`, mismo enum que ya anticipa el inventario MMI),
`afc_freq_offset_hz`, `afc_amp`. Cambio aditivo (mismo patrón que `burst_window_bins` o
`request_spectrum`: sube `version_minor`, no rompe nada). Como el cómputo ya existe en
`crates/burst`, es exponer un campo ya calculado, no nueva ingeniería de DSP — enmarcar el pedido
así para que no quede en cola larga junto a features nuevas.

## F1 — Burst Pulse Timing (`Pb`)

**Verificado:** mismo límite que E5 (triggers de solo lectura, D-13). El propio inventario ya
señala que con triggers read-only, F1 deja de ser editor y pasa a verificación — y F2 (ya
desbloqueado, ver arriba) va a tener captura de forma de onda del burst vía `spectrum_frame`.

**Propuesta:** esto no necesita una ronda de conversación con DSP — es una decisión de producto
que se puede tomar ya con lo verificado (mismo patrón que D-13 en DRx: decisión directa de
producto, no comité). Fusionar F1 en F2/F3 como una sola vista "Verificación de RF" que muestra
espectro de burst (F2) + timing de trigger de solo lectura (datos de E5) en el mismo panel, en vez
de tres vistas separadas con superficie de datos casi idéntica. Eliminar F1 como entrada separada
del inventario si se acepta la fusión.

## F3 — Receiver Waveforms (`Pr`)

**Verificado:** no hay ninguna mención a captura de forma de onda de receptor (IQ o equivalente a
`spectrum_frame` pero de Rx en vez de burst) en `lamula-dsp/docs/algorithms/roadmap.md` ni en el
resto de `docs/algorithms/` — grep sin resultados. No es que la respuesta esté pendiente, la
respuesta ya está: **no existe y no está en el roadmap de DSP**.

**Propuesta:** no dejar F3 como P1 "a la espera de confirmación" — no hay nada pendiente de
confirmar, ya se confirmó que no existe. Dos caminos, a decidir con el equipo:

1. Degradar F3 a P2/backlog hasta que exista un pedido explícito de captura de forma de onda de Rx
   en el roadmap de DSP (pedido de feature nueva, no de exponer un campo ya calculado — más caro
   que el de E7).
2. Si el valor de F3 es solo diagnóstico y `spectrum_frame` (canal `RX_0`, ya cableado vía F2)
   sirve como aproximación, fusionar F3 en la misma vista "Verificación de RF" de la propuesta F1
   y cerrar F3 como entrada separada.

Recomendado: opción 2 si el diagnóstico de burst/Rx en el mismo canal alcanza; opción 1 solo si
alguien necesita específicamente forma de onda de un canal Rx normal (no burst).

## Resumen de acciones

| Vista | Tipo de bloqueo | Acción | Bloquea a otra vista |
|---|---|---|---|
| E5 | Pregunta de hecho (no de contrato) | Pedir 4 valores fijos a DSP/DRx | — |
| E7 | Campo de contrato ausente, dato ya existe en DSP | Pedir 3 campos `afc_*` aditivos a DSP | — |
| F1 | Decisión de producto, ya resoluble | Fusionar con F2/F3 en "Verificación de RF" | depende de la fusión F3 |
| F3 | Feature ausente confirmada, no pendiente | Degradar a P2 o fusionar en "Verificación de RF" | — |
