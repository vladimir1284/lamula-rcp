# Pendientes P1 — instrucciones de avance

Este documento es el encargo de implementación para las vistas **P1** de
[`inventario-ui.md`](inventario-ui.md) que aún no existen en `mmi/src/views/`, a fecha
2026-09-20. No repite lo que ya está en el inventario (props, componentes propuestos,
comportamiento legacy): asume que se leyó esa vista primero. Lo que añade este documento es
**qué backend real hay detrás de cada una hoy**, **qué falta y de quién depende**, y **el orden
de trabajo recomendado**.

**Lista cubierta:** C5, D6, D8, E1, E2, E3, E4, E5, E6, E7, E11, E12, F1, F2, F3, G1, G2, G3, G4,
G5, G7, G8, I6. (E8, E9, E10, F4, F5, F6, G6 son P2, fuera de este documento.)

## Antes de tocar código

Leer `AGENTS.md` completo si no se hizo ya. Dos reglas de ahí son las que más se van a violar por
descuido en este bloque de trabajo:

- **El contrato RCP↔DSP lo posee el proyecto DSP.** Un campo que "falta" en `contract/vendor/` no
  se añade aquí a mano. Se pide al proyecto DSP, se espera el re-vendorizado, se sube el ancla en
  `contract/vendor/UPSTREAM.toml`.
- **`src/core/` no importa nada de `src/adapters/`.** Cualquier endpoint nuevo de gateway que lea
  hardware pasa por la interfaz `HardwareAbstractionLayer` (`src/core/contracts/hal.py`), nunca
  llama a Modbus directo.

## Diagnóstico de fondo: la familia E depende de un contrato que hoy no tiene la mayoría de estos
campos

Esto no es una nota al pie, es la razón de que el orden de trabajo recomendado empiece por otro
lado. `docs/interfaces/mapeo-parametros-dsp.md` (829 líneas, ya escrito, léase antes de tocar
cualquier vista E) hace el mapeo campo a campo contra `contract/vendor/dsp_rcp_v0_1.py` y contra
el repo `lamula-dsp`. Resultado cuantitativo (§ Resumen cuantitativo del propio documento): de 209
filas, **10 tienen equivalente literal hoy, 46 "difieren"** (existe algo parecido pero no es el
campo — env var de despliegue, unidad distinta, alcance distinto), **82 son funcionalidad que el
contrato de hoy no expone en absoluto**, y el resto no aplica o no es decidible desde este repo.
Verificado en código: `src/core/contracts/dsp.py` solo modela `RadialMoments` (radiales de
momentos) — no hay un solo campo de configuración (umbral, filtro, trigger) en el contrato de
dominio. Esto confirma el mapeo: **hoy no hay dónde escribir la mayoría de los parámetros de
E2–E7**, no es cuestión de tiempo de desarrollo en este repo.

Por tanto, para cada vista de la familia E este documento distingue:

- **Ya expuesto** (`Existe` o `Difiere` en el mapeo) → se puede construir el endpoint de gateway y
  la vista ya, con el campo real o con el más cercano documentado como aproximación (marcar
  `// PEND-nn`).
- **No expuesto** (`Falta`) → la vista se puede *diseñar y maquetar* contra datos simulados en
  `useGateway.mock.ts`, pero **no cablear a datos reales** hasta que el proyecto DSP publique el
  campo. Abrir la pregunta en el canal del proyecto DSP citando la fila exacta del mapeo, no
  reinventar el campo localmente.

## Receta común para una vista nueva de estado/configuración

Igual en las ~20 vistas de este documento salvo excepción marcada. Referencia concreta: la
implementación de B7 (`git show a217461`) y de B4/B5/C2 (`git show d0848ce`).

1. **Contrato de dominio** — añadir el modelo Pydantic en `src/core/contracts/mmi.py` (snapshot de
   lectura) y, si hay escritura, el modelo de comando. No en `dsp.py`/`hal.py` salvo que el dato
   venga realmente de ahí.
2. **Endpoint de gateway** — `src/adapters/gateway/app.py`. Patrón `GET` para snapshot, `POST` para
   `Set` (aplica, volátil) y `POST .../save` para `Save` (persiste), calcado del bloque
   `power-monitor` (líneas 627–660 a fecha de este documento). Si el dato sale del HAL, pasar
   siempre por `hal.read_analog`/`hal.read_digital`, envolver en `try/except` y degradar a
   `stale`/`None`, nunca lanzar 500 por una lectura de campo caída.
3. **Test de endpoint** — `tests/test_<vista>.py`, un test por estado (ok, sin dato, error de
   guardado). Ver `tests/test_power_monitor.py` como plantilla.
4. **Tipo espejo en MMI** — `mmi/src/types/mmi.ts`, mismo nombre de interfaz que el modelo Pydantic
   (regla ya seguida en todo `mmi.ts`, no romperla).
5. **Composable** — función `fetchX`/`setX` en `mmi/src/composables/useGateway.ts` **y** su doble
   en `useGateway.mock.ts` con datos sintéticos plausibles (ver
   `lamula_rcp_diseno_storybook_mock_gateway` en memoria: el doble atrapó un bug real en
   BiteMessagesView — no es un trámite).
6. **Vista** — `mmi/src/views/<Nombre>View.vue` + `.stories.ts`. Ancho de referencia 960×480 px
   (mosaico a un cuarto) y pantalla completa, los dos, per requisito transversal 4 del inventario.
7. **Registro** — añadir la entrada en el registro de vistas de `App.vue` (línea ~50 en adelante,
   `{ id, label, available: true }`) y quitar el placeholder `available: false` si esta vista ya
   estaba ahí como stub.
8. **Verificación real** — Storybook (`pnpm --filter mmi storybook` o el script equivalente del
   repo) contra el mock, y contra el HAL-simulador real si el dato viene de Modbus. No dar por
   completa una vista sin haberla visto en Storybook, per regla general de "probar antes de
   reportar terminado".

Patrones transversales que **no se rediseñan por vista** — si la vista los necesita, reutilizar lo
que ya exista o construirlo una sola vez y enlazarlo desde aquí:

- `SetSaveActions` (Set volátil / Save persistente) — patrón ya usado en B7, replicar tal cual.
- `BlockedActionExplainer` (acción bloqueada por condición física, p. ej. "Save solo con radiación
  apagada") — ya existe el caso de uso en B7, generalizar si la segunda vista lo necesita en vez de
  duplicar.
- `ParameterGroupCard` / `ConditionalFieldGroup` (formulario cuyo layout depende de otro campo) —
  necesario en E4, E6, E7; construir una vez.
- `ConfirmDangerDialog` — ya existe (A3). Reutilizar para toda acción irreversible de esta lista
  (G-family sobre todo).

---

## Familia D — pendientes P1

### D6 — Color Management y Color Composer

**Estado hoy:** no hay tabla de color ni en el backend ni en D2/D3/D4 — las vistas de datos
pintan con una paleta fija en el frontend. Cero contrato de por medio; esto es trabajo 100 %
`mmi/`.

**Pasos:**

1. Definir el espacio de color perceptual (OKLCH) como fuente de verdad para las paletas por
   defecto — decisión ya tomada en el inventario, no reabrir la discusión de RGB vs perceptual.
   Empezar por reflectividad (secuencial) y velocidad (divergente centrada en cero), que son las
   dos que D2/D3/D4 ya usan.
2. `mmi/src/lib/colorScales.ts` (nuevo): función `buildSequentialScale`/`buildDivergentScale` en
   OKLCH → array de stops RGB para el canvas de D2–D4. Verificar contraste con un chequeo de
   deuteranopía/protanopía (simular, no solo mirar).
3. `ColorTableEditor`/`ColorComposer` como vista o panel lateral (D1 ya decidió que las auxiliares
   viven dentro del panel de su vista de datos, no como panel propio) — construir después del
   punto 2, no antes: sin las paletas por defecto no hay nada que editar.
4. `InterpolateAction` interpola en el mismo espacio OKLCH, nunca en RGB — es la razón de ser de
   esta reescritura, no un detalle de implementación.
5. Cablear D2/D3/D4 a las nuevas paletas al final, con story de comparación antes/después en
   Storybook.

**No depende de nada externo.** Candidata a empezar ya si se quiere trabajo P1 sin bloqueos.

### D8 — Scan Parameter Popup

**Estado hoy:** el Scan Worksheet (`ScanWorksheetView.vue`) ya tiene el modelo completo de
parámetros de scan enviados (`src/core/contracts/scan.py`, cableado). D8 es de solo lectura: los
mismos parámetros, congelados junto con el dato que se está viendo.

**Pasos:**

1. Verificar que el snapshot de scan actual (el que ya usa `ScanWorksheetView`) se puede pedir sin
   abrir esa vista — si el endpoint ya devuelve el estado global, D8 solo necesita reusar
   `fetchScanWorksheet` (o el nombre real en `useGateway.ts`, verificar en el fichero) desde un
   popover, no un endpoint nuevo.
2. Componente `Popover`/panel lateral con `KeyValueTable`, invocable desde D2/D3/D4 (menú →
   "parámetros de scan").
3. Congelar el snapshot en el momento de abrir el popover (copia local), no suscribirlo a cambios
   en vivo — la vista es "¿con qué se tomó esto?", no un segundo Scan Worksheet.

**No depende de nada externo.**

### C5 — Sector Blanking Editor

**Estado hoy:** ni el HAL-simulador ni el contrato DSP tienen noción de sectores de blanking; el
mapeo (`mapeo-parametros-dsp.md` §E5) confirma que la generación de triggers, y con ella el
blanking, es del DRx/FPGA y el DSP solo expone 4 pares fijos de retardo/anchura, sin banco
configurable. Antes de construir la vista hay que decidir **dónde vive el estado de los
sectores**: si el blanking real ocurre en el DRx y el DSP no lo expone, el RCP puede como mucho
guardar la configuración deseada (perfil) sin poder aplicarla al hardware todavía.

**Pasos:**

1. Confirmar con el proyecto DSP si existe o se puede pedir un campo de blanking por sector — no
   asumir que aparecerá; documentar la respuesta en `docs/alcance/pendientes.md` con su propio
   `PEND-nn`.
2. Mientras tanto: construir `SectorBlankingEditor` + `AzimuthSectorDial` **contra estado local
   persistido en el RCP** (perfil de sectores en NVRAM propia, no en el DSP), con un badge visible
   de "no aplicado al hardware" si no hay backend real. Es preferible a no construir nada, porque
   el componente gráfico (círculo de azimut con sectores) es reutilizable el día que el DSP
   exponga el campo.
3. Ocho sectores (convención RVP900, no los cuatro de Ravis — ya decidido en el inventario), cada
   uno con `InUse` + rango AZ + rango EL.

**Bloqueado en parte por upstream.** Empezar por el punto 2 (componente + persistencia local) sin
esperar la respuesta del punto 1.

---

## Familia E — Configuración del DSP

**Leer primero `docs/interfaces/mapeo-parametros-dsp.md` completo.** Cada vista de abajo cita sus
filas relevantes; no se repite el detalle campo a campo que ya está ahí.

### E1 — DSP Setup Hub

**Estado:** sin contrato específico; es el índice de E2–E12. Se puede construir en cuanto exista
al menos una vista E real a la que enlazar (recomendado: después de E3, que es la más barata).

**Pasos:** `SetupHubGrid` con un badge "modificado respecto a saved" por grupo — depende de E11
(Config Profiles) para saber qué es "saved" vs "current"; construir E11 primero o en paralelo.
`ExportConfigButton` reutiliza el patrón transversal I6 (Export/Snapshot) — no lo dupliques,
constrúyelo ahí y consume desde aquí.

### E2 — Processing Options (`Mp`)

**Estado:** el mapeo marca la mayoría de este grupo como `Falta` (ver §E2, líneas ~116–159). Los
pocos campos con equivalente son de umbral/corrección, no de este grupo específico.

**Pasos:** maquetar completo contra mock (`useGateway.mock.ts`), sin cablear escritura real todavía.
Sí vale la pena construir ya el componente `TernaryOverrideField` (Never/User/Always) que el
inventario pide — se repite 5 veces en esta vista sola y reaparece en otras.

### E3 — Thresholds Matrix (`Vp`)

**Estado:** la más avanzada de la familia. Del mapeo (§E3):

- `sqi_threshold` → **Existe**, validado 0–1 (`lamula-dsp/crates/rcp-link/src/validate.rs:60-63`).
- `log_threshold` → **Difiere**: existe pero es global, no por momento, sin rango publicado.
- `ccor_threshold` → **Difiere**: equivale a CSR, documentado algebraicamente, también global.

**Pasos:**

1. Confirmar que `contract/vendor/dsp_rcp_v0_1.py` ya trae estos tres campos (debería, según el
   mapeo) — si no, es lo primero a re-vendorizar.
2. Endpoint de solo lectura (la vista es read-only también en el RVP900 — decisión ya tomada de no
   abrir edición). Snapshot con los tres umbrales, marcados **global**, no por fila de la matriz de
   19 parámetros — la matriz completa del legacy no tiene respaldo real; mostrar solo lo que hay y
   dejar el resto de filas com `no disponible`, no inventar valores.
3. `ThresholdMatrix`/`ThresholdCell` con el patrón `TCF` (expresión booleana legible) diferido —
   no hay campo `TCF` real hoy, omitir esa columna en vez de fingirla.

**La vista más barata de construir con datos reales de toda la familia E — empezar por aquí.**

### E4 — Clutter Filters (`Mf`)

**Estado:** `clutter_width_ms` → **Existe** (mapeo §E4, `…toml:316`), pero solo para el modelo
gaussiano (filtros #5–#7 del inventario). Los filtros fijos (#1–#3) y variable (#4) no tienen
campo.

**Pasos:** construir solo el bloque gaussiano contra dato real (`Win`, `Spectrum width`); el resto
del formulario (`ConditionalFieldGroup` por tipo de filtro) se maqueta contra mock y se marca
explícitamente "sin backend" en la UI, no oculto — el operador necesita saber que ese control no
hace nada todavía si lo toca.

### E5 — Trigger Setup general (`Mt`)

**Estado:** confirmado por diseño (no falta de dato, decisión de arquitectura): "cuatro pares fijos
de retardo y anchura, sin polaridad, sin término proporcional al PRT" — no los seis triggers libres
del RVP900 (nota ya en el inventario, §E). El mapeo confirma que el número de triggers de salida
**no aplica** (`drx_dsp_v0_1.rs:133-147`, fijo).

**Pasos:** `TriggerTimingTable` de solo lectura, 4 filas fijas — nada de `Pretrigger`/`polaridad`/
`término PRT` porque no existen en este hardware. `Blank output triggers within AZ/EL sectors`
enlaza a C5 (mismo componente `SectorBlankingEditor`, ver nota del inventario) — construir después
de C5.

### E6 — Trigger Setup por pulse width (`Mt<n>`)

**Estado:** casi todo `Falta` salvo `gate_spacing_m` → **Existe** (mapeo §E6, `…toml:310`, `:126`).

**Pasos:** por ahora, esta vista se reduce en la práctica a mostrar `Range mask spacing` real
dentro de una ficha por ancho de pulso; el resto (tabla de 6 triggers `Start/Width/High`, IF de
Tx/Rx, etc.) es exactamente lo que el mapeo lista en "Falta en el contrato" puntos 3 y 10 — no
construir esos campos como formulario editable todavía. Selector de ancho de pulso persistente sí
se puede construir ya (es navegación, no dato).

### E7 — Burst Pulse & AFC (`Mb`)

**Estado:** el mapeo es explícito (§E7, línea 282): "el ciclo AFC/burst está punta a punta [en
`lamula-dsp`], pero el contrato no expone ni una sola perilla suya". Único hallazgo aprovechable:
`LAMULA_DSP_AFC_AMP_THRESHOLD` existe como **config de despliegue** (variable de entorno del lado
DSP, no del contrato) — no es legible ni escribible desde el RCP.

**Pasos:** esta vista **no tiene nada que cablear a datos reales hoy**. Maquetar completa contra
mock; documentar en la propia vista (comentario de cabecera, convención ya usada en el resto de
`mmi/src/views/`) que depende de que el proyecto DSP publique telemetría de AFC/burst (mapeo
§"Falta en el contrato", puntos 1 y 2). No empezar esta vista hasta que E3/E4 estén hechas — es la
de menor retorno inmediato de toda la familia.

### E11 — Config Profiles

**Estado:** sin contrato de "current vs saved vs factory" en ningún lado del backend hoy — es
concepto nuevo, no legacy directo de RVP900 vía nuestro DSP.

**Pasos:**

1. Decidir alcance real: ¿el RCP guarda sus propios perfiles de lo que sí controla (E3, E4 parcial,
   límites de B7, sectores de C5), o se espera a que exista más superficie editable en E? Recomendado:
   construir ya sobre lo poco editable que hay (B7 `PowerMeasurementLimits` ya tiene su propio
   Set/Save — generalizar ese patrón a "perfil" en vez de reinventar).
2. `ConfigDiffView` (diff entre *current* y *saved*) es la pieza de más valor y la más barata: es
   comparación de JSON, no requiere contrato nuevo.

### E12 — DSP Internal Status (`V` / `Vz`)

**Estado:** la mejor cubierta de la familia después de E3. Del mapeo (§E12): número de celdas,
periodo de trigger (medido vs mandado, con deriva — mejor que el legacy), ruido por canal,
pulsos/rayo, celdas ok/total y espaciado de máscara de rango → todos **Existen** ya en
`status`/`moment_ray`/`config` del contrato de cable.

**Pasos:**

1. Extender `SystemStatusView`/B10 (que ya expone un subconjunto agregado) o crear `E12` como su
   "modo detallado MANT" — decidir si es vista separada o un nivel de detalle de B10; el inventario
   ya dice "versión de mantenimiento de B10".
2. `RawStatusWordsPanel` con decodificación simbólica de bits — patrón que también hace falta en
   I3 (`WFG System Status`); construir el componente `BitmaskStatusList` una vez y reusarlo en las
   dos.
3. Contadores de trigger con reset (`Vz`) → acción con `ConfirmDangerDialog`, no botón directo.

**Segunda vista más barata de construir con dato real, después de E3.**

---

## Familia F — Ajuste asistido por gráfico

**Estado general (mapeo §"Familia F", líneas ~430–466):** F2 tiene captura oportunista de espectro
del burst **cableada** (`spectrum_frame` msg 2, mandato `request_spectrum` value 7 del enum
`Command`), con tres limitaciones verificadas: solo canal `RX_0`, `center_freq_hz`/`span_hz` en 0
por falta de campos de IF/muestreo, sin promediado entre peticiones.

**Corrección 2026-09-24 (verificado en código, ya no bloqueado por contrato):** el enunciado previo
de esta sección decía que `request_spectrum` no estaba en el pin vendorizado y que hacía falta
re-vendorizar coordinando con el proyecto DSP. Falso a fecha de hoy:

- DSP agregó `request_spectrum` al contrato en `beb78b6` ("Wire IF spectrum analyzer into
  rcp-link output, v1.1 -> v1.2"), con `crates/rcp-link/src/session.rs` y
  `crates/service::ray::build_spectrum_frame` ya implementados de punta a punta del lado DSP.
- El pin de este repo (`contract/vendor/UPSTREAM.toml`) ya está en commit `6a09656`
  (2026-09-16, contrato v1.3) — **posterior** a `beb78b6`. El re-vendorizado ya ocurrió.
- Confirmado en `contract/vendor/dsp_rcp_v0_1.py:439`: `REQUEST_SPECTRUM = 7` ya está disponible.
  `SpectrumFrame` también está generado en `mmi/src/contracts/dsp_rcp_v0_1.ts:317-366`.

Lo que sí falta es enteramente trabajo de este repo, sin dependencia externa: cero referencias a
`REQUEST_SPECTRUM`/`SpectrumFrame` en `src/` o en `mmi/src/composables/` hoy — el único mandato
cableado en `src/adapters/dsp/moment_stream_receiver.py:93` es `RESET_COUNTERS`. F2 pasa a la
columna "sin bloqueo externo" del resumen: empezar directo por los pasos 2–4 de abajo.

### F1 — Burst Pulse Timing (`Pb`)

**Estado:** sin contrato — el temporizado de triggers es del DRx/FPGA, no expuesto (mismo límite
que E5/E6). Además, el propio inventario ya advierte: con los triggers de solo lectura (decisión
E5), **F1 deja de ser vista de ajuste y pasa a ser de verificación**.

**Pasos:** replantear el alcance antes de construir: no un editor de temporizado (no hay dónde
escribir), sino una visualización del pulso capturado (reusar lo que F2 ya resuelve para captura
de espectro, si hay una captura de forma de onda equivalente) con los valores de trigger actuales
en modo lectura. Confirmar con el equipo si esta vista sigue teniendo sentido en su forma actual o
se fusiona con F2/F3 en una sola "vista de verificación de RF". **No empezar sin esa conversación**
— es la única de este documento donde el riesgo de construir algo sin uso es alto.

### F2 — Burst Spectra & Matched Filter (`Ps`)

**Estado:** la única de la familia F con dato real parcial. `request_spectrum` ya vendorizado
(ver corrección arriba) — **sin bloqueo externo**, empezar directo por el punto 1.

**Pasos:**

1. Endpoint de gateway que dispare `request_spectrum` y devuelva el último `spectrum_frame`
   recibido — patrón "pedir y esperar" distinto del resto (no es snapshot inmediato); usar el mismo
   patrón de job asíncrono que ya existe para las rutinas de control (`JobActionPanel`,
   `src/core/control_routines/`).
2. Vista con las limitaciones **visibles, no escondidas**: banner "solo RX_0", eje de frecuencia
   sin escala real (`center_freq_hz`/`span_hz` en 0 — mostrar en unidades de bin, no fingir MHz).
3. Los seis estados de AFC (`Disabled/Manual/NoBurst/Wait/Track/Locked`) del inventario **no tienen
   telemetría real** (mapeo, "Falta" punto 2) — omitir ese indicador hasta que exista, no
   simularlo como si fuera dato del radar.

### F3 — Receiver Waveforms (`Pr`)

**Estado:** sin fila específica en el mapeo — depende de si existe una captura de forma de onda de
receptor equivalente a `spectrum_frame`. Verificar con el proyecto DSP si algo así está en su
roadmap antes de estimar esfuerzo.

**Pasos:** no empezar sin esa confirmación. Si no hay captura posible, esta vista queda en el mismo
estado que F1: replantear alcance, no construir contra mock como si fuera a cablearse pronto.

---

## Familia G — Calibración y alineación de receptor/transmisor

**Estado de fondo, verificado en código:** `src/core/contracts/hal.py` no tiene un solo concepto de
calibración (ni `SignalReading` ni `HardwareAbstractionLayer` mencionan cal/zero-check/radar
constant). El catálogo de señales Modbus del HAL-simulador
(`src/adapters/hal_sim/rd100s_signal_catalog.json`, 112 señales) tampoco tiene ningún punto de
calibración, ITSG, zero-check o constante de radar — solo estado/comandos de TX, antena, RX y
sistema. **Toda la familia G es trabajo nuevo de HAL, no solo de MMI.** El único precedente es
`tx.tx_reflected_power_sample`, vendorizado para B7 con `unit_id`/`module` inventados y marcado
`PEND-29` (`git show a217461` — commit de referencia) porque no hay sensor real confirmado
todavía. Cualquier señal nueva de esta familia sigue ese mismo patrón: inventar el punto Modbus,
marcarlo `PEND-nn`, y dejarlo para confirmación con el fabricante/hardware real.

**Precondición de UI común a toda la familia (ya en el inventario, repetirla aquí porque es fácil
de saltarse):** modo de mantenimiento activo (A4) **y** autoridad de control activa (A3) **y**
ACU/LCU en *Remote*. Construir el chequeo de precondiciones **una sola vez** (extender
`PrecheckList`, que ya existe para C4) y reusarlo en G1–G8, no reimplementarlo por vista.

### G1 — Calibration Hub

**Pasos:** índice puro — estado de precondiciones (arriba) + fecha/resultado de última calibración
por tipo (requiere que G2–G8 ya persistan resultado en alguna parte, aunque sea un registro simple
en `src/core/contracts/mmi.py` tipo `CalibrationRecord`). Construir **después** de al menos una de
G2/G4/G5, no antes — si no, el hub no tiene nada que agregar.

### G2 — TX Sampling Adjust

**Estado:** requiere `TX pulse` como tipo de dato del Scan Worksheet (ya existe en el contrato de
scan, verificar en `src/core/contracts/scan.py`) mostrado en ASCOPE (D2, ya existe) — la parte de
lectura cruzada ya está. Lo que falta es el HAL: `TX Start/Stop Sample`, `TX Sample`, `TX
Frequency`, `Commanded LO Freq.`, etc. no están en el catálogo de señales.

**Pasos:** definir los puntos Modbus nuevos con el mismo criterio `PEND-nn` de B7. El patrón de
"aceptación por campo se pinta de verde" (`ParameterField` con estado de aceptación) es
reutilizable en G3/G4 — construirlo una vez aquí.

### G3 — TX Power Calibration

**Estado:** procedimiento guiado (wizard) con entrada manual del operador — no es solo lectura de
HAL, es un flujo con `RoutineStepper`/`WizardStepper`. El patrón ya existe para las rutinas de
control (`src/core/control_routines/`, C4) — **extender ese mismo motor de rutinas**, no crear uno
nuevo. `WarmupTimer` (20 min de radiación antes de empezar) es un requisito duro, no cosmético:
bloquear el botón de inicio, no solo avisar.

### G4 — Single Point Calibration

**Pasos:** dos escenarios (generador interno automático / externo con intervención). Empezar por
el escenario automático — reusa el motor de rutinas de G3. El escenario externo necesita
`OperatorPromptDialog` (nuevo, compartido con G3). **Resultado volátil hasta guardar** — el estado
"obtenido pero no guardado" tiene que ser imposible de ignorar visualmente (banner persistente, no
un toast que desaparece).

### G5 — Zero Check

**Estado:** la única de la familia que **ya se ejecuta automáticamente** según el inventario ("al
arrancar el RCP y luego a intervalos fijos") — verificar si eso ya está implementado en
`src/core/` (buscar en `control_routines/` o `bite/`) antes de asumir que hay que construirlo desde
cero; puede que solo falte la vista sobre un mecanismo que ya corre.

**Pasos:** si el mecanismo periódico existe, esta es la vista más barata de la familia G —
`JobActionPanel` (ya existe) + `NoiseLevelReadout` + `ScheduleInfoRow`. Si no existe, construir
primero el job periódico en `src/core/`, con su propio test, antes de la vista.

### G7 — Radar Constant Parameters

**Estado:** parámetros mayormente estáticos de instalación (pérdidas, ganancia de antena,
wavelength) — candidatos a vivir en configuración del RCP, no en HAL. Solo los de Zero Check se
actualizan solos (depende de G5).

**Pasos:** empezar por el formulario estático (sin dependencia de hardware) — `ParameterGroupCard`
+ persistencia local. `EquationPanel` (mostrar la ecuación de la constante del radar con los
términos resaltados) es trabajo de contenido, no de datos; se puede hacer en paralelo por
cualquiera sin esperar al resto de la familia.

### G8 — Calibration Log

**Pasos:** depende de que G2–G5/G7 emitan eventos de log estructurados. Definir el modelo
`CalibrationLogEntry` en `src/core/contracts/mmi.py` **antes** de empezar cualquier otra vista de
G, para que todas escriban al mismo sitio desde el principio en vez de migrar después.
`LogStream`/`LogToolbar` reutilizan patrón de A5 (Event Log) — no reinventar el componente de
lista con severidad, ya existe en `EventLogPanel`.

**Orden recomendado dentro de G, dado lo anterior:** G8 (modelo de log) → G5 (verificar si ya hay
mecanismo) → G2 → G4 → G3 → G7 (en paralelo, sin dependencias) → G1 (hub, al final).

---

## I6 — Export / Snapshot

**P1 · transversal.** No es una vista, es un servicio compartido. Construir **antes** de tocar
cualquier vista de arriba que lo mencione (D1, D6, G6, I2...) para no reimplementarlo por pieza.

**Pasos:**

1. `ExportMenu`/`SnapshotAction` en `mmi/src/components/` (no en `views/`) — exportar el panel
   activo del mosaico como PNG (usar el mismo canvas que ya renderiza D2/D3/D4 cuando aplique, o
   `html-to-image`/similar para vistas de formulario) y los datos subyacentes como CSV/JSON.
2. `MeasurementFilePicker` para el caso "guardar y recargar un conjunto de resultados" (BiTE ya
   tiene su propio guardar/cargar en B9 — verificar si ese código es reusable aquí en vez de
   duplicarlo).
3. Integrar en `PanelFrame` (A1) como acción de cabecera de panel, disponible en todas las vistas
   por construcción, no añadida vista por vista.

**No depende de nada externo. Candidata a hacerse en paralelo con D6 al principio del bloque P1.**

---

## Resumen: qué se puede hacer ya vs qué espera a otro equipo

| Sin bloqueo externo | Bloqueado o parcial por contrato DSP/HAL ausente |
|---|---|
| D6 Color Management | E2 Processing Options (`Falta` casi todo) |
| D8 Scan Parameter Popup | E5/E6 Trigger Setup (triggers son del DRx/FPGA) |
| I6 Export/Snapshot | E7 Burst Pulse & AFC (`Falta` todo salvo env var no legible) |
| E3 Thresholds Matrix (parcial real) | F1 Burst Pulse Timing (replantear alcance) |
| E12 DSP Internal Status (parcial real) | F3 Receiver Waveforms (confirmar si existe captura) |
| E11 Config Profiles (diff, sin contrato nuevo) | |
| F2 Burst Spectra (`request_spectrum` ya vendorizado, solo falta el endpoint de gateway) | |
| G7 parámetros estáticos | G1–G5, G8 (necesitan HAL nuevo, puntos Modbus inventados `PEND-nn`) |
| C5 Sector Blanking (componente + persistencia local) | C5 aplicación real al hardware (mismo límite que E5) |

**Orden global recomendado:** I6 → D6/D8 (en paralelo) → E3 → E12 → E11 → G8 → G5 → resto de G →
C5 (componente) → E1 → E2/E4/E6 parciales contra mock → F2 (sin bloqueo externo, endpoint de
gateway) → E5/E7/F1/F3 (ver propuestas de desbloqueo en `docs/diseno/desbloqueo-p1.md`).
