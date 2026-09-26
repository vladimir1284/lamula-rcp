# Plan de pendientes cross-repo: DRx y DSP para paridad RVP900/RAVIS

Este documento complementa [`mapeo-parametros-dsp.md`](mapeo-parametros-dsp.md) (no lo repite) y
responde a un encargo distinto: dejar preparado, en `lamula-drx` y `lamula-dsp`, todo lo que hace
falta para que el MMI de `lamula-rcp` pueda llegar a manipular **todas** las configuraciones que
sabemos hoy que le corresponden, más dos prestaciones nuevas pedidas explícitamente (polaridad de
trigger, captura de alta resolución del burst), con la meta de alcanzar paridad completa con
RVP900/RAVIS en el mediano plazo — estamos en etapa temprana de desarrollo, así que el criterio no
es "lo mínimo para P1" sino "todo lo que sabemos que se necesitará".

Fecha: 2026-09-26. Basado en tres investigaciones de solo lectura (sin cambios de código) sobre
`lamula-drx` y `lamula-dsp`, más el contenido ya existente de `mapeo-parametros-dsp.md`.

## Gobernanza de cada repo (verificado, no asumido)

- **`dsp_rcp` (contrato DSP↔RCP):** lo posee `lamula-dsp`. Sin `AGENTS.md`/`CLAUDE.md` propio; la
  regla vive en la cabecera de `contract/schema/dsp_rcp_v0_1.toml:1-9`. Cambios suben
  `version_minor`/`version_major`, tres codegen (`.rs`, `.py`, `.ts`), nunca a mano.
- **`drx_dsp` (contrato DRx↔DSP):** lo posee `lamula-drx`. **Congelado en Z0 (D-08)** — cambios
  exigen ADR + bump de versión + regeneración de ambos lados (C y Rust) vía `tools/gen_*.py`. Regla
  dura en su `AGENTS.md`: "el DRx no habla con el RCP ni con ORPG". No hay proceso `PEND-nn` como en
  `lamula-rcp`; el mecanismo es ADR.
- **`lamula-rcp` (este repo):** no edita ningún contrato ajeno a mano. Vendoriza lo que el DSP
  publique (`contract/vendor/UPSTREAM.toml`), y ya tiene una tarea propia pendiente de
  re-vendorizar a v1.3 (ver `mapeo-parametros-dsp.md`, sección "Tarea pendiente en este
  repositorio"), prerrequisito para todo lo demás.

## Decisión que este documento reabre

`mapeo-parametros-dsp.md` (entrada 15, decidido 2026-09-19) dejó `trigger_delay_0..3` /
`trigger_width_0..3` como **solo lectura** en el proxy DSP↔RCP, con esta advertencia propia: *"F1
desplaza los triggers a la vez, y es su función principal. Con los triggers de solo lectura, F1 se
queda sin la mitad de sus controles... Si el ajuste del temporizado del burst tiene que hacerse
desde el MMI y no en puesta en marcha, hay que reabrir esto para F1 en concreto."*

**Se reabre ahora, por instrucción explícita:** el temporizado de burst (F1) sí debe ser
manipulable desde el MMI, no solo en puesta en marcha. Cambia el reparto de escritura de la
entrada 15 de "delay/width solo lectura" a "delay/width escribibles", igual que ya lo son
`pulse_width_idx` y el divisor de PRF.

## Hallazgo de base: el hueco real está casi todo en `lamula-dsp`, no en `lamula-drx`

Verificado en código (no en los contratos vendorizados, que van un paso atrás):

| Dato | Ya existe en `drx_dsp` (DRx↔DSP) | Expuesto en `dsp_rcp` (DSP↔RCP) hoy |
|---|---|---|
| `trigger_delay_0..3` / `trigger_width_0..3` | Sí, escribibles, `drx_dsp_v0_1.toml:88-131` | No — solo lectura por decisión reabierta arriba |
| Forma de onda I/Q del burst TX (`tx_burst_0`) | Sí, dentro de `ray` (`…toml:192`) | No — el DSP la usa internamente para AFC (`crates/service/src/ray.rs:321,644-672`, `crates/burst/src/afc.rs`) pero no la reexpone |
| Polaridad de trigger | **No existe en ningún lado** — ni bit de contrato ni bit de RTL | No aplica todavía (no hay de dónde) |
| Captura ADC cruda de alta resolución | **No existe en ningún lado** — ni mecanismo de debug/ILA ni buffer | No aplica todavía (no hay de dónde) |

## A. Pendientes para `lamula-dsp` (contrato `dsp_rcp`, dueño del proxy)

Orden recomendado, de más barato/valioso a más caro. Los ítems 1-7 ya estaban en
`mapeo-parametros-dsp.md` § "Falta en el contrato"; se listan aquí solo para mantener un único
plan de ejecución. Los ítems 8-10 son nuevos de este documento.

1. **Prerrequisito, ya en marcha:** re-vendorizar `dsp_rcp` a v1.3 en `lamula-rcp` (tarea propia,
   no del DSP). Sin esto el RCP no habla con el DSP ni para recibir momentos. Bloquea todo lo
   demás transitivamente porque cualquier v1.4+ se apila encima.
2. **Telemetría de AFC/burst en `status`** (mapeo, entrada 1). Coste bajo: 4 `f32` + 1 `u8`,
   aditivo. Desbloquea saber si el receptor está sintonizado — hoy no se puede.
3. **Modos de barrido compuestos** `sweep_mode` (mapeo, entrada 5). El algoritmo ya existe
   (`crates/range/src/split_cut.rs:23`), solo falta el valor de enum. El hueco más barato de toda
   la lista original.
4. **Tipo de transmisor** (mapeo, entrada 16). Ya hay dos algoritmos completos (magnetrón/klistrón)
   detrás de una constante de compilación (`ray.rs:267`); un `u8` de enum los desbloquea a los dos
   sin escribir lógica nueva.
5. **Relay de parámetros DRx ya existentes** (mapeo, entrada 15) — **con el cambio de esta
   sesión**: `pulse_width_idx`, modo de celda y divisor de PRF (ya decididos escribibles) **más
   `trigger_delay_0..3`/`trigger_width_0..3` ahora también escribibles**. Definir en el DSP la
   conversión de unidades de reloj del DRx a microsegundos — recomendado ya en el mapeo: que la
   conversión viva en el DSP, no en el RCP, para no exponer el reloj del DRx.
6. **IF de Tx/Rx y frecuencia de muestreo del DRx** (mapeo, entrada 3). Desbloquea el eje de
   frecuencias real de F2 (`center_freq_hz`/`span_hz` hoy en 0) y da contexto útil a F1/F3.
7. **Selección de canal + promediado en `request_spectrum`** (mapeo, entrada 6). `channel` ya
   viaja en la subida; falta en la petición. Barato, mejora F2 directamente.
8. **Nuevo — mensaje `burst_waveform_frame` + comando `request_burst_waveform`, para F1.** Mismo
   molde que `spectrum_frame`/`request_spectrum` (ya vendorizado y funcionando como patrón). El
   dato ya se calcula hoy dentro del DSP (`ray.rs:321,644-672`) para uso interno del AFC — exponerlo
   es transporte, no algoritmo nuevo. **Con la resolución de rango actual** (bins de 125/250 m, no
   ADC crudo en µs) — ver bloque C para la resolución alta, que depende de DRx y no está resuelta
   todavía. Aun con esa limitación, es mejor que nada: permite a F1 mostrar el pulso capturado
   real, aunque con menos detalle temporal del que pide RVP900 legacy.
9. **Nuevo — relay de polaridad de trigger**, condicionado a que `lamula-drx` agregue el bit
   (bloque C). No hay nada que hacer en DSP hasta que exista el campo del lado DRx; se deja
   reservado el hueco en el mismo mensaje `config` que delay/width para no tener que hacer un
   segundo bump de versión después.
10. **Resto de la lista "Falta en el contrato" de `mapeo-parametros-dsp.md`** (entradas 2, 4, 7-14):
    tabla de rangos válidos, máquina de estados de AFC con histéresis, umbrales hoy horneados como
    constantes, interruptores de algoritmos incondicionales, distinción de vías de recuperación de
    trip múltiple, filtro IIR de clutter en tiempo, mapa de clutter, umbrales por momento con
    máscara `TCF`, selección de subserie alternante. Se mantienen en el orden ya recomendado ahí;
    no se repiten aquí.

**Preguntas ya abiertas en `mapeo-parametros-dsp.md`** que siguen sin responder (7: cinco
parámetros Ravis sin equivalente encontrado; 10: corrección de `polarization_mode` en el enum) — no
son bloqueantes para lo anterior, pero conviene cerrarlas con el equipo DSP en la misma ronda.

## B. Pendientes para `lamula-drx` (contrato `drx_dsp`, y RTL/firmware)

Todo lo de aquí exige ADR propio del repo (contrato congelado en Z0) — no se hace "de paso" dentro
de otro cambio.

11. **Nuevo — bit de polaridad de trigger.** Investigado, **viable y barato en RTL**: `trig_out` en
    `drx_trigger_one_shot.sv:41,53,60,70,76` es registro directo activo-alto sin XOR ni mux de
    inversión hoy; agregar un bit de control antes del pad es cambio trivial de lógica, no de
    diseño físico del driver. Camino completo verificado:
    `drx_trigger_gen.sv:61` → `drx_top.sv:117,196,305` → `drx_zynq_top.sv:57,135` (pad de salida).
    **Lo que sí cuesta:** el proceso, no la lógica — nuevo campo en `drx_dsp` (bump de versión) +
    nuevo registro AXI-Lite (mapa de registros ya en v3, `docs/implementacion/fases.md:738-740`) +
    regenerar ambos lados + ADR. Recomendado: agruparlo con el ítem 12 en el mismo ADR/versión para
    no pagar el ciclo de congelamiento dos veces.
12. **Reconfirmar por escrito (ya lo dice el contrato hoy, pero conviene que quede en el ADR):**
    `trigger_delay_0..3`/`trigger_width_0..3` no cambian de lado DRx — ya son escribibles
    (`drx_dsp_v0_1.toml:88-131`). Lo único nuevo de este bloque es el bit de polaridad del ítem 11.
13. **Nuevo — captura de alta resolución del burst TX (ADC crudo, no bins de rango).**
    **No confirmado que sea viable con presupuesto de recursos conocido — no prometer fecha
    todavía.** Verificado: no existe ningún mecanismo de captura de depuración (`ILA`, "raw
    capture", "debug capture", "adc dump") en `rtl/`, `fw/`, `sim/`, `ip/` hoy — sería un buffer
    BRAM nuevo, construido desde cero. Dato duro de recursos medido (no estimado) en la plataforma
    experimental actual (ZedBoard): DSP48 al 91% con solo 4 canales activos, **"sin margen para
    Z2/Z3/DMA"** (`docs/plataforma/recursos.md:24,47-53`), BRAM también sin margen real (3,6%
    libre). El objetivo real, ZU9, tiene "mucho más margen" según el propio plan
    (`docs/implementacion/fases.md:83-84`) **pero sin `report_utilization` medido en ZU9 en el
    repo hoy** — es proyección, no medición.

    **Acción concreta antes de comprometer este ítem a un sprint:** pedir al equipo de HW de
    `lamula-drx` un `report_utilization` real sobre el target ZU9 con el diseño actual, y a partir
    de ahí dimensionar cuántas muestras de buffer caben. No se puede decidir alcance (N muestras,
    profundidad, cuántos canales simultáneos) sin ese número.

## C. Revisar el registro "No aplica" de `mapeo-parametros-dsp.md` contra la meta de paridad total

`mapeo-parametros-dsp.md` § "No aplica" descarta 65 filas del inventario legacy por seis motivos.
Con "etapa temprana, alcanzar todas las prestaciones RVP900/RAVIS" como meta explícita, hay que
distinguir **motivo de decisión de alcance del plan DSP** (reabrible) de **motivo estructural**
(no reabrible sin rediseñar arquitectura completa). Ninguno de estos se agrega al backlog de A/B
sin decisión de producto explícita — son de otro tamaño:

- **Banco de triggers configurable completo** (6 triggers libres del RVP900, no 4 fijos;
  pretrigger; polarización por trigger; blanking durante medida de ruido) — motivo de **decisión
  de plan** ("trigger generation... owned by the FPGA", `lamula-dsp/docs/dsp-plan.md` §3.2), no de
  imposibilidad física confirmada. Ampliar de 4 pares fijos a banco configurable es un rediseño de
  `drx_trigger_gen.sv`, no un bit — orden de magnitud distinto al ítem 11. **Requiere decisión de
  producto explícita antes de convertirse en ADR** — no se infiere de este documento.
- **Interfaz eléctrica AFC de 25 pines** — no reabrir. Nuestro camino (`Afc`/`nco_phase_inc` por
  TCP) ya es funcionalmente equivalente; perseguir paridad *eléctrica* con un radar que no tiene
  esa interfaz física no aporta nada.
- **Pulso comprimido** (`Tx Waveform`, chirp, F4 completa) — fuera del plan Stage 1 del DSP, ningún
  crate lo implementa. Es generación de forma de onda de transmisión nueva, no un campo de
  contrato. Tratar como iniciativa propia si se decide perseguir, no como ítem de este backlog.
- **Receptor dual de ganancia solapada (WDN)** — rediseño de hardware de recepción, no de
  contrato. Mismo tratamiento que el punto anterior.
- **TAGs / hardware IFD-IFDR** — motivo estructural real (arquitectura distinta: SSI ya calibrado
  en grados vs. formato serie de ángulo RVP900; DRx ya es el equivalente funcional del IFD). No
  reabrir, no aporta.
- **Resuelto en hardware, presentación, formato de series temporales** — no aplica por diseño
  correcto, no por hueco. No reabrir.

**Recomendación:** si "paridad total" incluye banco de triggers libre, pulso comprimido o receptor
WDN, eso es una conversación de roadmap con el equipo de producto y HW de `lamula-drx`/`lamula-dsp`
separada de este plan — cada una es un proyecto propio, no un campo que falta.

## Orden global recomendado

1. Re-vendorizar `dsp_rcp` a v1.3 en `lamula-rcp` (ya pendiente, bloquea todo).
2. `lamula-dsp`: ítems A.2-A.4 (telemetría AFC, sweep modes, tipo de transmisor) — más baratos,
   algoritmo ya existe en los tres.
3. `lamula-dsp` + `lamula-drx` en paralelo: A.5 (relay delay/width escribible, con conversión a
   µs) y B.11 (bit de polaridad) — agrupar en el mismo ciclo de ADR de `drx_dsp` si B.11 sale
   primero, para no reabrir el contrato congelado dos veces por lo mismo.
4. `lamula-dsp`: A.8 (mensaje `burst_waveform_frame`, resolución de rango actual) — desbloquea F1
   en modo verificación con dato real ya, sin esperar al buffer de alta resolución.
5. `lamula-dsp`: A.6-A.7 (IF/muestreo, canal+promedio en espectro) — desbloquea F2/F3.
6. `lamula-drx`: B.13 (buffer de alta resolución) — **condicionado a medir recursos reales en ZU9
   primero**. No se agenda fecha hasta tener ese número.
7. Resto de A.10 (entradas 2,4,7-14 del mapeo original) en el orden ya recomendado ahí.
8. Conversación de roadmap aparte (no en este plan) para banco de triggers libre, pulso
   comprimido, receptor WDN — si se decide perseguir paridad ahí también.
