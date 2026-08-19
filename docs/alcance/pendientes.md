# Pendientes

Cada pendiente lleva identificador estable (`PEND-RCP-nn`) para no chocar con la numeración
`PEND-nn` de `radar_emulator`, que se referencia aparte porque **también aplica a este repo**: el
RCP consume el mismo contrato Modbus/UDP que ese proyecto especifica del lado servidor/emisor.

## Heredados de `radar_emulator` — bloqueantes para pruebas formales del RCP también

Estos valores están inventados como marcador de posición en el otro proyecto. Un RCP que confíe
en ellos para una prueba formal contra hardware real hereda el mismo riesgo.

- **PEND-01** (radar_emulator) · Escala de azimut/elevación (milésimas de grado) — sin verificar
  contra la resolución real del encoder.
- **PEND-04** (radar_emulator) · Palabra de estado del paquete UDP — bits propuestos, no
  confirmados con el equipo de FPGA/controlador.
- **PEND-06** (radar_emulator) · Codificación y escalado de señales analógicas Modbus — Type Code
  real desconocido; todos los rangos de ingeniería de la semilla son invención.
- **PEND-07** (radar_emulator) · Mapa Modbus de módulos 4069/4117/4150 — inferido por analogía,
  no leído de manual.
- **PEND-08** (radar_emulator) · Unit IDs reales del gateway — arbitrarios en la semilla.
- **PEND-20** (radar_emulator) · Ciclo de interrogación y timeout del controlador — dato que
  **este repo** debe producir (es el propio RCP quien fija ese ciclo), y que puede obligar a
  `radar_emulator` a revisar su tick de 50 ms (D-10 de ese proyecto).

Ver `radar_emulator/docs/alcance/pendientes.md` para el detalle completo de cada uno.

## Propios de este repo

### PEND-RCP-01 · Semántica de doble reloj (monótono vs. pared) en el contrato RCP↔ORPG

`AGENTS.md` de este repo introduce la regla "dos relojes, no uno" (Level-II/ORPG en hora de
pared real, telemetría interna en reloj monótono) como **inferencia**, no como algo explícito en
[Project Plan](../referencia/project-plan.md). El plan no dice literalmente qué reloj usa el feed a ORPG.
Confirmar con el equipo antes de congelar el contrato RCP↔ORPG en Fase 0: NEXRAD Level-II exige
timestamp absoluto de la observación, así que probablemente no hay alternativa, pero debe quedar
explícito y no asumido.

### PEND-RCP-02 · Librería de componentes frontend

Plan §5: "PrimeVue o shadcn-vue (Reka UI) — *decisión necesaria*".

**Resuelto (2026-08-19):** shadcn-vue (Reka UI). Primer intento fue PrimeVue, revertido el mismo
día al descubrir que `primevue@5.0.1` exige license key (relicenciado como "PrimeUI", ya no MIT
sin condiciones). Ver
[D-08](decisiones.md#d-08-stack-python-312-fastapi-pydantic-v2-asyncio-vue-3-ts-vite-en-frontend).

### PEND-RCP-03 · Herramienta de empaquetado de dependencias Python para el target offline

El plan (§5, §12) fija Docker Compose como opción primaria y PyInstaller como alternativa, pero
no fija cómo se vendorizan los wheels de Python para el mirror interno / build offline (pip-tools
+ index local, `uv` con lockfile, o imagen Docker que ya trae todo). Decisión de tooling, no de
arquitectura — resolver en Fase 0 al montar CI.

**Resuelto (2026-08-19):** `uv` con lockfile (`uv.lock`). CI resuelve/instala con `uv`, wheels
cacheados en capa Docker; el lockfile queda como fuente auditable de versiones exactas,
independiente de reconstruir la imagen.

### PEND-RCP-04 · Disponibilidad de ORPG real o stub CM_TCP para Fase 0

El plan (§8.2, Fase 0) pide un "handshake mínimo RDA↔ORPG" como spike de la Fase 0. No está
confirmado si hay acceso, en esta etapa, a un build real de ORPG.

**Parcialmente resuelto (2026-08-19):** se construyó el stub CM_TCP (`spike-fase0/
rda_orpg_handshake_spike.py`, rol `--role orpg`) y se corrió el spike de loopback (Msg 11/12)
contra él — ver `spike-fase0/RESULTADO-rda-orpg.md`. El formato de bytes (CTM_Header, MSG_Header,
payload del Loopback Test) se tomó del proyecto legacy `RDA_Backend_Py` (2013, ingesta de
radares cubanos al ORPG), que cita el ICD 2620002F como fuente — no es una reinterpretación
propia del ICD.

**Hallazgo del legacy confirmado (2026-08-19):** quién valida el eco del loopback (el que recibe
11, no el que recibe 12) fue confirmado por el usuario — ese mismo `RDA_Backend_Py` corrió en
producción real haciendo ingesta de productos al ORPG, no es un bug de 2013. Confirmación por
experiencia operativa directa, no por sign-off del equipo LAMULA ORPG. Ver `RESULTADO-rda-orpg.md`.
El spike actual todavía implementa la lectura literal del ICD, no esta dirección confirmada —
alinear antes de congelar el contrato.

Sigue sin resolver: acceso a un ORPG real para validar el stub contra la implementación real, y
el rol de `RDA_Redundant_Channel` (canal principal vs. redundante) en quién inicia el loopback.

**Acción pendiente explícita:** cuando haya acceso a un ORPG real, correr
`rda_orpg_handshake_spike.py --role rda` contra él (no contra el stub `--role orpg` local) y
confirmar que la dirección del eco coincide con lo que el usuario reportó de producción. Hasta
entonces, la confirmación vale como "funcionó en producción con este legacy", no como "validado
contra este ORPG real".

### PEND-RCP-05 · El DSP externo no tiene aún una interfaz de referencia ejecutable

El plan asume el contrato RCP↔DSP "acordado con el proyecto DSP" (plan §6, §12), pero no hay,
al momento de crear este repo, un simulador o especificación del stream de momentos equivalente
a lo que `radar_emulator` ya ofrece para HAL. La ingestión DSP/DRX de Fase 1 puede quedar
bloqueada por esto igual que Fase 0 lo estaría sin `radar_emulator`.

**Parcialmente resuelto (2026-08-19):** se construyó un stub propio
(`spike-fase0/dsp_moment_stream_spike.py`) que emite/consume un volumen sintético contra el
esquema ya congelado (`src/core/contracts/dsp.py`) — ver `spike-fase0/RESULTADO-dsp.md`. El
framing/formato de transporte es invención de este repo, no un acuerdo con el proyecto DSP; sigue
sin resolver el acceso a una implementación de referencia real del lado DSP para validar contra
algo no inventado localmente.

### PEND-RCP-06 · Secuencia y confirmación de la rutina "general radar power-on" (Fase 2)

El plan (§4.3) nombra las seis rutinas de control pero no fija su procedimiento interno — a
diferencia del ICD RCP↔ORPG, esto es responsabilidad de diseño de este repo, no de un documento
externo. `core/control_routines/general_power_on.py` infiere, solo a partir de los nombres del
catálogo vendorizado, que las precondiciones son `sys.line_parameters_ok_status`,
`sys.environment_ok_status`, `sys.standby_system_ok_status` (en ese orden, sin orden fijado por
nada más que la posición en el catálogo). No está confirmado con el product expert.

Además, el catálogo RD100S no tiene ninguna señal de confirmación tipo "radar encendido": la
rutina infiere éxito de que las tres precondiciones sigan en OK después del pulso a
`sys.turn_on_radar_conmand`, no de una lectura directa. `radar_emulator` tampoco modela lógica
para ese DO (a diferencia de `tx.fsm`), así que el spike de esta rutina no puede validar más que
"el pulso se envió y las precondiciones no cambiaron" — no hay forma de que el simulador actual
confirme ni refute la secuencia elegida.

**Acción pendiente explícita:** confirmar con el product expert (o el manual del RD100S si
aparece) el procedimiento real de "general radar power-on" antes de tratar esta rutina como algo
más que un primer borrador — y decidir si vale la pena pedir a `radar_emulator` un bloque de
lógica para `sys.*` equivalente a `tx.fsm`, igual que se hizo notar para el transmisor.

### PEND-RCP-07 · Secuencia y umbrales de las rutinas de control 2–6 (Fase 2)

Mismo problema de fondo que PEND-RCP-06, extendido a las cinco rutinas que todavía no tienen
código: `docs/operacion/rutinas-control.md` documenta un diseño propuesto para cada una, deducido
del comportamiento de `radar_emulator` (hoy la única referencia disponible), no de un manual del
RD100S ni de un procedimiento confirmado por el product expert. Puntos concretos sin confirmar:

- **Transmisor:** el tiempo de arranque (~1,5 s), el tiempo de caldeo del magnetrón (~3 min) y el
  umbral de sobrecorriente pico del magnetrón (55 A) son valores de marcador de posición que el
  propio `radar_emulator` marca como pendientes en su config — no son datos del RD100S real.
  Tampoco está confirmado si el radomo participa en la cadena de enclavamiento del transmisor.
  **Implementada como primer borrador**, hasta `tx.ready_status` únicamente, en
  `core/control_routines/transmitter_power_on.py` (ver
  `spike-fase2/RESULTADO-transmitter-power-on.md`, incluye corrida real esperando el caldeo
  completo de ~180 s). Elige no subir alta tensión ni radiar como parte de esta rutina — respuesta
  conservadora a la pregunta abierta, sin confirmar con el experto. **Hallazgo:** la transición
  real de encendido del `tx.fsm` no exige ningún interlock (solo los exige al subir HV); la
  rutina los chequea de todos modos como precondición propia del RCP, más estricta que el
  simulador. Son seis señales agregadas, no siete — `tx.interlock_ok_status` ya combina radomo +
  sistema en espera.
- **Receptor:** no hay ninguna pista de tiempos de enganche del oscilador local (STALO) ni de si
  existe algún enclavamiento previo al encendido — el simulador no modela nada de esto.
  **Implementada como primer borrador** en `core/control_routines/receiver_power_on.py` (ver
  `spike-fase2/RESULTADO-receiver-power-on.md`). A diferencia de las demás, ninguna señal `rx.*`
  la calcula nada en el simulador — el camino de éxito solo se pudo probar forzando también
  `rfe_on_status`/`stalo_locked_status`, no solo la precondición. `confirm_timeout_s` es
  obligatorio, sin default, por la misma falta total de referencia.
- **Unidad de antena:** el catálogo tiene una sola orden (no un par Encender/Apagar como las
  demás rutinas de encendido) — puede ser un interruptor de nivel en vez de un pulso momentáneo,
  rompe el patrón de las otras tres rutinas de encendido y necesita confirmación explícita antes
  de programarla. **Implementada como primer borrador** en
  `core/control_routines/antenna_unit_power_on.py` (ver
  `spike-fase2/RESULTADO-antenna-unit-power-on.md`), tratando el comando como nivel (mismo
  criterio que `enable_drive_az/el_conmand` en la Rutina 5: comando único, no listado en
  "Comandos por flanco" de `radar_emulator`) — sin confirmar. Mismo problema que el receptor:
  ningún bloque del simulador calcula `au_on_status` ni los `drive_{az,el}_ok_status`.
- **Movimiento de antena:** los límites de elevación (interruptor en ≈−1,5°/91,5°, tope físico
  duro del simulador en −2°/92°) y el umbral térmico de azimut (30 A durante 5 s equivalentes) son
  valores de marcador de posición. Azimut tiene protección térmica de motor modelada en el
  simulador; elevación no (solo fin de carrera) — sin confirmar si es un hueco a cubrir en el RCP.
  **Implementada como primer borrador** en `core/control_routines/antenna_movement.py` (ver
  `spike-fase2/RESULTADO-antenna-movement.md`): consume la guarda de límites de antena
  (`core/safety_guard/`) antes de empezar a mover y también mientras se mueve, porque el bloque de
  azimut del simulador calcula la falla térmica pero no corta el drive él mismo — a diferencia de
  elevación. **Hallazgo nuevo:** la señal real de referencia de velocidad
  (`ant.speed_reference_driver_az`/`_el`) está en voltios (±10 V), no en grados/s como sugiere la
  descripción de la rutina más abajo — no existe una ganancia real del RD100S para traducir una
  velocidad deseada en grados/s a esa referencia de voltaje; la rutina implementada recibe
  voltios directamente y no confirma magnitud de velocidad, solo sentido de giro y arranque.
- **Posicionamiento de antena:** el radar solo acepta velocidad, nunca una posición objetivo — el
  lazo de control (tolerancia final, timeout, perfil de frenado) es diseño enteramente nuevo del
  RCP, sin nada equivalente que imitar del simulador ni del plan. **Implementada como primer
  borrador** en `core/control_routines/antenna_positioning.py` (ver
  `spike-fase2/RESULTADO-antenna-positioning.md`), apoyada en la Rutina 5 en cada paso de control.
  A diferencia de las demás rutinas, aquí no hay ni siquiera un marcador de posición del
  simulador que usar — por eso la ganancia, el voltaje máximo, la tolerancia y el timeout son
  parámetros obligatorios sin default, no constantes inventadas dentro de la rutina. **Limitación
  conocida sin resolver:** control proporcional simple sin cálculo de distancia de frenado, puede
  sobrepasar el objetivo mientras el eje desacelera (ver Rutina 5, aceleración sin confirmar).

**Acción pendiente explícita:** revisar `docs/operacion/rutinas-control.md` completa con el
product expert — con esto, las seis rutinas del plan tienen primer borrador implementado y
probado contra el simulador, pero ninguna confirmada. Esto no es un caso donde "probar contra el
simulador y listo" alcance: varios de los valores que el simulador usa son marcadores de posición
inventados por el equipo de `radar_emulator`, no datos del radar real, y los de la Rutina 6 no
tienen ni siquiera ese respaldo débil.

### PEND-RCP-08 · Guarda de PRF × pulse-width para protección del klystron/magnetrón (Fase 2)

El plan (§4.3/§4.4) pide que la guarda de seguridad de parámetros rechace "combinaciones de
pulse-width × PRF que dañarían el klystron/magnetrón", además de los límites de antena.

**Bloqueado, no solo sin confirmar:** a diferencia de los límites de antena (`PEND-RCP-07`, que sí
tienen señales reales que consultar aunque sus valores numéricos sean marcadores de posición), la
parte de PRF × pulse-width no tiene **ningún** dato que vigilar todavía:

- No hay ninguna señal de PRF ni de pulse-width en el catálogo HAL vendorizado
  (`rd100s_signal_catalog.json`) — `tx.duty_cycle_ok_status` es un estado que el propio
  `radar_emulator` calcula del lado servidor, no un parámetro que el RCP fije.
- `core/contracts/dsp.py` (RCP↔DSP/DRX) tampoco tiene un campo de PRF/pulse-width — ese contrato
  es sobre momentos ya calculados, no sobre parámetros de forma de onda de transmisión.
- El plan ubica el Scan Worksheet manual (donde el operador definiría estos parámetros) más
  adelante en la misma Fase 2, sin implementar todavía; tampoco existe contrato alguno con un
  generador de forma de onda o DRX que reciba esos parámetros.

Ver `spike-fase2/RESULTADO-parameter-guard.md` para el spike que implementó y validó solo la
parte de límites de antena de esta guarda (`core/safety_guard/antenna_limits.py`), dejando esta
mitad fuera explícitamente.

**Acción pendiente explícita:** no implementar esta parte de la guarda hasta que exista (a) el
Scan Worksheet o el punto de entrada que fije PRF/pulse-width, y (b) la tabla de límites de
ciclo de trabajo del klystron/magnetrón del RD100S real, propiedad del product expert según el
propio plan ("Product-expert-owned duty-cycle/limit rules", §11 Risk Register).
