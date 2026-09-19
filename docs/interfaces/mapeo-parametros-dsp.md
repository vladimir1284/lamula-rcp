# Mapeo de parámetros: inventario de UI ↔ contrato RCP↔DSP

## Propósito

El [inventario de UI](../diseno/inventario-ui.md) describe las familias **E** (configuración
del DSP, vistas E1–E12) y **F** (ajuste asistido por gráfico, F1–F6) con nombres de parámetro
calcados del manual del **Vaisala RVP900** — menús TTY `Mc`, `Mp`, `Mf`, `Mt`, `Mt<n>`, `Mb`,
`Mz`, `M+` y vistas `V`/`Vz`/`Vp`. El propio inventario avisa de que esa lista documenta *el
volumen y la naturaleza* de lo que hay que configurar en un DSP meteorológico, no nuestro
contrato. Este documento hace el trabajo que faltaba: parámetro a parámetro, decir qué existe
de verdad en el contrato `DSP↔RCP`, qué existe distinto, qué no aplica a nuestro radar y qué
falta.

El destinatario natural de la sección **"Falta en el contrato"** es el proyecto LAMULA DSP,
que es quien posee el contrato. Aquí no se decide nada: se levanta el inventario del hueco.

## Método

Se comparó cada fila de las familias E y F contra cuatro fuentes, en este orden de autoridad:

| Orden | Fuente | Qué aporta |
| --- | --- | --- |
| 1 | `lamula-dsp/contract/schema/dsp_rcp_v0_1.toml` | **Única fuente de verdad del contrato.** De él se generan Rust, Python y TypeScript |
| 2 | `lamula-dsp/crates/` (`service::ray`, `rcp-link`, `burst`, `polarimetry`, `clutter`, `range`…) | Qué está cableado de verdad, y con qué constantes locales donde el contrato no llega |
| 3 | `lamula-dsp/docs/algorithms/` (21 páginas + `roadmap.md`) | Qué algoritmo hay detrás de cada perilla y qué huecos declara cada página |
| 4 | Lado RCP: `contract/vendor/`, `mmi/src/contracts/dsp_rcp_v0_1.ts`, `src/adapters/dsp/`, `src/core/contracts/dsp.py` | Qué llega efectivamente a este repositorio |

Los nombres de campo y de tipo se dejan en su idioma original. Las citas son `fichero:línea`
relativas a la raíz del repositorio correspondiente, indicado con el prefijo `lamula-dsp/` o
`lamula-rcp/`.

### Ancla de versión, y una divergencia que hay que mirar antes de nada

!!! warning "El contrato vendorizado aquí está cuatro versiones por detrás del que posee el DSP"

    | | Versión | `Config` | `Command` | Procedencia |
    | --- | --- | --- | --- | --- |
    | Vendorizado en este repo | **v0.1** | 26 campos, 80 B | 7 mandatos (0–6) | `contract/vendor/UPSTREAM.toml:39-40`, commit `8d7c7ba` del 2026-08-31 |
    | Cabeza de `lamula-dsp` | **v1.3** | 29 campos, 84 B | 8 mandatos (0–7) | `lamula-dsp/contract/schema/dsp_rcp_v0_1.toml:50-51`, commit `4a226af` |

    Los cuatro cambios intermedios, en orden (`git log` de `lamula-dsp` sobre el esquema):

    1. `e91b908` — `polarization_mode` (u8), v0.1 → v0.2. Consume relleno, no crece el mensaje.
    2. `f984850` — `antenna_isolation_db` (f32), v0.2 → **v1.0**. `Config` crece de 80 a 84 B:
       **ruptura**, `version_major` 0 → 1.
    3. `f1e577e` — `burst_window_bins` (u16), v1.0 → v1.1. Aditivo sobre relleno.
    4. `beb78b6` — mandato `request_spectrum` = 7, v1.1 → v1.2. Aditivo.
    5. `4a226af` — `header_flag::SIMULATED_SOURCE` en el byte de banderas de la cabecera,
       v1.2 → v1.3. Aditivo sobre un byte ya reservado; ver la pregunta 8.

    Consecuencia práctica: **el `Config` vendorizado aquí no puede hablar con el DSP de hoy**
    — `version_major` 0 frente a 1, y 80 B frente a 84. Cualquier trabajo de familia E contra
    el pin actual nace roto. Re-vendorizar es prerrequisito, no limpieza.

Este mapeo se hizo **contra v1.2** y sigue vigente contra **v1.3**, que sólo añade una bandera de
cabecera. Se marca en la nota de
cada fila cuando el campo no existe todavía en el pin v0.1 de este repositorio.

### Estado del lado RCP, para que el mapeo no se lea con optimismo

Familia E está **implementada al 0 %** en este repositorio, y el plano de control está
cableado sólo a medias:

- No existe `encode_config` en Python. `Config` no se construye en ningún punto de `src/`;
  `src/adapters/dsp/wire.py` llega hasta `encode_control` (`wire.py:213-216`).
- `encode_control` y `encode_selftest_request` existen pero **sólo los llaman los tests**
  (`tests/test_dsp_wire.py:304` y `:313`). El autotest de enlace que el propio docstring
  llama obligatorio en cada reconexión (`src/adapters/dsp/wire.py:208`) no está implementado.
- `STATUS`, `CAPABILITIES`, `CONFIG_ACK`, `BITE_EVENT` y `SPECTRUM_FRAME` se cuentan y se
  descartan (`src/adapters/dsp/moment_stream_receiver.py:81-84`).
- El contrato TypeScript no lo importa nadie en la MMI; es código muerto en el bundle.

Es decir: los huecos que este documento levanta son de contrato, pero **incluso los campos
que sí existen no tienen consumidor**. Son dos trabajos distintos y conviene no confundirlos.

## Resumen cuantitativo

Unidad de cuenta: **una fila del inventario de UI** — cada entrada con nombre propio en las
tablas de las familias E y F. Los grupos que el inventario presenta como una sola fila
(`AFC hysteresis Inner / Outer`, `TxWave MIN / MAX / actual`) se cuentan como una.

| Diálogo | Existe | Difiere | No aplica | Falta | No decidible | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| E2 `Mp` — Processing Options | 1 | 8 | 7 | 18 | 3 | 37 |
| E3 `Vp` — Thresholds Matrix | 1 | 2 | 1 | 3 | 0 | 7 |
| E4 `Mf` — Clutter Filters | 1 | 3 | 0 | 7 | 3 | 14 |
| E5 `Mt` — Trigger Setup general | 0 | 2 | 8 | 2 | 0 | 12 |
| E6 `Mt<n>` — Trigger por pulse width | 1 | 4 | 12 | 3 | 0 | 20 |
| E7 `Mb` — Burst Pulse & AFC | 0 | 5 | 6 | 17 | 0 | 28 |
| E8 `Mz` — Transmissions & Modulations | 0 | 0 | 10 | 4 | 0 | 14 |
| E9 `Mc` — Top-Level Configuration | 0 | 6 | 5 | 1 | 0 | 12 |
| E10 `M+` — Debug Options | 0 | 1 | 1 | 0 | 0 | 2 |
| E11 — Config Profiles | 0 | 3 | 0 | 4 | 0 | 7 |
| E12 `V`/`Vz` — DSP Internal Status | 6 | 9 | 3 | 12 | 0 | 30 |
| Familia F (F1–F6) | 0 | 3 | 12 | 11 | 0 | 26 |
| **Total** | **10** | **46** | **65** | **82** | **6** | **209** |

Lectura de esos números, separando hecho de inferencia:

- **Hecho.** Sólo 10 parámetros del inventario tienen equivalente literal en el contrato, y 46
  más tienen equivalente con semántica, unidad o granularidad distinta. Los 56 juntos son el
  27 % del inventario.
- **Hecho.** 65 filas (31 %) son específicas del hardware Vaisala —IFDR, temporizado de
  triggers, interfaz eléctrica AFC de 25 bits, TAGs, receptor dual WDN, generación de forma de
  onda de Tx— y no aplican a nuestra arquitectura, en la que esas funciones o viven en el DRx
  o no existen.
- **Hecho.** 82 filas (39 %) son funcionalidad que sí necesitamos y el contrato no expone.
- **Inferencia.** El sesgo del reparto no dice que el contrato esté mal dimensionado: dice que
  el RVP900 es a la vez procesador de señal *y* receptor digital *y* generador de triggers,
  mientras que nosotros partimos esas tres cosas en tres proyectos. Buena parte de lo que aquí
  sale "No aplica" o "Falta" existe en el contrato `DRx↔DSP`, sólo que el RCP no tiene camino
  hasta él (ver la pregunta 1).

---

## E2 — Processing Options (`Mp`)

| Parámetro del inventario | Categoría | Campo en nuestro contrato | Ubicación | Nota |
| --- | --- | --- | --- | --- |
| `Spectral Window` (User/Rect/Hamming/Blackman) | Falta | — | — | `crates/spectral` usa ventana de Hann fija (`lamula-dsp/docs/algorithms/roadmap.md:127`); el analizador de espectro declara la ventana como "configuración local" que no existe (`analizador-espectro-fi.md:59`) |
| `Allow continuous sizes for power spectra` | No aplica | — | — | Nuestra longitud de FFT es `n_pulses` (`estimador-espectral.md:60`); no hay un tamaño de espectro configurable aparte del número de pulsos |
| `R2 Processing` (Never/User/Always) | Falta | — | — | El algoritmo "preciso" `R0,R1,R2` de ancho espectral está documentado como **no implementado**: `pulse_pair_moments` sólo calcula `R0` y `R1` (`pulse-pair-moments.md:91-96`) |
| `Clutter Microsuppression` (Never/User/Always) | No decidible | — | — | Sin equivalente. Ver pregunta 6 |
| `PPP autocorrels from DFTs` (Never/User/Always) | Difiere | `estimator` (u8) | `lamula-dsp/contract/schema/dsp_rcp_v0_1.toml:304`, enum `:484-490` | Nuestra elección es entre dos estimadores distintos (`pulse_pair` / `spectral`), no "calcular pulse-pair vía DFT". No es un override ternario |
| `Unfold Velocity (Vh−Vl)` (Never/User/Always) | Difiere | `dealias_mode` (u8) + `prf_ratio_num`/`prf_ratio_den` (u8) | `…toml:302`, `:307-308`, enum `:463-470` | Vh−Vl es la formulación dual-PRF. Nosotros lo modelamos como enum {`none`,`dual_prf`,`staggered_prt`} más razón de PRF, sin ternario |
| `Process w/ custom trigs` (Never/User/Always) | No aplica | — | — | Los triggers los genera el FPGA/DRx, fuera del alcance del DSP (`lamula-dsp/docs/dsp-plan.md` §3.2) |
| `Use High-SNR 16-bit packed timeseries format` | No aplica | — | — | El `DSP↔RCP` no transporta series temporales: los momentos van en f32 a precisión plena (`…toml:24-27`). El formato de I/Q crudo es del archivo local (`capability_flag.iq_archive` = 128, `…toml:534`), sin cablear (`roadmap.md:847-849`) |
| `Minimum freerunning ray holdoff` (% del dwell) | No decidible | — | — | Ver pregunta 7 |
| `Linearized saturation headroom` (dB) | Falta | — | — | `receiver_gain_db` (`…toml:319`) es ganancia, no margen de saturación. La linealidad de RX está en Stage 2 del plan del DSP (§3.3) |
| `Apply amplitude correction based on Burst/COHO` | Falta | — | — | La corrección de **fase** por burst existe y está cableada (`burst-fase-afc.md:36-42`); la medida de **amplitud** sigue pendiente (`burst-fase-afc.md:3`). No hay interruptor en `config` |
| `Time constant of mean amplitude estimator` (pulsos) | Falta | — | — | La única constante de tiempo que existe es la del lazo de AFC, y por variable de entorno: `LAMULA_DSP_AFC_TAU_S` (`lamula-dsp/crates/service/src/config.rs:55`) |
| `Channel separation` (dB, grados) | No aplica | — | — | Perilla del receptor dual de ganancia solapada (WDN) del RVP900. Nuestros canales son polarimétricos o de burst, todos de la misma ganancia (`lamula-dsp/contract/vendor/drx_dsp_v0_1.rs:207`) |
| `Maximum deviation` (dB, grados) | No aplica | — | — | Ídem |
| `Overlap/Interpolate interval` (dB) | No aplica | — | — | Ídem |
| `Interference Filter` (None/Alg.1/2/3) | Difiere | `rfi_filter` (u8) | `…toml:305` | Interruptor binario 0/1, un solo algoritmo (mediana + anchura angosta, `crates/rfi`). No hay selección entre tres algoritmos |
| `Threshold parameter C1` (dB) | Falta | — | — | `rfi-filtrado.md:56-59` lo declara explícitamente: "el contrato v0.1 no expone umbral de detección; es configuración local del DSP vía TOML". **Ese TOML no existe**: no hay ningún fichero de configuración en `lamula-dsp` fuera del esquema y el pin de vendorizado |
| `Threshold parameter C2` (dB) | Falta | — | — | Ídem |
| `Provide WSR88D legacy BATCH major mode` | Falta | — | — | `sweep_mode` sólo tiene `ppi`/`rhi`/`sector`/`point`/`manual` (`…toml:451-460`), pero el plan del DSP §3.1 compromete Split Cut, Batch Cut y Doppler Cut, y `crates/range/src/split_cut.rs:23` ya implementa `compose_split_cut`. **El algoritmo existe y el contrato no puede pedirlo** |
| `Maximum range to unfold` (km) | Falta | — | — | El desdoblado se aplica a todo el radial; no hay campo de rango máximo |
| `Low-PRF bins range averaged on each side` | Falta | — | — | La corrección por continuidad usa `DUAL_PRF_MAX_FOLD_SEARCH = 3` como constante local (`lamula-dsp/crates/service/src/ray.rs:225`), y es radio de búsqueda de pliegues, no promediado en rango |
| `Overlay power` (Refl/Vel/Width, dB) | Falta | — | — | `range_dealias` es un bit sin parámetros (`…toml:306`); no hay umbrales de solapamiento de trip por momento |
| `T/Z/V/W computed from: H-Xmt / V-Xmt` | Falta | — | — | En modo alternante el cableo fija la subserie copolar H (paridad `ray_flag::TX_POL_V` = 0, `roadmap.md:300-312`) sin campo que lo cambie |
| `T/Z/V/W computed from: Co-Rcv / Cx-Rcv` | Falta | — | — | El canal V es `channel::RX_1` por convención cableada (`roadmap.md:609-613`); no hay campo de selección |
| `Polarimetric Power Params – NoiseCorrected` | Difiere | — (siempre activo) | `lamula-dsp/crates/polarimetry/src/covariance.rs:4-5` | Las potencias por canal se corrigen **siempre** por resta de ruido HS74. No es opcional ni gobernable |
| `Polarimetric Correlations – NoiseCorrected` | Difiere | — (deliberadamente no aplicado) | `lamula-dsp/crates/polarimetry/src/covariance.rs:5-8`, censura en `:89` | La covarianza cruzada `R_hv` **no** resta ruido a propósito (el ruido es independiente entre canales y no sesga el valor esperado); la protección es censura por SNR mínimo (`MIN_SNR_LIN_POLARIMETRIC = 0.05`, `ray.rs:199`). Semántica distinta y sin interruptor |
| `PhiDP – Negate / Offset` (grados) | Difiere | `phidp_offset_deg` (f32, grados) | `…toml:321`; Rust generado `lamula-dsp/contract/generated/dsp_rcp_v0_1.rs:393` | El offset existe tal cual. **`Negate` no**: no hay campo de signo para ΦDP |
| `Polarimetric Attenuation Correction` | Difiere | — (siempre activo sobre CZ) | `roadmap.md:452-474`; `crates/attenuation`; cableo en `ray.rs:1268-1269` | Implementada (Z-PHI, Testud et al. 2000) pero **sin interruptor**: CZ siempre lleva corrección de atenuación. Además `ZPHI_BETA` y `ZPHI_A_COEF_DB_PER_DEG` son constantes locales de banda C (`ray.rs:242`, `:251`) |
| `KDP – LSQ Length` (km) | Falta | — | — | `KDP_WINDOW_GATES = 15` celdas, constante local que el propio doc-comment declara placeholder (`ray.rs:210-216`); `kdp-estimacion.md:66-69` lo registra como hueco de contrato |
| `KDP – LSQ Weights (FIR) Width` (km) | Falta | — | — | No hay ponderación FIR: la ventana es de mínimos cuadrados sin pesos (`crates/kdp`, Ryzhkov & Zrnić 1996) |
| `KDP – Standard Smoothing Factor` | Falta | — | — | Sin equivalente |
| `KDP – Adaptive Smoothing Factor` | Falta | — | — | Sin equivalente. Lo más cercano es el corte por ρHV bajo, también constante local (`RHOHV_THRESHOLD_KDP = 0.8`, `ray.rs:200-208`, marcado como placeholder) |
| `DualRx – Sum H+V Time Series` | No aplica | — | — | Suma de series de los dos receptores del RVP900 dual. No tenemos ese modo; `polarization_mode` elige simultáneo o alternante (`…toml:324`, `:473-481`) |
| `Melting height` (metros) | No aplica | — | — | Entrada de la clasificación de hidrometeoros. El DSP no clasifica: la generación de producto es del ORPG (`dsp-plan.md` §3.2), y `moment_kind` no tiene `HCLASS` (`…toml:379-398`) |
| `Enable noise power based correction of Z0` | Falta | — | — | Existe `noise_floor_dbm` (`…toml:318`), el suelo por canal en `status` (`…toml:202-205`) y `bite_flag.noise_floor_drift` (`…toml:547`), pero **no hay corrección de Z0 basada en ruido** ni interruptor |
| `Z0 – Baseline` (dB/dB) | Falta | — | — | Ídem |
| `Z0 – HiSignal` (dB/dB) | Falta | — | — | Ídem |

---

## E3 — Thresholds Matrix (`Vp`)

El inventario describe **19 momentos × 5 umbrales + una columna de banderas `TCF`**, de sólo
lectura. Nuestro contrato tiene **4 umbrales globales**, no por momento.

| Parámetro del inventario | Categoría | Campo en nuestro contrato | Ubicación | Nota |
| --- | --- | --- | --- | --- |
| Umbral `LOG` (dB) | Difiere | `log_threshold` (f32, dB) | `…toml:315` | Existe, pero **global**, no por momento. Sin rango publicado: `validate.rs:16-20` declara explícitamente que no lo comprueba porque no hay referencia real |
| Umbral `CSR` (dB) | Difiere | `ccor_threshold` (f32, dB) | `…toml:314` | CCOR = `10·log10(P_filtrada/P_total)`; el manual del RVP8 expone la misma cantidad en forma de CSR (`pulse-pair-moments.md:80-83`). Equivalencia algebraica **documentada**, no inferida por el nombre. Global, no por momento |
| Umbral `WSP` (dB) | Falta | — | — | Sin equivalente |
| Umbral `SQI` | Existe | `sqi_threshold` (f32, 0–1) | `…toml:312`; validado en `lamula-dsp/crates/rcp-link/src/validate.rs:60-63` | Único umbral con rango realmente validado, y el motivo está escrito: SQI se define "0 a 1" en la propia enumeración `moment_kind` (`…toml:388`) |
| Umbral `PMI` | No aplica | — | — | Índice propietario de Vaisala. Nuestro par funcional es ρHV + SQI, ya publicados como momentos |
| Columna `TCF` (máscara de banderas por momento) | Falta | — | — | No hay máscara por momento de qué umbral censura qué. Los cuatro umbrales censuran la celda completa (`ruido-y-umbrales.md:41-55`; `ray.rs::gate_quality:481`) |
| Matriz por-momento (19 filas) | Falta | — | — | El contrato no tiene umbrales por momento. Es una diferencia de **dimensionalidad**, no de nombre: 4 escalares frente a 95 celdas |

Dos observaciones que el inventario no recoge:

- El contrato tiene un **quinto** umbral que el inventario no lista: `sig_threshold` (f32, dB,
  `…toml:313`), censura por SNR. Los cuatro son ortogonales a propósito
  (`ruido-y-umbrales.md:41-48`).
- El vocabulario de momentos también difiere. Correspondencia verificada contra
  `…toml:379-398`:

| Inventario (RVP) | Nuestro `moment_kind` | Nota |
| --- | --- | --- |
| `DBT` | `uz` = 0 | Reflectividad sin corregir |
| `DBZ` | `cz` = 1 | Reflectividad corregida. **Semántica ampliada**: nuestro CZ incluye además corrección de atenuación Z-PHI (`roadmap.md:452-474`) |
| `VEL` | `v` = 2 | |
| `WID` | `w` = 3 | |
| `ZDR` | `zdr` = 4 | |
| `PHIDP` | `phidp` = 5 | |
| `KDP` | `kdp` = 6 | |
| `RHOHV` | `rhohv` = 8 | |
| `SQI` | `sqi` = 9 | |
| `SNR` | `sig` = 11 | Mismo concepto, nombre distinto |
| `LDRH` | `ldr` = 7 | Un solo LDR, sin distinguir H de V |
| `DBZA`, `DBTA` | (plegados en `cz`) | Nuestro CZ ya va corregido de atenuación; no hay momento aparte |
| `LDRV`, `RHOH`, `PHIH`, `RHOV`, `PHIV` | — | **Falta**: correlaciones y fases de canal cruzado del modo LDR |
| `HCLASS` | — | **No aplica**: clasificación de hidrometeoros, producto del ORPG |
| — | `ccor` = 10 | Sin equivalente en la lista del inventario |
| — | `i` = 12, `q` = 13 | Componentes crudas, sin equivalente |

---

## E4 — Clutter Filters (`Mf`)

| Parámetro del inventario | Categoría | Campo en nuestro contrato | Ubicación | Nota |
| --- | --- | --- | --- | --- |
| Banco de **7 filtros** seleccionables | Falta | — | — | El contrato tiene **un** filtro por configuración: `clutter_filter` (u8), `…toml:301`. No hay banco, ni asignación por celda, sector o ancho de pulso |
| `Tipo` (0 Fixed / 1 Variable / 3 Gaussian Model) | Difiere | `clutter_filter` enum {`none`,`gmap`,`notch`} | `…toml:493-499` | `Gaussian Model` ≈ `gmap` (ajuste gaussiano e interpolación del hueco, `gmap-clutter-filtering.md:11`), `Fixed` ≈ `notch`. **`Variable` no tiene equivalente** |
| `Win` (ventana del filtro) | Falta | — | — | La ventana del GMAP no es configurable |
| `WidthPts` (puntos de espectro) | Difiere | `clutter_width_ms` (f32, m/s) | `…toml:316` | Misma función, unidad física en vez de puntos de espectro: la anchura se expresa en m/s y el DSP la traduce a bins |
| `EdgePts` | Falta | — | — | Sin equivalente |
| `HuntPts` (sólo tipo Variable) | Falta | — | — | Sin equivalente; no existe el tipo Variable |
| `Spectrum width` (m/s, modelo gaussiano) | Existe | `clutter_width_ms` (f32, m/s) | `…toml:316` | Correspondencia literal, misma unidad |
| `Secondary SQI Threshold Slope/Offset` | Falta | — | — | Un solo `sqi_threshold` escalar, sin pendiente ni offset secundario |
| `Max power mismatch across octants` (dB) | No decidible | — | — | Ver pregunta 6 |
| `High power rejection threshold` (dB) | No decidible | — | — | Ver pregunta 6 |
| `Maximum KEY phase error` (grados) | No decidible | — | — | Ver pregunta 6 |
| Ravis: 15 anchos de filtro IIR con profundidad 30/40/50 dB | Falta | — | — | **No hay filtro IIR en el dominio del tiempo.** `crates/clutter` implementa notch y GMAP, los dos en el dominio espectral. El plan del DSP §3.1 sí compromete "adaptive time-domain IIR filters" |
| Ravis: FFT con 32/64/128/256 pulsos por CPI, o automático | Difiere | `n_pulses` (u16) | `…toml:299` | La longitud de FFT **es** `n_pulses` (`estimador-espectral.md:60`), no un parámetro independiente, y no hay modo automático |
| Ravis: ventana de Hamming opcional | Falta | — | — | Hann fija (`roadmap.md:127`) |
| Ravis: filtro estadístico | No decidible | — | — | Ver pregunta 6 |

Añadido que el inventario sí pide y el contrato no puede dar: **el mapa de clutter fijo**.
`mapas-de-clutter.md:66-69` es explícito — el contrato no transporta el mapa, es un fichero
de configuración local del DSP, y que el RCP lo suba o dispare su regeneración exige un
mensaje nuevo (declarado alcance Stage 2). Añado un hecho verificado que esa página no dice:
**ese fichero de configuración local tampoco existe todavía** en `lamula-dsp`.

---

## E5 — Trigger Setup general (`Mt`)

| Parámetro del inventario | Categoría | Campo en nuestro contrato | Ubicación | Nota |
| --- | --- | --- | --- | --- |
| `Pulse Repetition Frequency` (Hz, 50–20000) | Difiere | `prf_hz` (f32, Hz) | `…toml:311` | El campo existe. **Los límites no**: sólo se valida que sea finito y positivo, más la coherencia PRF × extensión de rango (`validate.rs:77-93`), que es un proxy físico de la decisión D-09 del DRx, no su texto (el propio módulo lo advierte, `validate.rs:78-87`) |
| `Transmit pulse width` (índice) | Falta | — | — | **No existe en `DSP↔RCP`.** Sí existe en `DRx↔DSP` como `pulse_width_idx` (`lamula-dsp/contract/vendor/drx_dsp_v0_1.rs:121`). Con el DSP haciendo de proxy (decisión del 2026-09-19) la ruta está resuelta y esto es hueco de campo: hay que añadirlo a `DSP↔RCP`. Ver entrada 15 de "Falta" |
| `Use external pretrigger` | No aplica | — | — | Generación y temporizado de triggers pertenecen al FPGA/DRx (`dsp-plan.md` §3.2) |
| `PreTrigger active on rising edge` | No aplica | — | — | Ídem |
| `PreTrigger is synchronous with IFD AQ clock` | No aplica | — | — | Ídem, y además no hay IFD |
| `PreTrigger fires the transmitter directly` | No aplica | — | — | Ídem |
| `Number of user-defined output triggers` | No aplica | — | — | El DRx expone cuatro pares fijos `trigger_delay_N`/`trigger_width_N` (`drx_dsp_v0_1.rs:133-147`); no es un número configurable |
| `Number of polarization output controls` | No aplica | — | — | Ídem |
| `Blank output triggers within AZ and EL sectors` + 8 sectores | Falta | — | — | Función operativa real (el inventario la cruza con C5). **Ni `DSP↔RCP` ni el `Config` del DRx vendorizado tienen campos de sector** (`drx_dsp_v0_1.rs:113-152`). Probablemente sea hueco del contrato DRx, no de éste |
| `Blank output triggers during noise measurement` | No aplica | — | — | Temporizado de triggers |
| `Rx-Fixed Triggers` (6 + `P0`, `P1`) | No aplica | — | — | Ídem |
| `2-way (Tx+Rx) total waveguide length` (metros) | Difiere | `start_range_m` (f32, m) + `radar_constant_db` (f32, dB) | `…toml:309`, `:317` | El **efecto** está cubierto: el retardo de guía se absorbe en el rango de la primera celda y sus pérdidas en la constante de radar. La **magnitud física** no se transporta, así que el RCP no puede recalcular ninguna de las dos |

---

## E6 — Trigger Setup por pulse width (`Mt<n>`)

| Parámetro del inventario | Categoría | Campo en nuestro contrato | Ubicación | Nota |
| --- | --- | --- | --- | --- |
| Repetición **por cada ancho de pulso** | Falta | — | — | `Config` es un juego plano único (`…toml:285-327`). No hay noción de perfil por ancho de pulso, ni de comparar o copiar entre anchos |
| Tabla de triggers — `Start` (µs, con término `+ k·PRT`) | No aplica | — | — | El DRx tiene cuatro `trigger_delay_N` en unidades de reloj, sin término proporcional al PRT (`drx_dsp_v0_1.rs:133-139`) |
| Tabla de triggers — `Width` (µs) | No aplica | — | — | `trigger_width_N` del DRx (`drx_dsp_v0_1.rs:141-147`) |
| Tabla de triggers — `High` (polaridad) | No aplica | — | — | Sin equivalente en el DRx |
| `Maximum number of Pulses/Sec` | No aplica | — | — | Guarda de ciclo de trabajo. Confirmado por el product expert que la tarjeta del modulador la evalúa **en hardware** y corta la transmisión ella misma (`lamula-rcp/docs/alcance/pendientes.md:266-275`); el software no la fija |
| `Maximum instantaneous 'PRF'` | No aplica | — | — | Ídem |
| `External pretrigger delay to range zero` (µs) | Difiere | `start_range_m` (f32, m) | `…toml:309` | Lo mismo expresado en el dominio del rango en vez del tiempo |
| `Range mask spacing` (metros) | Existe | `gate_spacing_m` (f32, m) | `…toml:310`, publicado por radial en `:126` | Correspondencia literal, misma unidad |
| `Tx Intermediate Frequency` / `Rx Intermediate Frequency` (MHz) | Falta | — | — | **No hay ningún campo de IF en `DSP↔RCP`.** Consecuencia medible: `spectrum_frame.center_freq_hz` y `span_hz` se emiten en 0 porque no hay de dónde tomarlos (`roadmap.md:653-658`) |
| `FIR-Filter impulse response length` (µs) | No aplica | — | — | El FIR de recepción vive en el FPGA; la decimación nunca llega al DSP (`dsp-plan.md` §3.2) |
| `Burst Freq Estimator – Length / Start` (µs) | Difiere | `burst_window_bins` (u16) | `…toml:326`; consumo en `ray.rs:281-295` | La longitud se expresa en **bins**, no en µs, y **no hay campo de inicio**: se asume el bin 0 (`radial.burst_window(TX_BURST_0, 0, …)`). Campo ausente del pin v0.1 de este repo |
| `FIR-Filter prototype passband width` (MHz) | No aplica | — | — | FIR del DRx |
| `Output control 4-bit pattern` (0–15) | No aplica | — | — | Salidas digitales del IFD |
| `Current noise level` / `Powerup noise level` (dBm; `PriRx`/`SecRx`) | Difiere | `config.noise_floor_dbm` (f32, dBm); `status.noise_floor_dbm_0..3` (f32, dBm) | `…toml:318`; `:202-205` | El de referencia es **uno solo**; el vigente se publica **por canal**. No hay distinción current/powerup ni valores por ancho de pulso |
| `Transmitter phase switch point` (µs) | No aplica | — | — | Temporizado de Tx, FPGA |
| `Polarization switch point for POLAR1 / POLAR2` (µs) | No aplica | — | — | Ídem. La alternancia H/V llega al DSP ya decidida, como el bit `ray_flag::tx_pol_v` del contrato DRx (`roadmap.md:274-278`) |
| `Tx Waveform` (CWPulse/LinFM/NLFM) | No aplica | — | — | No hay compresión de pulso: el plan del DSP §3.1 no la lista, y ningún crate la implementa |
| `Bandwidth of transmit pulse` (MHz) | No aplica | — | — | Ídem |
| `Pulselength of transmit pulse` (µs) | No aplica | — | — | Ídem |
| `Zero offset of transmit pulse` (µs) | No aplica | — | — | Ídem |
| `TxWave MIN / MAX / actual tuning params` | No aplica | — | — | Ídem; y se ajustan desde F4, que tampoco aplica |

---

## E7 — Burst Pulse & AFC (`Mb`)

Éste es el diálogo donde más se nota el hueco: **el lazo de AFC existe y está cableado de
punta a punta** (`roadmap.md:528-572`), pero el contrato no expone ni una sola perilla suya.
Todo lo que lo gobierna son variables de entorno del servicio.

| Parámetro del inventario | Categoría | Campo en nuestro contrato | Ubicación | Nota |
| --- | --- | --- | --- | --- |
| `Tx Intermediate Frequency` (MHz) | Falta | — | — | Ver E6; ningún campo de IF en el contrato |
| `Rx Intermediate Frequency` (MHz) | Falta | — | — | Ídem |
| `IF increases for an approaching target` | Falta | — | — | El signo del Doppler es convención cableada (`pulse-pair-moments.md:61-67` documenta la convención de qué muestra se conjuga); no hay campo |
| `PhaseLock to the burst pulse` | Difiere | `burst_window_bins` (u16) ≠ 0, más `MAGNETRON_TRANSMITTER` | `…toml:326`; `ray.rs:267`, `:282` | La corrección se activa **implícitamente**: si hay ventana de burst y la instalación es de magnetrón. `MAGNETRON_TRANSMITTER` es constante local y su propio doc-comment dice que es así porque el contrato no tiene campo de tipo de transmisor (`ray.rs:253-267`) |
| `Minimum power for valid burst pulse` (dBm) | Difiere | `LAMULA_DSP_AFC_AMP_THRESHOLD` (variable de entorno) | `lamula-dsp/crates/service/src/config.rs:56` | Existe el umbral y hace lo mismo (congelar el lazo y marcar BITE), pero **no es del contrato**: es config de despliegue, en amplitud lineal, no en dBm |
| `Design/Analysis Window` (Rect/Hamming/Blackman) | Falta | — | — | Sin equivalente |
| `Settling time (to 1%) of burst frequency estimator` (s) | Difiere | `LAMULA_DSP_AFC_TAU_S` (variable de entorno) | `lamula-dsp/crates/service/src/config.rs:55` | Constante de tiempo τ de un lazo de primer orden, no tiempo de establecimiento al 1 %, y fuera del contrato |
| `Enable AFC and MFC functions` | Falta | — | — | El lazo se crea incondicionalmente en `START` (`roadmap.md:559-566`). **No hay interruptor, y MFC —control manual de frecuencia— no existe en absoluto** |
| `AFC Servo` (DC Coupled / Motor-Integrator) | No aplica | — | — | Tipo de actuador eléctrico del RVP900. Nuestro actuador es el NCO digital del DRx: mensaje `Afc` con `nco_phase_inc` (u64) (`drx_dsp_v0_1.rs:175`; `burst-fase-afc.md:44-52`) |
| `Wait time before applying AFC` (s) | Falta | — | — | Sin equivalente |
| `AFC hysteresis Inner / Outer` (kHz) | Falta | — | — | `crates/burst::AfcLoop` no implementa histéresis. Sin histéresis no hay estado `Locked`, que es justo el que F2 pide vigilar |
| `AFC outer tolerance during data processing` (kHz) | Falta | — | — | Ídem |
| `AFC feedback slope` | Difiere | `lamula_burst::loop_gain(n_pulses/prf_hz, afc_tau_s)` | `roadmap.md:560-562` | La ganancia se **deriva** de τ y del periodo de radial, no se fija como pendiente en D-Units/kHz. No es un campo |
| `AFC minimum / maximum slew rate` | Falta | — | — | `burst-fase-afc.md:3` y `:54-59` declaran los límites de excursión y de velocidad de cambio como **pendientes de implementar**. Es una salvaguarda de lazo cerrado sobre hardware que hoy no está |
| `AFC format` (Bin/BCD/8B4D) + `ActLow` | No aplica | — | — | Interfaz eléctrica AFC de 25 bits del RVP902/DAFC |
| `AFC uplink protocol` (Off/Normal/PinMap) | No aplica | — | — | Ídem |
| Tabla de 25 pines (`Pin01`…`Pin25` → bit) | No aplica | — | — | Ídem |
| `FAULT status pin` + `ActLow` | No aplica | — | — | Ídem. Nuestro equivalente funcional es el catálogo `bite_flag` (`…toml:538-551`) |
| `Burst frequency increases with increasing AFC voltage` | No aplica | — | — | Ídem: no hay tensión, hay palabra de fase |
| `Enable Burst Pulse Tracking` | Falta | — | — | No hay seguimiento de burst: el lazo corrige frecuencia, no busca la ventana |
| `Enable Time/Freq hunt for missing burst` | Falta | — | — | Ante pérdida de burst el lazo **se congela y emite BITE** (`burst-fase-afc.md:54-59`); no busca |
| `Number of frequency intervals to search` | Falta | — | — | Ídem |
| `Settling time for each frequency hop` (s) | Falta | — | — | Ídem |
| `Automatically hunt immediately after being reset` | Falta | — | — | Ídem |
| `Repeat auto hunt every` (s) | Falta | — | — | Ídem |
| `Enable burst power based correction of Z0` | Falta | — | — | Mismo hueco que el bloque Z0 de E2, y además depende de la medida de amplitud de burst, pendiente (`burst-fase-afc.md:3`) |
| `Simulate burst pulse samples` | Difiere | `crates/simulator::burst::generate_burst` | `roadmap.md:757-762` | El simulador sabe generarlo, pero se elige por variable de entorno al desplegar, no por el contrato |
| `Frequency span of simulated burst` (MHz a MHz) | Difiere | `crates/simulator::burst::drifting_phase_sequence` | `roadmap.md:758-760` | Ídem: existe como API del crate, no como campo |

---

## E8 — Transmissions & Modulations (`Mz`)

| Parámetro del inventario | Categoría | Campo en nuestro contrato | Ubicación | Nota |
| --- | --- | --- | --- | --- |
| `Provide phase modulation of transmitted pulses` | Falta | — | — | `crates/sz864` construye el código y separa trips, contrastado contra oráculo (`roadmap.md:716-721`), pero **sin cablear**: falta que el contrato distinga esta vía de la de fase aleatoria, y falta el canal por el que el excitador recibe el patrón (`roadmap.md:722-725`) |
| `Number of binary angle phase bits to use` | Falta | — | — | Ídem |
| `Phase angle to apply when idle` (grados + hex) | Falta | — | — | Ídem |
| `Modulation` (None/Random/Custom/SZ(8/64)) | Falta | `range_dealias` (u8) como aproximación pobre | `…toml:306` | Hoy un solo bit cubre dos mecanismos distintos —recuperación por fase aleatoria en magnetrón y detección/marcado en coherente— y el RCP no distingue cuál (`roadmap.md:197-205`). SZ(8/64) sería un tercero sin sitio. **El bloqueo de hardware ya está levantado**: confirmado el 2026-09-04 que el excitador de klistrón soporta fase programable pulso a pulso (`roadmap.md:712-713`) |
| `Chan A` (Unused/FixedFreq/TxWaveform) | No aplica | — | — | Generación de forma de onda de Tx en el IFD. El DSP no genera señal de transmisión (`dsp-plan.md` §3.2: el control físico de osciladores y triggers está fuera de alcance) |
| `Chan A – FreeRunning fixed frequency` (MHz) | No aplica | — | — | Ídem |
| `Chan A – Output CW power level` (dBm) | No aplica | — | — | Ídem |
| `Chan A – Apply pulse-to-pulse phase modulation` | No aplica | — | — | Ídem |
| `Chan A – Fixed relative phase offset` (grados) | No aplica | — | — | Ídem |
| `Chan B` (mismas opciones) | No aplica | — | — | Ídem |
| `Chan B – Output power level` (dBm) + `Peak` | No aplica | — | — | Ídem |
| `Chan B – Apply pulse-to-pulse phase modulation` | No aplica | — | — | Ídem |
| `FM Chirp manual spectrum flattener` (%/MHz) | No aplica | — | — | Sin pulso comprimido |

!!! note "Matiz sobre SZ(8/64) que el inventario ya anticipa bien"
    La nota de proyecto del inventario —"el klystron excitador admite fase programable pulso a
    pulso, así que `SZ(8/64)` es viable y no debe descartarse"— está **confirmada** del lado
    DSP (`roadmap.md:712-713`), y el algoritmo ya está implementado y contrastado. Lo que
    falta es contrato, no hardware ni algoritmo. Por eso las cuatro filas de modulación de
    fase van como **Falta** y no como **No aplica**, a diferencia del resto de E8.

---

## E9 — Top-Level Configuration (`Mc`)

| Parámetro del inventario | Categoría | Campo en nuestro contrato | Ubicación | Nota |
| --- | --- | --- | --- | --- |
| `IP address of networked RVP9/IFD` | Difiere | `LAMULA_DSP_DRX_ADDR` (variable de entorno) | `lamula-dsp/crates/service/src/config.rs:50` | Existe el concepto; es configuración de despliegue del servicio, no campo de contrato. El RCP no puede leerlo ni cambiarlo |
| `Maximum ethernet incoming UDP frame length` (250–8192 B) | No aplica | — | — | El tamaño de trama lo fija el contrato `DRx↔DSP` (cabecera fija + carga), no una perilla de red |
| `Receive buffer size for incoming UDP packets` | Falta | — | — | Hay cola acotada con contrapresión y se **observa** (`status.queue_depth`, `…toml:196`; `bite_flag.queue_overflow`, `…toml:543`), pero su tamaño no es gobernable desde el contrato |
| `IFD synthesized system clock` (50–100 MHz) | No aplica | — | — | Reloj del FPGA. Matiz: `LAMULA_DSP_DRX_NCO_FS_HZ` (`config.rs:54`) es una **lectura** de esa frecuencia que el DSP necesita para convertir Hz a palabra de NCO, y está en variable de entorno precisamente porque ningún contrato la expone (`roadmap.md:546-554`) |
| `IFD clock is derived from an external reference` + `External input reference` (MHz) | No aplica | — | — | Ídem, FPGA |
| `Live angle input` (None/SimRVP/SimIFD/TAGs/S-D/RtCtrl) | Difiere | Elección de adaptador de ingesta | `lamula-dsp/crates/ingest/src/{tcp,udp,simulator}.rs`, seleccionado por `LAMULA_DSP_DRX_ADDR` | El concepto existe (real vs simulado) pero se resuelve al desplegar, no en caliente. Los ángulos llegan ya en grados calibrados (`…toml:120-124`), no en cuenta cruda |
| `TAG bits to invert` AZ/EL (máscaras hex de 16 bits) | No aplica | — | — | TAG es el formato serie de ángulo del RVP900. Nuestro encoder es SSI |
| `TAG scale factors` AZ/EL | Difiere | `LAMULA_DSP_SSI_COUNTS_PER_TURN` (variable de entorno) | `lamula-dsp/crates/service/src/config.rs:52` | Equivalente funcional (escala de encoder), pero fuera del contrato y **sin calibración documentada confirmada** — el propio doc-comment lo advierte (`config.rs:1-8`) |
| `TAG offsets` AZ/EL (grados) | Difiere | `LAMULA_DSP_SSI_ZERO_OFFSET_DEG` (variable de entorno) | `lamula-dsp/crates/service/src/config.rs:53` | Ídem |
| `Co-Polarized signal is always on the primary Rx` | Difiere | Convención cableada: canal V = `channel::RX_1` | `roadmap.md:609-613` | Se decidió por bit de `channel_mask`, no por posición, lo cual corrigió un bug real; pero **no hay campo que invierta la convención** |
| `Default receiver mode` (single / legacy WDN / dual channel) | Difiere | `capabilities.n_rx_channels` (u8) + `config.polarization_mode` (u8) | `…toml:280`; `:324`, enum `:473-481` | Cubre el eje que importa (uno o dos canales; simultáneo o alternante) sin modo WDN y **sin exigir reinicio**, que es mejor que el legacy. `polarization_mode` ausente del pin v0.1 de este repo |

!!! warning "Un desfase de documentación en el propio esquema del DSP"
    El enum `polarization_mode` describe `alternating` como "H/V alternante **radial a
    radial**" (`…toml:480`), pero el bit `ray_flag::TX_POL_V` del contrato DRx es **por pulso**,
    y todo el cableo asume alternancia pulso a pulso. El texto quedó de una redacción anterior
    y el propio roadmap lo señala sin corregir (`roadmap.md:403-413`). Si el RCP construye una
    UI a partir del texto del esquema, la etiquetará mal.

---

## E10 — Debug Options (`M+`)

| Parámetro del inventario | Categoría | Campo en nuestro contrato | Ubicación | Nota |
| --- | --- | --- | --- | --- |
| `Noise level for simulated data` (dB) | Difiere | `crates/simulator` (ruido térmico de potencia conocida) | `lamula-dsp/docs/algorithms/simulador-iq.md` | El simulador lo soporta, pero se elige al desplegar; no hay campo en `config`, así que el RCP **no puede saber si está hablando con un simulador**. Ver pregunta 8 |
| `Nyquist sign flip of plotted IF samples` | No aplica | — | — | Perilla de presentación del plot del RVP. En nuestra arquitectura el dibujo es del MMI del RCP |

---

## E11 — Config Profiles

| Parámetro del inventario | Categoría | Campo en nuestro contrato | Ubicación | Nota |
| --- | --- | --- | --- | --- |
| Tres juegos de valores: *current* / *saved* / *factory*, con `S`/`R`/`F` | Falta | — | — | El contrato tiene **una** configuración vigente, identificada por `status.config_seq` (`…toml:192`) y legible con `request_config` (`…toml:444`). No hay juego guardado, ni de fábrica, ni comandos de guardar/restaurar |
| "Los cambios no surten efecto hasta salir (`Q`)" | Difiere | `phase` + `enter_setup`/`start`/`stop` | `…toml:426-433`, `:440-442`; aplicación atómica descrita en `:287-292` | **Nuestro modelo es mejor y más explícito**: configurar y arrancar son fases distintas, el `config` entra entero o se rechaza entero, y uno que llega en marcha se rechaza con `not_in_setup_phase` (`…toml:368`). No hay estado de "edición pendiente" ambiguo |
| "Cada parámetro tiene límites; mostrarlos *antes* de equivocarse" | Difiere | `config_ack.error` | `…toml:235-246`, códigos `:358-377`; validación real en `lamula-dsp/crates/rcp-link/src/validate.rs:38-96` | El contrato da el motivo **a posteriori** (`threshold_out_of_range`, `prf_range_illegal`, `gate_count_illegal`). **No publica ninguna tabla de rangos.** El único umbral con rango real es `sqi_threshold` 0–1; los otros tres se dejan sin comprobar a propósito, porque no hay referencia publicada (`validate.rs:14-24`) |
| Diff entre *current* y *saved* | Falta | — | — | Sin segundo juego, no hay diff posible desde el contrato |
| Exportar / importar configuración | Falta | — | — | `request_config` permite leerla; serializar y reaplicar es trabajo del RCP, pero sin juego guardado no hay a qué compararla |
| Versión de software que guardó los ajustes | Difiere | `selftest_result.version_major`/`version_minor` | `…toml:255-256` | Es la versión del **contrato**, no la del software del DSP. No hay ningún campo de versión de build |
| Aviso de "parámetro nuevo tomó el valor de fábrica tras actualizar" | Falta | — | — | Sin valores de fábrica no hay tal aviso. Lo más cercano sería un `bite_event` de severidad `info` (`…toml:217-232`), que hoy nadie emite por este motivo |

---

## E12 — DSP Internal Status (`V` / `Vz`) y `GPARM`

| Parámetro del inventario | Categoría | Campo en nuestro contrato | Ubicación | Nota |
| --- | --- | --- | --- | --- |
| Procesos y políticas de planificación | Falta | — | — | Sin telemetría de proceso |
| Fechas de compilación de las bibliotecas | Falta | — | — | Sin mensaje de versión de build; `selftest_result` sólo trae versión de contrato (`…toml:255-256`) |
| Uso de TrigRAM | No aplica | — | — | Memoria del IFD |
| Contadores de trigger | Difiere | `status.rays_in`/`rays_out`/`rays_dropped` (u32) | `…toml:193-195` | Cuentan **radiales**, no triggers |
| Temperaturas de chasis y FPGA | Falta | — | — | Sin telemetría de temperatura en `status` |
| Estado de GPS | Falta | — | — | Sin campo. El contrato asume el reloj del DSP ya disciplinado y publica los dos instantes (`…toml:107-108`), pero no dice de qué fuente |
| AFC: nivel, potencia y frecuencia del burst | Falta | — | — | **El lazo corre y nada se publica.** `AfcUpdate::bite` "no se publica en ningún sitio todavía" (`roadmap.md:565-566`). Es el hueco de observabilidad más grande del contrato |
| Modo de receptor | Difiere | `status.n_rx_channels`, `capabilities.n_rx_channels` (u8) | `…toml:189`, `:280` | Número de canales, no "modo" |
| Resultado de diagnósticos | Difiere | `selftest_result` (msg 6), `status.bite_flags` (u32) | `…toml:249-262`; `:191`, catálogo `:538-551` | `selftest_result` es autotest **de enlace**, no diagnóstico interno del procesador |
| `GPARM`: número de celdas | Existe | `moment_ray.n_gates` (u16), `config.n_gates` (u16) | `…toml:112`, `:300` | |
| `GPARM`: periodo de trigger actual | Existe | `status.trigger_period_meas_ns` (u32, ns) frente a `trigger_period_cmd_ns` | `…toml:199-200` | **Mejor que el legacy**: la diferencia entre mandado y medido es la deriva, y hay `bite_flag.trigger_drift` (`…toml:546`) |
| `GPARM`: TAGs | No aplica | — | — | Formato de ángulo del RVP900 |
| `GPARM`: nivel de ruido medido | Existe | `status.noise_floor_dbm_0..3` (f32, dBm); `moment_ray.noise_floor_dbm` | `…toml:202-205`; `:130` | Por canal, que es lo correcto: un único valor promediado sesga ZDR (`ruido-y-umbrales.md:59-64`) |
| `GPARM`: estado latcheado del procesador | Difiere | `status.severity`, `status.last_error`, `status.bite_flags` | `…toml:187-188`, `:191` | **Sin semántica de "latcheado hasta leer"**: `reset_counters` (`…toml:446`) reinicia contadores, no banderas |
| `GPARM`: cuatro *immediate status words* | No aplica | — | — | Registros del hardware IFD |
| `GPARM`: dos registros de diagnóstico | No aplica | — | — | Ídem |
| `GPARM`: pulsos por rayo | Existe | `moment_ray.n_pulses` (u16) | `…toml:113` | |
| `GPARM`: contador de triggers | Difiere | `moment_ray.seq` (u32), `status.rays_in` (u32) | `…toml:106`, `:193` | Por radial, no por trigger |
| `GPARM`: celdas adquiridas y procesadas correctamente | Existe | `status.bins_ok`/`bins_total` (u32); `moment_ray.bins_valid` (u16) | `…toml:197-198`; `:114` | Telemetría de completitud, exigida explícitamente por el plan del DSP §6.1 |
| `GPARM`: periodos mínimos por ancho de pulso | Falta | — | — | Sin noción de ancho de pulso en el contrato |
| `GPARM`: PRT al inicio y al final del último rayo | Difiere | `moment_ray.prf_hz` (f32, Hz) | `…toml:127` | Una sola PRF efectiva (media en dual-PRF). No hay PRT de inicio y de fin, que es justo lo que delata un rayo a caballo de un cambio de PRF |
| `GPARM`: umbrales en uso | Difiere | Los cuatro umbrales, vía `request_config` | `…toml:312-315`, mandato `:444` | Legibles bajo petición, **no publicados en `status`** |
| `GPARM`: ruido I²/Q² | Difiere | `status.dc_offset_i_0..3`, `dc_offset_q_0..3` (f32) | `…toml:206-213` | Offset de continua por componente, no potencia de ruido por componente. Cantidades distintas |
| `GPARM`: desviación estándar del ruido LOG | Falta | — | — | Sin equivalente |
| `GPARM`: relación de ruido H/V | Falta | — (derivable) | — | Se puede calcular de `noise_floor_dbm_0` menos `noise_floor_dbm_1` (`…toml:202-203`). **Inferencia**: el contrato no declara en ningún sitio que el canal 0 sea H y el 1 sea V; esa correspondencia se deduce de `channel::RX_0`/`RX_1` y del cableo (`roadmap.md:609-613`), no de un campo |
| `GPARM`: valor de control AFC/MFC | Falta | — | — | Mismo hueco que "AFC: nivel, potencia y frecuencia" |
| `GPARM`: selección del filtro de interferencia | Difiere | `config.rfi_filter` vía `request_config` | `…toml:305`, mandato `:444` | Legible, no publicado en `status` |
| `GPARM`: constantes del filtro de interferencia | Falta | — | — | Internas del crate, sin campo (`rfi-filtrado.md:56-59`) |
| `GPARM`: slew de seguimiento del burst | Falta | — | — | No hay seguimiento de burst (ver E7) |
| `GPARM`: espaciado de la máscara de rango | Existe | `config.gate_spacing_m`, `moment_ray.gate_spacing_m` (f32, m) | `…toml:310`, `:126` | |

---

## Familia F — Ajuste asistido por gráfico

La familia F es, en el legacy, un osciloscopio virtual alimentado por el propio DSP. Nuestro
contrato tiene **un solo mensaje de ese género**: `spectrum_frame` (`…toml:154-171`). Todo lo
demás —muestras de burst en el tiempo, formas de onda del receptor, diagrama de ambigüedad—
no tiene camino.

| Vista / parámetro | Categoría | Campo en nuestro contrato | Ubicación | Nota |
| --- | --- | --- | --- | --- |
| **F1** — plot de muestras del burst en el tiempo | Falta | — | — | No hay mensaje de muestras I/Q crudas del burst hacia el RCP. `spectrum_frame` da espectro, no tiempo |
| F1 — `I/i` longitud de respuesta impulsional del FIR | No aplica | — | — | FIR del DRx |
| F1 — `A/a`, `S/s` apertura e inicio de la ventana de AFC | Difiere | `burst_window_bins` (u16) | `…toml:326` | Sólo apertura, en bins, y sin inicio (se asume bin 0, `ray.rs:281-295`) |
| F1 — `L/l`, `R/r` desplazar todos los triggers | No aplica | — | — | Triggers del DRx |
| F1 — `T/t` span del plot, `Z/z` zoom | No aplica | — | — | Estado de presentación; en nuestra arquitectura es del MMI |
| F1 — `B/b` desactivar/reactivar seguimiento de burst | Falta | — | — | No hay seguimiento de burst que desactivar (ver E7) |
| F1 — `+` buscar el burst perdido | Falta | — | — | Ídem |
| F1 — línea de estado: `Freq`, `Pwr`, `DC`, `BPT` | Falta | — | — | `DC` tiene equivalente parcial en `status.dc_offset_i/q_0..3` (`…toml:206-213`), pero **no por radial ni ligado al burst**; `Freq`/`Pwr`/`BPT` del burst no se publican en ningún sitio (`roadmap.md:565-566`) |
| **F2** — espectro del burst | Difiere | `spectrum_frame` (msg 2) + mandato `request_spectrum` (7) | `…toml:154-171`; `:447` | **Existe la captura oportunista**, cableada (`roadmap.md:619-651`). Limitaciones verificadas: sólo canal `RX_0` (`roadmap.md:645-647`), `center_freq_hz` y `span_hz` **en 0** por falta de campos de IF/muestreo (`roadmap.md:653-658`), sin promediado entre peticiones (`roadmap.md:659-663`). **El mandato `request_spectrum` no existe en el pin v0.1 de este repo** |
| F2 — diseño del filtro adaptado (`N/n`, `W/w`, `#`, `$`) | No aplica | — | — | El filtro adaptado es del DRx/FPGA |
| F2 — `U/u`, `D/d`, `=` control manual de frecuencia (MFC) | Falta | — | — | MFC no existe (ver E7) |
| F2 — `V/v` número de espectros promediados (1–25) | Falta | — | — | Sin promediado entre peticiones (`roadmap.md:659-663`); la ventana y el número de promedios son "configuración local" sin campo (`analizador-espectro-fi.md:59`) |
| F2 — `%` alternar entre receptores | Falta | — | — | `spectrum_frame.channel` (u8) **existe en el mensaje de subida** (`…toml:164`), pero el contrato no tiene campo en la petición para elegirlo y el cableo sólo atiende `RX_0` (`roadmap.md:645-647`) |
| F2 — línea de estado: `BW`, `DCGain`, `Loss` | No aplica | — | — | Propiedades del filtro adaptado del DRx |
| F2 — **los seis estados del AFC** (`Disabled`/`Manual`/`NoBurst`/`Wait`/`Track`/`Locked`) | Falta | — | — | La máquina de estados no existe: `AfcLoop` congela por amplitud y nada más (`burst-fase-afc.md:54-59`), y **nada de su estado llega al contrato**. Sin histéresis no hay `Locked`, que es exactamente el estado en el que el inventario dice que hay que adquirir |
| F2 — patrón de bits codificado del AFC digital | No aplica | — | — | Interfaz eléctrica de 25 bits |
| **F3** — formas de onda del receptor | Falta | — | — | No hay mensaje de muestras I/Q de recepción hacia el RCP. `capability_flag.iq_archive` = 128 (`…toml:534`) es volcado **local** a disco y sigue sin cablear (`roadmap.md:847-849`) |
| F3 — `L/l`,`R/r`,`T/t` ventana de muestras IF | Falta | — | — | Ídem |
| F3 — `V/v` promediado, `Z/z` zoom | No aplica | — | — | Presentación |
| F3 — línea de estado: `Total`, `Filtered`, `MidSamp` | Falta | — | — | Ídem F3 en general |
| **F4** — diagrama de ambigüedad de la forma de onda Tx | No aplica | — | — | Sólo aplica con pulso comprimido, que no está en alcance |
| F4 — `S/s`,`L/l`,`N/n`,`W/w`, tuning `1`/`2`/`3`, `$` | No aplica | — | — | Ídem |
| F4 — línea de estado: `PSL`, `ISL`, `TxLoss`, `RxLoss` | No aplica | — | — | Ídem. Nota: `TxLoss` alimenta la constante de radar (→ G7), que en nuestro contrato llega ya resuelta como `radar_constant_db` (`…toml:317`) |
| **F5** — AFC Test / Pin Map (25 bits, *walking ones*) | No aplica | — | — | Verificación eléctrica de una interfaz que no tenemos |
| **F6** — Display Test Pattern | No aplica | — | — | Comprobación de render del MMI; nada que ver con el contrato |

---

## Falta en el contrato

Consolidado y ordenado por importancia operativa. Ésta es la lista que hay que llevar al
proyecto LAMULA DSP. Cada entrada dice qué se pide y por qué, con la evidencia de que el
algoritmo ya existe cuando así es — esos son los baratos.

!!! note "Decisión de arquitectura (2026-09-19): el DSP hace de proxy"

    La pregunta 1 de este documento —cómo llega el RCP a los parámetros que hoy posee el
    contrato `DRx↔DSP`— está resuelta: **el DSP actúa de proxy.** El RCP no habla DRx
    directamente y no habrá `src/adapters/drx/`; el RCP habla un único protocolo, `DSP↔RCP`,
    y el DSP retransmite hacia el DRx lo que corresponda.

    Lo que esa decisión cambia en este mapeo:

    - **Las vistas E5 y E6 siguen dentro de alcance.** Estaban pendientes de esta respuesta.
    - **Lo que era "hueco de ruta" pasa a ser "hueco de campo"**, y por tanto entra en esta
      lista: `pulse_width_idx`, el modo de celda, el divisor de PRF y los cuatro pares
      `trigger_delay_N`/`trigger_width_N` existen en `DRx↔DSP`
      (`lamula-dsp/contract/vendor/drx_dsp_v0_1.rs:113-152`) y ahora necesitan representación
      en `DSP↔RCP`. Es la entrada 15 de abajo.
    - **No convierte en accesible lo que el DRx tampoco tiene.** El blanking por sector no
      existe en el `Config` del DRx, así que sigue siendo hueco del contrato DRx y el proxy no
      lo arregla. Lo mismo con todo lo marcado "No aplica" por pertenecer al FPGA: proxy
      significa camino, no funcionalidad nueva.
    - **Refuerza la pregunta 9** (ruta de los mensajes de subida y sentido de la conexión): si
      el DSP retransmite mandatos hacia el DRx, el plano de control `RCP → DSP` deja de ser
      opcional y se vuelve el camino único. Hay que decidir si comparte socket con el flujo de
      momentos.
    - **El DSP gana responsabilidad de validación.** Al ser el único que ve los dos contratos,
      es quien puede rechazar una combinación inválida antes de que llegue al DRx, y quien
      debe reportar al RCP por qué la rechazó. Sin eso, el MMI no puede explicar un fallo de
      configuración al operador.

### 1. Telemetría de AFC y burst en `status` (o mensaje propio)

**Qué falta:** frecuencia medida del burst, potencia del burst, valor de control del AFC,
estado del lazo, y el `bite` de congelamiento.

**Por qué es lo primero:** el lazo está cableado de punta a punta y funcionando
(`roadmap.md:528-572`), pero **su salida no sale del proceso**. `AfcUpdate::bite` ante pérdida
de burst "no se publica en ningún sitio todavía" (`roadmap.md:565-566`). Hoy el operador no
puede saber si el receptor está sintonizado. Con magnetrón eso no es un lujo: sin AFC, la
velocidad no significa nada (`pulse-pair-moments.md:24-29`).

**Coste estimado:** bajo. Cuatro `f32` y un `u8` en `status`, aditivo si hay relleno.

### 2. Máquina de estados del AFC con histéresis, y sus parámetros

**Qué falta:** `AFC hysteresis Inner/Outer`, `AFC outer tolerance during data processing`,
`Wait time before applying AFC`, límites de excursión y de velocidad de cambio
(`AFC min/max slew rate`), y el estado resultante (`Disabled`/`Manual`/`NoBurst`/`Wait`/
`Track`/`Locked`).

**Por qué:** es a la vez hueco de algoritmo y de contrato. `burst-fase-afc.md:3` y `:54-59`
declaran los límites como pendientes, y son las salvaguardas estándar de cualquier lazo
cerrado que gobierna hardware. Sin `Locked` no hay criterio de "ya se puede adquirir", que es
la pregunta operativa que F2 existe para responder.

### 3. IF de transmisión y recepción, y frecuencia de muestreo del DRx

**Qué falta:** `Tx Intermediate Frequency`, `Rx Intermediate Frequency`, frecuencia de
referencia del NCO y anchura del acumulador de fase.

**Por qué:** el síntoma es medible hoy — `spectrum_frame.center_freq_hz` y `span_hz` salen en
**0** porque no hay de dónde tomarlos (`roadmap.md:653-658`). El eje de frecuencias del
analizador de espectro es inútil sin esto. Además `LAMULA_DSP_DRX_NCO_FS_HZ` y
`LAMULA_DSP_DRX_NCO_WORD_BITS` son variables de entorno obligatorias sin valor por defecto
precisamente porque ningún contrato las expone (`config.rs:8-15`, `roadmap.md:546-554`), lo
que bloquea verificar la conversión Hz→palabra de NCO contra hardware real.

### 4. Tabla de rangos válidos por parámetro, publicada por el contrato

**Qué falta:** un mecanismo para que el RCP conozca los límites **antes** de mandar un
`config`, no después.

**Por qué:** hoy el único umbral con rango real es `sqi_threshold` 0–1, y el propio validador
declara que deja los otros tres sin comprobar porque no hay referencia publicada
(`validate.rs:14-24`). El inventario pide explícitamente mostrar el rango antes de que el
usuario se equivoque; con el contrato de hoy, una UI de familia E sólo puede mandar y rezar.
`capabilities` (`…toml:267-283`) es el sitio natural: ya lleva `max_gates` y `max_pulses`.

### 5. Modos de barrido compuestos: Split Cut, Batch Cut, Doppler Cut

**Qué falta:** valores en el enum `sweep_mode` (`…toml:451-460`).

**Por qué:** el plan del DSP §3.1 los compromete explícitamente y
`crates/range/src/split_cut.rs:23` ya implementa `compose_split_cut`. **El algoritmo existe y
el contrato no puede pedirlo.** Es el hueco más barato de cerrar de toda la lista.

### 6. Selección de canal en la petición de espectro, y promediado

**Qué falta:** un campo de canal (y de número de promedios, y de ventana) en el mandato
`request_spectrum`.

**Por qué:** `spectrum_frame.channel` ya existe en el mensaje de subida (`…toml:164`) y el
propio algoritmo dice que comparar las trazas de los dos canales "es en sí misma un
diagnóstico de apareamiento" (`analizador-espectro-fi.md:112-115`), pero el cableo sólo atiende
`RX_0` porque el contrato no tiene con qué pedir otro (`roadmap.md:645-647`).

### 7. Umbrales y parámetros de algoritmo hoy horneados como constantes locales

Cada uno lleva en `crates/service/src/ray.rs` un doc-comment que dice, literalmente, que es un
placeholder hasta que exista campo en `Config`:

| Constante | Valor | Ubicación | Qué gobierna |
| --- | --- | --- | --- |
| `KDP_WINDOW_GATES` | 15 celdas | `ray.rs:216` | Longitud de la ventana de ajuste de KDP (`kdp-estimacion.md:66-69`) |
| `RHOHV_THRESHOLD_KDP` | 0.8 | `ray.rs:208` | Censura de ΦDP por ρHV bajo. El doc-comment avisa: "convención habitual, **no un valor que este repositorio documente**" |
| `MIN_SNR_LIN_POLARIMETRIC` | 0.05 | `ray.rs:199` | Censura de ZDR/ρHV/ΦDP por SNR |
| `GMAP_SIGNAL_MARGIN` | 3.0 dB | `ray.rs:233` | Selección de bins de señal para el ajuste gaussiano |
| `DUAL_PRF_MAX_FOLD_SEARCH` | 3 | `ray.rs:225` | Radio de búsqueda de pliegues en la corrección por continuidad |
| `ZPHI_BETA` | 0.64884 | `ray.rs:242` | Exponente de la corrección de atenuación |
| `ZPHI_A_COEF_DB_PER_DEG` | 0.08 | `ray.rs:251` | Coeficiente de atenuación, **banda C fijada por defecto** |
| `MAGNETRON_TRANSMITTER` | `true` | `ray.rs:267` | Tipo de transmisor de la instalación |
| Umbral de detección de RFI | (interno al crate) | `rfi-filtrado.md:56-59` | `Threshold parameter C1`/`C2` del inventario |

Los dos últimos son de otra naturaleza y merecen tratarse aparte: **`MAGNETRON_TRANSMITTER` y
la banda del radar son propiedades de la instalación, no ajustes de operador.** Un campo de
tipo de transmisor y otro de banda (o derivar la banda de `wavelength_m`, que ya está en el
contrato, `…toml:323`) cierran los dos de una vez y desbloquean además el punto 9.

### 8. Interruptores para algoritmos hoy incondicionales

- **Corrección de atenuación Z-PHI**: siempre activa sobre CZ, sin interruptor
  (`roadmap.md:452-474`). El inventario la pide como `Polarimetric Attenuation Correction`.
- **Corrección de fase por burst**: se activa implícitamente con `burst_window_bins != 0` más
  `MAGNETRON_TRANSMITTER` (`ray.rs:267`, `:282`). El inventario la pide como
  `PhaseLock to the burst pulse`.
- **Resta de ruido en potencias polarimétricas**: siempre activa
  (`crates/polarimetry/src/covariance.rs:4-5`).

Un interruptor no es cosmética: sin él, el operador no puede aislar si un artefacto viene del
algoritmo o del dato, que es el flujo de diagnóstico normal.

### 9. Distinguir las tres vías de recuperación de trip múltiple

Hoy un único bit `range_dealias` (`…toml:306`) cubre dos mecanismos distintos —recuperación
real por fase aleatoria en magnetrón, y sólo detección y marcado en transmisor coherente— y
el RCP no distingue cuál está pasando (`roadmap.md:197-205`). SZ(8/64) sería una tercera vía,
ya implementada y contrastada en `crates/sz864` (`roadmap.md:716-721`), **sin sitio en el
contrato**, y sin el canal por el que el excitador recibiría el patrón de fase
(`roadmap.md:722-725`). El bloqueo de hardware ya no existe: el klistrón admite fase
programable pulso a pulso (`roadmap.md:712-713`).

### 10. Filtro IIR de clutter en el dominio del tiempo

`clutter_filter` ofrece `none`/`gmap`/`notch`, los dos últimos en el dominio espectral
(`…toml:493-499`). El plan del DSP §3.1 compromete además "adaptive time-domain IIR filters",
y el catálogo Ravis del inventario pide 15 anchos con profundidades de 30/40/50 dB. No existe
ni el algoritmo ni el campo.

### 11. Mapa de clutter: subida y regeneración desde el RCP

`mapas-de-clutter.md:66-69` declara que el contrato no transporta el mapa y que hacerlo exige
un mensaje nuevo (alcance Stage 2). Añado el hecho verificado de que **el fichero de
configuración local que esa página supone tampoco existe** en `lamula-dsp` — no hay ningún
`.toml` de configuración en el repositorio.

### 12. Umbrales de censura por momento, y máscara `TCF`

Nuestros cuatro umbrales son globales y censuran la celda completa (`ray.rs::gate_quality:481`).
El inventario pide 19 momentos × 5 umbrales más una máscara de qué umbral afecta a qué
momento. Es una diferencia de dimensionalidad, y la decisión de si la queremos es de producto,
no de implementación. La marco como falta porque hoy **no se puede publicar velocidad con un
umbral y reflectividad con otro**, que es un requisito operativo corriente.

### 13. Selección de subserie en modo alternante

`T/Z/V/W computed from H-Xmt / V-Xmt` y `Co-Rcv / Cx-Rcv` no tienen campo: el cableo fija la
subserie copolar H y el canal V en `RX_1` (`roadmap.md:300-312`, `:609-613`). Prioridad menor
que las anteriores, pero conviene registrarlo antes de que la convención se vuelva folclore.

### 14. Resto, por completitud

Sin desarrollar porque su prioridad es claramente menor, pero para que no se pierdan:
algoritmo `R0,R1,R2` de ancho espectral (`pulse-pair-moments.md:91-96`); ventana espectral
configurable; `PhiDP – Negate`; corrección de Z0 basada en ruido o en potencia de burst;
`Linearized saturation headroom`; corrección de amplitud por burst/COHO
(`burst-fase-afc.md:3`); tamaño de la cola de ingesta; momentos `LDRV`/`RHOH`/`PHIH`/`RHOV`/
`PHIV` del modo LDR; temperaturas y estado de GPS en `status`; versión de build del DSP;
blanking de triggers por sector (probablemente hueco del contrato DRx); y el juego
*saved*/*factory* de configuración con su diff.

### 15. Parámetros del DRx que el proxy tiene que reexponer

Consecuencia directa de la decisión de arriba. Existen ya en `DRx↔DSP` y hay que darles
representación en `DSP↔RCP` para que el MMI pueda leerlos y escribirlos:

| Parámetro | Origen en `DRx↔DSP` | Vista que lo necesita |
| --- | --- | --- |
| `pulse_width_idx` | `drx_dsp_v0_1.rs:121` | E5, E6, y el selector de ancho de pulso que E6 y F1–F3 comparten |
| Modo de celda | `drx_dsp_v0_1.rs:113-152` | E6 |
| Divisor de PRF | `drx_dsp_v0_1.rs:113-152` | E5 |
| `trigger_delay_0..3` / `trigger_width_0..3` | `drx_dsp_v0_1.rs:133-147` | E6, en su forma real: **cuatro pares fijos, sin polaridad ni término proporcional al PRT**, no los seis triggers libres del RVP900 |

**Escritura: decidido (2026-09-19), reparto mixto.** El ancho de pulso y el divisor de PRF son
**escribibles** —son decisiones operativas normales, y el ancho de pulso ya aparece en el Scan
Worksheet (C3)—. Los cuatro pares de retardo y anchura de trigger son **de solo lectura**: son
alineación de puesta en marcha, se miran para diagnosticar y no se tocan en operación. E5 y E6
quedan, por tanto, como formulario parcial con una sección de estado, no como formulario
completo.

Esa decisión tiene un flanco que hay que mirar: **F1 (`Pb`, temporizado del burst) desplaza los
triggers a la vez**, y es su función principal. Con los triggers de solo lectura, F1 se queda sin
la mitad de sus controles y pasa a ser una vista de verificación, no de ajuste. Si el ajuste del
temporizado del burst tiene que hacerse desde el MMI y no en puesta en marcha, hay que reabrir
esto para F1 en concreto.

Sigue abierto **en qué unidades cruzan el cable**: el DRx los lleva en unidades de reloj, y
exponerlos así al MMI traslada al RCP una conversión que depende del reloj del DRx. Recomendamos
que el proxy convierta a microsegundos y que el reloj no salga del DSP.

### 16. Tipo de transmisor en el contrato

Consecuencia de la pregunta 5, ya cerrada: **el parque es mixto, magnetrón y klistrón conviven.**

**Qué falta:** un campo de tipo de transmisor en `DSP↔RCP` —y, seguramente, el mismo dato en
`DRx↔DSP`—, publicado en `capabilities` o en `config`, no deducido.

**Por qué:** hoy es una constante de compilación
(`lamula-dsp/crates/service/src/ray.rs:267`, `MAGNETRON_TRANSMITTER: bool = true`) cuyo propio
doc-comment admite ser un placeholder a falta de campo de contrato. De ese valor dependen tres
comportamientos incompatibles entre sí: la vía de recuperación de segundo trip (fase aleatoria
frente a SZ(8/64)), si la corrección de fase por burst es obligatoria u opcional, y qué controles
puede ofrecer el MMI sin invitar a un error. Un binario compilado para magnetrón desplegado en
una instalación de klistrón no falla: produce datos silenciosamente peores.

**Coste:** un `u8` de enumeración y la ramificación en `ray.rs`. Los dos algoritmos ya existen.

---

## Tarea pendiente en este repositorio: re-vendorizar a v1.3

Decidido el 2026-09-19 (pregunta 2). **No es una tarea del proyecto DSP, es nuestra.** Consiste en:

1. Regenerar en `lamula-dsp` con `make gen` a partir de
   `contract/schema/dsp_rcp_v0_1.toml` (hoy v1.3).
2. Copiar los tres ficheros generados a sus destinos: `contract/vendor/dsp_rcp_v0_1.py`,
   `contract/vendor/dsp_rcp_v0_1.rs` y `mmi/src/contracts/dsp_rcp_v0_1.ts`.
3. Actualizar el pin en `contract/vendor/UPSTREAM.toml`: `commit`, `commit_date`,
   `version_major` 0 → **1**, `version_minor` 1 → **2**, y los tres SHA-256.
4. Pasar `tools/check_vendored_contract.py` y `make check`.

**Lo que no es mecánico:** `Config` crece de 80 a 84 bytes y gana `polarization_mode`,
`antenna_isolation_db` y `burst_window_bins`; `Command` gana `request_spectrum` = 7; y la
cabecera gana `header_flag::SIMULATED_SOURCE`, que **hay que leer**, no sólo tolerar — un lector
que siga exigiendo `flags == 0` rechazará toda trama de un despliegue simulado. Todo lo que
hoy consume el contrato v0.1 —adaptadores de `src/adapters/dsp/` y lo que la MMI importe de
`mmi/src/contracts/`— hay que revisarlo, y los tests que fijen tamaños o desplazamientos van a
fallar. Cuéntese como cambio de código con su verificación, no como actualización de un fichero.

---

## Preguntas para el equipo DSP

1. ~~**¿Cómo llega el RCP a los parámetros que posee el contrato `DRx↔DSP`?**~~
   **Cerrado (2026-09-19): opción (a), el DSP hace de proxy y `DSP↔RCP` gana los campos.** El
   RCP habla un solo protocolo y no tendrá adaptador DRx. Ver la nota al comienzo de "Falta en
   el contrato" y la entrada 15. Queda dentro de esa decisión, para el equipo DSP: si los
   parámetros reexpuestos son de solo lectura o escribibles, en qué unidades cruzan, y quién
   valida las combinaciones inválidas.

2. ~~**¿Se re-vendoriza `DSP↔RCP` antes de empezar familia E?**~~
   **Cerrado (2026-09-19): se re-vendoriza ya, y el destino es v1.3.** No se espera a una v2 que incluya los
   huecos de este documento. Es prerrequisito: con el pin actual el RCP no puede hablar con el
   DSP ni siquiera para recibir momentos. Ver "Tarea pendiente: re-vendorizar" más abajo.

3. **¿La familia E se acota a lo que el `Config` sabe llevar, o el DSP ensancha el esquema?**
   Es la pregunta de alcance que gobierna todo lo demás. Diseñar 29 campos y diseñar 130 son
   proyectos de tamaños muy distintos, y el reparto de este documento (10 Existe + 46 Difiere
   frente a 82 Falta) dice que hoy sólo se puede construir un tercio de las vistas E.

4. **¿Qué parte de los ocho parámetros horneados como constantes en `ray.rs` (punto 7 de
   "Falta") debe ser ajustable por el operador, cuál es de puesta en marcha, y cuál es
   realmente constante?** No hace falta exponerlos todos. Pero los doc-comments dicen que son
   placeholders, y un placeholder que nadie decide se convierte en constante por omisión.

5. ~~**¿Nuestra instalación es de magnetrón o de klistrón?**~~
   **Cerrado (2026-09-19): conviven las dos configuraciones.** No es una constante de
   instalación: el parque es mixto. Consecuencias, y ninguna es cosmética:

   - **`MAGNETRON_TRANSMITTER: bool = true` (`lamula-dsp/crates/service/src/ray.rs:267`) deja
     de ser admisible.** Su propio doc-comment ya decía que era constante local a falta de
     campo de contrato; ahora ese campo es obligatorio. Ver la entrada 16 de "Falta".
   - **La recuperación de segundo trip depende del tipo de transmisor**: fase aleatoria en
     magnetrón (ya cableada en el dealiasing de rango), SZ(8/64) en klistrón
     (`crates/sz864`). El DSP tiene que elegir la vía según el campo, no según la compilación.
   - **La corrección de fase por burst es prerrequisito duro en magnetrón y opcional en
     klistrón.** El MMI no puede ofrecer apagarla en una instalación de magnetrón.
   - **El MMI tiene que mostrar de qué instalación se trata** y adaptar qué opciones ofrece.
     Un control de SZ(8/64) visible frente a un magnetrón es una invitación a un fallo.

6. **¿Hay equivalente previsto para `Clutter Microsuppression`, `Max power mismatch across
   octants`, `High power rejection threshold`, `Maximum KEY phase error` y el "filtro
   estadístico" del catálogo Ravis?** No he encontrado nada en `docs/algorithms/` ni en los
   crates que corresponda a ninguno de los cinco. Puede que sean específicos del RVP900 —en
   cuyo caso son "No aplica" y se cierran— o funciones reales que nadie ha mapeado. No se
   puede decidir desde aquí.

7. **¿Existe un modo *freerunning* (radial cerrado por ángulo, sin trigger externo)?** De ello
   depende si `Minimum freerunning ray holdoff` aplica. `RadialAssembler` cierra por metadatos
   de rayo, pero no he encontrado documentado qué pasa cuando no llega trigger.

8. ~~**¿Debe el contrato declarar si el DSP corre contra el simulador o contra hardware real?**~~
   **Cerrado (2026-09-19): sí, y ya está implementado en el DSP** — contrato `DSP↔RCP`
   **v1.2 → v1.3**, aditivo. Quedó en el **byte de banderas de la cabecera común**, que estaba
   reservado, como `header_flag::SIMULATED_SOURCE` (bit 0), y no en `capabilities` ni en
   `status`: así viaja **con cada trama, incluido cada `moment_ray`**, sobrevive a una
   reconexión del RCP a mitad de adquisición y no exige petición previa. El DSP lo lee de una
   variable de entorno obligatoria (`LAMULA_DSP_SIMULATED_SOURCE`) y lo estampa en todos los
   mensajes `up`.

   **Lo que falta es de este lado.** El RCP tiene que: leer el byte de banderas en vez de
   ignorarlo, **negarse a archivar en Level-II una trama marcada como simulada** —o archivarla
   con marca inequívoca, según decida el proyecto ORPG—, y encender el estado `simulated` que
   el inventario de UI ya exige en la barra global (`EnvironmentBadge`, vista A1). Nada de eso
   existe hoy, y llega con la re-vendorización.

9. ~~**¿Comparte el plano de control socket con el flujo de momentos?**~~
   **Cerrado (2026-09-19): socket propio para control, separado del flujo de momentos.** Los
   momentos son un caudal continuo en un sentido; el control es esporádico, bidireccional y
   necesita confirmación. Evita el bloqueo de cabeza de línea —un `config_ack` esperando
   detrás de un lote de radiales justo cuando el operador espera respuesta— y desacopla las
   caídas. Queda por concretar con el equipo DSP: **qué mensajes viajan por cuál**. Hoy
   `status`, `capabilities`, `config_ack`, `bite_event` y `spectrum_frame` llegan por el socket
   de momentos y se descartan sin leer
   (`src/adapters/dsp/moment_stream_receiver.py:81-84`); la propuesta natural es que
   `config_ack` y `bite_event` pasen al socket de control con el resto del plano de mandatos, y
   que `spectrum_frame`, que es un volcado de datos, se quede con los momentos.

10. **Corrección de documentación, no de formato:** el enum `polarization_mode` describe
    `alternating` como "radial a radial" (`…toml:480`) cuando todo el cableo asume pulso a
    pulso vía `ray_flag::TX_POL_V`. El propio roadmap lo detecta y lo deja para "la próxima
    revisión del contrato" (`roadmap.md:403-413`). Si esa revisión va a tardar, conviene al
    menos anotarlo en `interfaces/dsp.md` para que la MMI no etiquete mal el control.

---

## No aplica — registro razonado

Para que nadie vuelva a revisar esto dentro de seis meses. 65 filas del inventario se
descartan, y todas por una de estas seis razones. La razón de fondo es siempre la misma: el
RVP900 es procesador de señal, receptor digital y generador de triggers a la vez; nosotros
partimos esas funciones en tres proyectos.

| Motivo | Filas afectadas | Fundamento |
| --- | --- | --- |
| **Generación y temporizado de triggers** | E5: pretrigger (4), número de triggers de salida y de controles de polarización (2), blanking durante medida de ruido, `Rx-Fixed Triggers`. E6: tabla `Start`/`Width`/`High`, puntos de conmutación de fase y de polarización, patrón de 4 bits. E2: `Process w/ custom trigs` | Fuera del alcance del DSP por decisión de plan (`lamula-dsp/docs/dsp-plan.md` §3.2): "hard real-time signal acquisition (ADC, DDC, decimation, **trigger generation**, SSI encoder reading) — owned by the FPGA". El DRx expone cuatro pares fijos, no un banco configurable (`drx_dsp_v0_1.rs:133-147`) |
| **Hardware IFD / IFDR del RVP900** | E9: reloj sintetizado, referencia externa, longitud de trama UDP. E6: FIR de recepción (2). E12: TrigRAM, *immediate status words*, registros de diagnóstico | No existe tal módulo en nuestra arquitectura. Su equivalente funcional es el DRx, cuyo contrato es otro |
| **Interfaz eléctrica AFC digital de 25 bits** | E7: `AFC format` + `ActLow`, `AFC uplink protocol`, tabla de 25 pines, `FAULT status pin` + `ActLow`, sentido de la tensión, `AFC Servo`. F2: patrón de bits codificado. F5 entera | Nuestro camino de AFC es un mensaje `Afc` con `nco_phase_inc` (u64) sobre TCP hacia el DRx (`drx_dsp_v0_1.rs:175`; `burst-fase-afc.md:44-52`). No hay cableado paralelo, ni pines, ni tensión |
| **TAGs (formato serie de ángulo del RVP900)** | E9: bits a invertir AZ/EL. E12: `GPARM` TAGs | Nuestro encoder es SSI y los ángulos llegan al RCP **ya en grados calibrados** (`…toml:33-37`, `:120-124`). La escala y el offset sí tienen equivalente, pero en variables de entorno del DSP, y por eso van como "Difiere", no aquí |
| **Receptor dual de ganancia solapada (WDN) y generación de forma de onda de Tx** | E2: `Channel separation`, `Maximum deviation`, `Overlap/Interpolate interval`, `DualRx – Sum H+V`. E8: canales A y B completos (9). E9: `Default receiver mode` legacy WDN | Nuestros canales son polarimétricos o de burst, todos de la misma ganancia (`drx_dsp_v0_1.rs:207`). Y el DSP no genera señal de transmisión: el control físico de osciladores está fuera de alcance (`dsp-plan.md` §3.2) |
| **Pulso comprimido** | E6: `Tx Waveform`, ancho de banda, longitud, offset, tres parámetros de *tuning*. E8: `FM Chirp spectrum flattener`. F4 entera | No está en el alcance Stage 1 (`dsp-plan.md` §3.1 no lo lista) y ningún crate lo implementa |
| **Presentación, o producto del ORPG** | E10: `Nyquist sign flip`. E2: `Allow continuous sizes`, `Melting height`. E3: `PMI`, `HCLASS`. F1/F3: zoom, span, promediado de plot. F6 entera | El dibujo es del MMI del RCP; la clasificación de hidrometeoros y la generación de producto son del ORPG (`dsp-plan.md` §3.2) |
| **Resuelto en hardware** | E6: `Maximum number of Pulses/Sec`, `Maximum instantaneous PRF` | El product expert confirmó que la tarjeta del modulador evalúa PRF × ancho de pulso y corta la transmisión ella misma; el RCP sólo lee el estado (`lamula-rcp/docs/alcance/pendientes.md:266-275`) |
| **Formato de series temporales** | E2: `Use High-SNR 16-bit packed timeseries format` | El `DSP↔RCP` transporta momentos en f32 a precisión plena por decisión explícita (`…toml:15-27`); la diezmación a 8/16 bits es del codificador Level-II del RCP |

Un caso que **no** se descarta pese a parecerlo, y conviene dejarlo escrito: **SZ(8/64) de la
vista E8**. El inventario ya avisaba de que el klistrón admite fase programable pulso a pulso,
y del lado DSP está confirmado (`roadmap.md:712-713`) e implementado (`crates/sz864`). Va como
**Falta**, no como No aplica.
