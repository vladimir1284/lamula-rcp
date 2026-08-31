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
framing/formato de transporte era invención de este repo, no un acuerdo con el proyecto DSP.

**Resuelto en formato (2026-08-30):** el proyecto DSP congeló el contrato de cable
`DSP↔RCP v0.1` y aquí está vendorizado y anclado por hash en `contract/vendor/`, con adaptador
(`src/adapters/dsp/wire.py`) y tests contra tramas construidas con el módulo generado del propio
proyecto DSP. El framing inventado por el stub ya no se usa en `src/`. Ver
[la página de interfaz](../interfaces/dsp.md).

Dos cosas del contrato se decidieron a raíz de las reglas de este repo, no en el DSP: la
separación de relojes (el cable trae ahora hora de pared **y** monótono, en vez de solo monótono)
y los tres campos que el Msg 31 del ICD 2620002 exige y solo el DSP conoce.

**Sigue abierto:** no hay emisor de referencia del lado DSP corriendo. Lo verificado es el
**formato**, no la cadencia, ni la contrapresión con radiales de 3680 celdas a PRF alta, ni el
comportamiento en reconexión. Hace falta el simulador de señal del proyecto DSP, que aún no
existe.

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

!!! success "Parcialmente resuelto (2026-08-20): feedback de expertos + `sys.fsm` en `radar_emulator`"
    El product expert revisó la Rutina 1 (`ControlRoutines.md`, absorbido en
    `radar_emulator/docs/alcance/pendientes.md` PEND-27/PEND-28 y ya no vive como fichero suelto
    en este repo). Responde las dos preguntas abiertas de arriba:

    - **Precondiciones confirmadas:** son **cuatro**, no tres — `sys.standby_system_ok_status`,
      `sys.line_parameters_ok_status`, `sys.environment_ok_status` **y
      `sys.remote_mode_ok_status`** (falta esta última en `PRECONDITIONS` de
      `general_power_on.py`).
    - **Sí existe ahora una confirmación de "radar encendido":** tras el pulso, el procedimiento
      confirmado exige comprobar `sys.system_on_ok_status` y `sys.mdb_fan_ok_status` (antes
      inexistentes en el catálogo), y como paso final, `Tx/Rx/AU Cabinet Fan Ok Status`
      (`sys.cabinet_fans_ok`, agregado). `radar_emulator` ya modela todo esto en un bloque
      `sys.fsm` real (`state_machine`, OFF/STARTING/ON/FAULT) — equivalente a `tx.fsm`, lo que
      esta rutina pedía como trabajo futuro ya está hecho del lado del simulador.

    **Resuelto del lado del código (2026-08-20):** `general_power_on.py` ya chequea las cuatro
    precondiciones, lee `system_on_ok_status`/`mdb_fan_ok_status` como confirmación directa
    post-pulso, y agrega el chequeo final de Cabinet Fans leyendo las cuatro señales reales por
    separado (no `sys.cabinet_fans_ok`, que es virtual/interna al simulador — mismo criterio que
    `tx.interlock_ok_status` en la Rutina 2). Si el pulso y la confirmación salen bien pero falla
    algún Cabinet Fan, la rutina reporta `INTERRUPTED` (el radar sí quedó encendido), no `FAILED`.
    No lee `sys.radar_on_status`: es virtual y sin equivalente en el catálogo real, coherente con
    que el ICD confirma que esa señal no existe en el hardware real.

    **Re-ejecutado contra instancia real (2026-08-20):** `spike-fase2/general_power_on_spike.py`
    corrido contra `radar_emulator` con el `sys.fsm` nuevo (119 señales) — las tres corridas
    (precondiciones en falso, todo en verdadero, un Cabinet Fan caído) en verde, ver
    `spike-fase2/RESULTADO-general-power-on.md`. PEND-RCP-06 queda resuelto del lado de
    código+simulador.

    Sigue quedando abierto: las dos asunciones del mapeo de "Cabinet Fan" en `radar_emulator`
    (PEND-27/PEND-28) — sin equivalente que validar contra hardware real todavía.

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

!!! success "Aceptado por decisión del usuario (2026-08-20), no por revisión confirmada — ver D-11"
    El product expert no ha objetado nada de las Rutinas 2–6 (solo la Rutina 1 tuvo feedback
    explícito, ver PEND-RCP-06). El usuario decide aceptar esto como suficiente para seguir
    adelante sin bloquear más trabajo de Fase 2/3. **Esto es inferencia por ausencia de
    objeción, no una confirmación línea por línea** como sí ocurrió con la Rutina 1 — si el
    experto señala algo concreto sobre estas rutinas más adelante, tiene prioridad automática
    sobre esta decisión. Ver [D-11](decisiones.md#d-11-pend-rcp-07-rutinas-26-se-acepta-como-suficientemente-confirmado-por-silencio).

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
  adelante en la misma Fase 2. **Su contrato de datos ya existe**
  (`core/contracts/scan.py`, `PpiCut`/`RhiCut` con `prf_hz`/`pulse_width_us`) pero es solo forma —
  todavía no existe contrato alguno con un generador de forma de onda o DRX que reciba esos
  parámetros, ni un Scan Controller que los use.

Ver `spike-fase2/RESULTADO-parameter-guard.md` para el spike que implementó y validó solo la
parte de límites de antena de esta guarda (`core/safety_guard/antenna_limits.py`), dejando esta
mitad fuera explícitamente.

!!! success "Parcialmente resuelto (2026-08-20): feedback de expertos, replantea el bloqueo"
    Reporte técnico del product expert sobre `Duty Cycle Ok/Fault` e `I²t` de servodrives.
    Confirma que `Duty Cycle Ok/Fault` es señal de hardware pura -- la tarjeta del modulador
    evalúa PRF×pulse-width contra el dispositivo emisor (magnetrón/klystron) y corta la
    transmisión ella misma; el RCP solo lee el estado (`tx.duty_cycle_ok_status`, ya en el
    catálogo, ya alimenta el interlock de subida de HV en `tx.fsm`). **El bloqueo original estaba
    mal planteado:** no hacía falta ninguna señal HAL nueva ni un contrato con un adaptador de
    forma de onda -- eso es responsabilidad exclusiva del hardware. Lo que el RCP sí debe hacer es
    la guarda de **software, en el punto de captura del dato** (VCP personalizado -- en este repo,
    el Scan Worksheet manual): calcular `duty = prf_hz × pulse_width_us` y bloquear la
    confirmación si excede norma. Implementado como validador de pydantic directamente en
    `core/contracts/scan.py` (`PpiCut`/`RhiCut`, función `_check_duty_cycle`) -- se aplica solo
    en el punto de entrada porque perfiles predefinidos (VCP fijo por el sistema) no necesitan la
    guarda, y ese mecanismo de perfiles no existe todavía en este repo.

    **Resuelto también el valor numérico (2026-08-20):** el reporte inicial daba cuatro casos sin
    decir cuál aplicaba al RD100S real (magnetrón VMS1157 0.06%, MRL-5 0.05%, modulador de estado
    sólido La Habana 0.05%/0.08%, hasta 0.2% según modo). El usuario confirmó directamente el
    número real: **0,085% (0.00085), el máximo válido en cualquier caso/configuración de este
    RD100S** -- no un valor genérico ni una inferencia por nombre de señal. `DUTY_CYCLE_LIMIT` en
    `core/contracts/scan.py` actualizado de 0.001 (placeholder) a 0.00085 (confirmado). PEND-RCP-08
    queda resuelto por completo -- mecanismo y número.

### PEND-RCP-09 · Reconciliar el Scan Worksheet manual con VCP real (Fase 3)

`core/contracts/scan.py` define el Scan Worksheet manual de Fase 2 (`PpiCut`/`RhiCut`, plan §8.2:
"interactive scans (Scan Worksheet equivalent)") deliberadamente **sin** ningún concepto de VCP.

VCP es del lado `RCP↔ORPG` (ICD 2620002: Msg 6 "VCP change", Msg 5 definición de VCP) y está
asignado a Fase 3 ("emulación RDA completa"), no a Fase 2 — ver
`spike-fase0/RESULTADO-rda-orpg.md`: `RDA_TCPServer.py` (legacy `RDA_Backend_Py` del usuario, no
vendorizado en este repo) ya contesta `process_VCP` completo, pero ese alcance se dejó
explícitamente para Fase 3, no para el spike de Fase 0. Al no estar vendorizado el legacy, no hay
todavía una estructura VCP byte-exacta disponible para diseñar contra ella.

**Acción pendiente explícita:** cuando se cablee `RCP↔ORPG` en Fase 3, reconciliar
`ScanWorksheet` con VCP real — puede que el scheduler de volumen automático (Fase 2, sin
implementar todavía) termine consumiendo VCPs de ORPG en vez de, o además de, este Worksheet
manual. No se anticipa esa forma en este contrato. Tampoco se definió aquí ninguna relación entre
PRF/pulse-width/ancho de haz y velocidad de rotación de la antena durante un corte — es teoría de
escaneo de radar real que el product expert debe confirmar, no algo que se pueda inventar sin
respaldo (mismo criterio que PEND-RCP-07 para la Rutina 6).

### PEND-RCP-10 · Scan Controller: alcance acotado a movimiento de antena, sin confirmar (Fase 2)

`core/scan_controller.py` (`run_scan_cut`) secuencia solo el movimiento de antena de un corte del
Scan Worksheet (posicionar eje fijo + barrer eje móvil, apoyado en las Rutinas 5/6). Deliberadamente
no sube alta tensión ni radía (ver docstring del módulo — `transmitter_power_on.py` se detuvo en
`tx.ready_status` a propósito, sin que exista todavía una secuencia decidida para lo que sigue) ni
aplica `prf_hz`/`pulse_width_us` a ningún adaptador (PEND-RCP-08, bloqueado). La detección de fin de
barrido (acumulación de delta angular hasta alcanzar el ancho total pedido) es diseño propio de este
repo sin nada que imitar del simulador ni del plan — mismo criterio que ya justificó los parámetros
obligatorios de la Rutina 6. Probado como primer borrador contra una instancia real de
`radar_emulator` (`spike-fase2/RESULTADO-scan-controller.md`): `RhiCut`/`PpiCut` simples,
interrupción por guarda de seguridad a mitad de barrido, precondición `au_on_status` en falso. Sin
confirmar con el product expert.

**Hallazgo colateral (bug real, no de diseño):** el spike disparó un bug en
`src/adapters/hal_sim/simulated_hal.py` — `write_analog`/`read_analog` no manejaban la codificación
con signo (`int16`) de analógicas con rango crudo negativo (ej. `ant.speed_reference_driver_az`,
`-32768..32767`) contra el registro Modbus, sin signo en el wire (`0..65535`). Nunca se había
disparado antes porque ningún spike de Fase 1/2 había comandado una analógica negativa. Corregido
con conversión de complemento a dos de 16 bits en la frontera del wire — ver
`spike-fase2/RESULTADO-scan-controller.md` para el detalle.

**No probado en este spike:** vuelta completa de PPI (`azimuth_end_deg == 360`) — la lógica del
acumulador es la misma que el caso parcial, pero no se ejercitó ese caso límite. Tampoco el
sobrepaso de frenado con voltajes de barrido altos (misma limitación conocida de la Rutina 6,
heredada aquí vía `run_antenna_positioning`).

**Acción pendiente explícita:** decidir con el experto la secuencia de HV/radiar al arrancar un
escaneo (candidato natural para donde `transmitter_power_on.py` se detuvo), y si la detección de
fin de barrido por acumulación de delta es aceptable o si el radar real ofrece una señal de
posición de referencia distinta. Extiende PEND-RCP-07/09 (ganancia volt→grados/s, relación
PRF/pulse-width/ancho de haz→velocidad de rotación) a este nuevo consumidor.

### PEND-RCP-11 · Detalle Ravis para Data Views y DRX/RSP Control & Calibration (pantallas de Fase 3, aún no construidas)

`docs/referencia/project-plan.md` §4.5 ("MMI Screen Inventory") se amplió con detalle funcional
minado de los capítulos "Control Windows", "Data Views" y "Calibration and Alignment" del manual
Ravis 1.3 — capacidades e interacciones, nunca texto/etiquetas literales del manual (regla de
sourcing en `docs/index.md` de `lamula-dsp`). Cubre solo las dos pantallas que **todavía no
existen en este repo** (Data Views PPI/RHI/ASCOPE, DRX/RSP Control & Calibration) — las pantallas
ya construidas (System Visualization, Antenna Control, Scan Worksheet, BITE, System Information)
no se tocaron.

Se registra como **pendiente propuesto, no como decisión** (a diferencia de la mayoría de este
documento de plan): el plan en sí no pasó por el product expert de este proyecto, y un punto en
particular choca con una decisión ya congelada — ver más abajo. Nada de esto se implementa sin
confirmación explícita.

**Data Views (PPI/RHI/ASCOPE + color management).** Corrección, no solo adición: el plan
anterior decía que las tres vistas comparten un único subsistema de color; en realidad ASCOPE no
es una vista con color — es un trazo 1D y necesita su propio toggle de agregación por píxel
(máximo vs. promedio de bins) y toggle de unidad de eje X (distancia vs. tiempo). Detalle nuevo:
point-probe por click que sigue actualizando en vivo en ese punto hasta que el operador haga click
en otro lado; freeze/unfreeze independiente por ventana; divisor de refresco variable ("cada N
actualizaciones") y selector de resolución de renderizado, ambos para aliviar carga a alta
velocidad de antena; Color Composer (solo PPI/RHI) con matriz de presets por tipo de dato,
herramienta de interpolación RGB lineal entre dos colores para construir un degradado, copiar/
pegar preset entre tipos de dato, y tres modos de entrada de color (swatches/HSB/RGB). De esto
último sale un patrón de convención transversal a toda la MMI: **aplicar** (transitorio, sesión
actual) siempre es una acción separada de **guardar como default** (persistido) — mismo patrón
que aplica también en DRX/RSP más abajo, así que conviene fijarlo como convención de MMI, no
resolverlo por separado en cada pantalla.

**DRX/RSP Control & Calibration.** El texto anterior era un párrafo; la estructura real son seis
sub-vistas: (1) ajuste TX/RX; (2) carpeta de calibración, que resulta ser **dos procedimientos
distintos** — Zero Check (muestreo de piso de ruido) corre automático en boot y en intervalo de
fondo fijo, sin acción del operador, aparte del workflow manual de calibración de punto único/TX
que ya describía el plan; (3) configuración de trigger/timing por tabla; (4) monitor de proceso
DRX, más amplio de lo que decía el plan (espeja todo parámetro vigente del pipeline de
adquisición, no solo link/ray-rate); (5) carpeta BiTE del DRX, explícitamente **pull-only, no
push** — semántica distinta al System Status & BITE Manager del RCP (que es push/evento), no
deben confundirse en la UI ni en el contrato; (6) carpeta de constantes de la ecuación del radar.

**Vista ORPG-link:** sin precedente en Ravis (es anterior a ORPG/RDA) — se especifica solo desde
el contrato `RCP↔ORPG`, sin aporte de este pendiente.

!!! success "Resuelto (2026-08-27): gate de autoridad para calibración — D-13"
    El choque con D-07 (autoridad elevada para calibración vs. toggle único passive/active) se
    resuelve como **gate de modo mantenimiento**, acotado a las sub-vistas de calibración y
    constantes de la ecuación del radar, con Zero Check exento por ser automático — ver
    [D-13](decisiones.md#d-13-gate-de-modo-mantenimiento-para-acciones-de-calibracion-aparte-del-toggle-passiveactive)
    para el mecanismo completo. Decisión operativa del usuario, no confirmación técnica del
    product expert — mismo criterio que D-11.

**Acción pendiente explícita, lo que sigue abierto:** confirmar con el product expert antes de
Fase 3 (cuando estas pantallas entren en construcción) el resto del detalle de Data Views/Color
Composer y DRX/RSP de arriba como base de diseño, o ajustarlo. El gate de autoridad (D-13) ya no
es parte de lo pendiente.

### PEND-RCP-12 · ORPG no tolera la geometría del radial: la filtra por lista blanca

El RCP posee la emulación RDA WSR-88D (ICD 2620002) y el feed por radial a ORPG. Una lectura del
árbol de fuentes real de ORPG build 24 (paquete CODE del ROC, `rpg_b24_0r1_20_pub_src`), hecha en
agosto de 2026 desde el proyecto `lamula-drx` para su pendiente P-01, encontró que **ORPG no
valida la geometría del radial contra una banda de tolerancia, sino contra listas cerradas de
valores**, y descarta el dato cuando no encajan:

- `src/cpc004/tsk009/combine_radials.c:427-431` — la recombinación azimutal de super-res admite
  `surv_bin_size` en `{250, 1000}` y `dop_bin_size` **solo 250**. Si no encaja, descarta los dos
  radiales del split-cut con un aviso de nivel `GL_INFO`, fácil de perder en el log.
- `src/cpc023/tsk002/qia_process.c:707` y `src/cpc004/tsk011/dpp_format.c:547` — `Verify_gm_hd()`
  exige `bin_size == 250` exacto para **todo** moment dual-pol, y rechaza el campo con `GL_ERROR`
  si no. En la misma condición valida `data_word_size`, que admite solo 8 ó 16.
- `include/basedata.h:1013-1017` — topes duros de 1840 gates de reflectividad y 1200 de Doppler y
  dual-pol.

El campo de espaciado del Message 31 es entero de 16 bits **en metros**
(`include/generic_basedata.h:202`), así que no hay forma de declarar una fracción de metro: se
declara un valor de la lista o se pierde el producto.

**Lo que esto abre para el RCP:** si ORPG valida así el espaciado, es razonable esperar que valide
igual el resto de la geometría del radial — conteo de gates, rango al primer gate, resolución
azimutal, tamaño de palabra de dato. `data_word_size` ya está confirmado. El requisito del feed no
es «parecerse a NEXRAD», es **declarar valores legales de NEXRAD en todos los campos de geometría
del Message 31**, y eso puede imponer restricciones al encoder Level-II y, aguas arriba, al
formato del stream de momentos que llega del DSP.

**Condición de cierre:** enumerar los campos de geometría del Message 31 con la lista de valores
que ORPG acepta para cada uno, contrastarla contra lo que el RCP puede emitir con el stream que le
da el DSP, y anotar cada divergencia como decisión o como pendiente propio.

**Procedencia y salvedad:** las citas vienen de `lamula-drx/research/p-01-RESULTADO.md` y
`p-01-RESULTADO-barrido.md`. El árbol de ORPG no está en la máquina de desarrollo, así que no son
reverificables desde aquí; el barrido sí reverificó las cuatro citas decisivas del primer resultado
y coinciden. La cobertura fue por grep dirigido, no lectura exhaustiva: **quedan sin revisar** la
composición geográfica entre radares, VAD/VWP y el remuestreo final a rejilla Level-III, que es
justo donde más daño haría una asunción cableada.

### Vista MMI "Scan Worksheet" y endpoints de soporte (Fase 2)

`mmi/src/views/ScanWorksheetView.vue` (ruta `/scan-worksheet`) + `GET/POST/DELETE
/api/scan/worksheet` en `adapters/gateway/app.py`: editor manual de `PpiCut`/`RhiCut`, probado en
navegador (Playwright/chrome-devtools) contra el gateway + `radar_emulator` reales — crear PPI,
cambiar a RHI, crear con dos moments, eliminar, validación de cliente de "al menos un moment".
En esta sesión dejó de estar sin botón de "ejecutar" -- ver "Scan Controller conectado a la vista
Scan Worksheet" más abajo. **Resuelto (2026-08-20): persistencia en disco.** El worksheet se
guarda entero a un JSON (`--scan-worksheet-path`, default `data/scan_worksheet.json`, `data/` ya
gitignored -- un solo operador/instancia, sin necesidad de DB) en cada `POST`/`DELETE`, y se carga
una vez al arrancar el proceso; un archivo ausente o corrupto arranca en lista vacía en vez de
tumbar el gateway. Verificado matando y relanzando el proceso del gateway con datos ya guardados:
el corte sobrevivió el restart. Limitación conocida, sin resolver: sin sincronización entre
pestañas/operadores en vivo (cada cliente solo ve lo que trajo en su propio `GET`, no hay
broadcast por WS de esto -- la persistencia en disco no cambia esto, solo sobrevive un restart).
Ver también la nota en `core/contracts/scan.py` sobre por qué esto usa una lista plana en vez del
modelo `ScanWorksheet` (`name` + `cuts`) ya definido ahí.

### Scan Controller conectado a la vista Scan Worksheet (Fase 2, 2026-08-20)

`POST /api/scan/worksheet/{index}/execute` (`adapters/gateway/app.py`) ejecuta
`core.scan_controller.run_scan_cut` sobre el corte elegido del worksheet, reusando el mismo patrón
de job asíncrono (D-12) que los seis endpoints de rutinas: responde `202` con un `job_id`, la MMI
sondea `GET /api/control/jobs/{job_id}` igual que ya hacía para esas seis. `ControlJobStatusResponse.
result` se amplió a `RoutineResult | ScanCutResult` (mismo criterio D-10: ampliar el contrato ya
congelado en vez de inventar un contrato de job separado -- `routine` ya era `str` libre, no el
enum cerrado `RoutineName`, y el resto del sobre es idéntico). Gateado igual que las seis rutinas
(`control.mode == active`, 403 si no). Nuevo panel "Ejecutar corte (Scan Controller)" en
`ScanWorksheetView.vue`: un formulario único para todo el worksheet (no uno por fila, mismo
criterio que Jog/Posicionar en `AntennaControlView.vue`), con selector de índice de corte y los
mismos 11 campos obligatorios sin default que `run_scan_cut` exige
(`azimuth_positioning`/`elevation_positioning` de a cuatro, más `sweep_voltage_magnitude`/
`sweep_tolerance_deg`/`sweep_timeout_s`) -- botón deshabilitado hasta llenarlos todos, mismo
patrón que el resto de la MMI.

Verificado end-to-end contra `radar_emulator` + gateway reales: gating 403 en modo passive, 404 en
índice fuera de rango, `RhiCut` completo con `outcome=success` tanto por HTTP directo como por
click real en el navegador (Playwright/chrome-devtools) -- posicionamiento del eje fijo (azimut),
barrido del eje móvil (elevación) hasta completar dentro de `sweep_tolerance_deg`, detención
limpia. Antes de ejercitarlo hubo que forzar por el canal WS del propio `radar_emulator` las
precondiciones de Rutina 5/6 (`ant.au_on_status`, límites de elevación, `i2t_drive_az`) -- mismo
atajo que ya usaba `spike-fase2/scan_controller_spike.py`, no un flujo real de "encender la unidad
de antena primero" (eso ya existe como rutina propia en la MMI, `AntennaControlView.vue`/card
"Encendido").

**No resuelto por este cambio, sigue abierto:** PEND-RCP-08 (guarda PRF×pulse-width) y PEND-RCP-09
(VCP real) siguen bloqueando que este botón suba HV/radíe o aplique `prf_hz`/`pulse_width_us` --
sigue siendo solo movimiento de antena. Tampoco resuelve la falta de persistencia/sincronización
del worksheet (párrafo de arriba), ni agrega cancelación de un job en curso (misma limitación ya
anotada para las seis rutinas).

### Rutinas de control cableadas al gateway + MMI (Fase 2)

Hasta esta sesión, `core/control_routines/` solo se ejercitaba desde spikes de línea de comandos
— ningún botón de la MMI podía disparar nada, pese a que el criterio de salida M2 del plan
(project-plan.md §8.3) dice literalmente que el operador "powers up the radar ... positions and
moves the antenna". Cerrado con seis endpoints nuevos en `adapters/gateway/app.py`
(`POST /api/control/{general-power-on,transmitter-power-on,receiver-power-on,
antenna-unit-power-on,antenna-movement,antenna-positioning}`, request models nuevos en
`core/contracts/mmi.py`) y su consumo desde la MMI: card "Encendido" en `ControlCenterView.vue`
(las cuatro rutinas de encendido) y vista nueva `AntennaControlView.vue` (ruta
`/antenna-control`, Jog con Rutina 5 + Posicionar con Rutina 6). También se agregó
`SystemInformationView.vue` (ruta `/system-information`, versión/uptime/autoridad de control —
sin backend nuevo, solo consume el `SessionMessage` que ya viajaba por WS).

**Gating de autoridad de control:** los seis endpoints exigen `control.mode == active` (403 si
no) — primer punto donde D-07 se hace cumplir de verdad contra un comando real al HAL, no solo
contra el cambio de modo. Verificado end-to-end (backend con `httpx`/`curl`, frontend en
navegador con Playwright/chrome-devtools) contra `radar_emulator` + gateway reales: gating
403/422, `general-power-on` con `outcome=success` vía HTTP y vía click real en la MMI,
`antenna-movement` confirma movimiento real (jog + detención) por ambos caminos.

**Ningún campo de request lleva default** (mismo criterio que `core/control_routines/`:
`warmup_timeout_s`, `confirm_timeout_s`, `gain_v_per_deg`, `max_voltage`, `tolerance_deg`,
`timeout_s`, `voltage_reference` salvo el `0` explícito de "detener") — en la MMI, cada input
correspondiente arranca vacío y el botón queda deshabilitado hasta que el operador lo llena; no
hay ningún valor sugerido precargado.

**Resuelto (2026-08-20, D-12):** los seis endpoints dejaron de ser síncronos/bloqueantes.
`POST /api/control/*` responde `202` de inmediato con un `job_id` (`ControlJobAccepted`) y arranca
la rutina en un `asyncio.create_task` de fondo; `GET /api/control/jobs/{job_id}` expone
`ControlJobStatusResponse` (`status: running|done`, `result`, `error`). La MMI sondea ese GET cada
400 ms (`useGateway.ts: runControlJob`) hasta `done` — cada vista sigue viendo la misma forma
"await, obtengo el resultado final" que ya tenía, solo que ahora puede tardar de verdad sin dejar
el fetch original colgado. Historial de jobs acotado a 50 (`CONTROL_JOB_HISTORY_LIMIT`, mismo
criterio que `MAX_LOG` en `useGateway.ts`) para no crecer sin límite en una sesión larga.
Verificado con `curl` (202/404/transición running→done) y en navegador real (jog de antena con
"en curso" visible durante el sondeo). Ver D-12 en `docs/alcance/decisiones.md`.

**Resuelto (2026-08-20): cancelación de jobs.** `POST /api/control/jobs/{job_id}/cancel` cancela
un job en curso -- `_start_control_job` ahora guarda la `asyncio.Task` (`app.state.
control_job_tasks`) además del resultado, y el endpoint llama `task.cancel()` y espera a que la
corrutina termine antes de responder. Idempotente: cancelar un job ya terminado devuelve su
estado actual sin error. Botón "Cancelar" agregado a "Posicionar" (`AntennaControlView.vue`) y
"Ejecutar corte" (`ScanWorksheetView.vue`) -- no a "Jog" (ya se detiene mandando 0 V como comando
nuevo, no necesita cancelar la tarea) ni a las cuatro rutinas de encendido en
`ControlCenterView.vue` (pulsos momentáneos, no actuación continua -- ver más abajo).

**Prerequisito de seguridad, resuelto antes de exponer el botón:** ninguna rutina tenía manejo de
cancelación -- si la tarea moría a mitad de un movimiento continuo, el eje seguiría recibiendo esa
referencia de voltaje indefinidamente. Se agregó `except BaseException: <detener eje>; raise`
alrededor del tramo que comanda movimiento en `run_antenna_movement` (`antenna_movement.py`),
`run_antenna_positioning` (`antenna_positioning.py`) y el sondeo de barrido de `run_scan_cut`
(`scan_controller.py`).

**Hallazgo real durante la verificación (no hipotético):** la primera versión atrapaba solo
`except asyncio.CancelledError`, y el botón de cancelar **dejaba la antena girando** en la
verificación real contra `radar_emulator` + navegador -- pymodbus, cuando la cancelación llega
mientras un `await hal.write_analog`/`read_*` está en vuelo (petición Modbus real pendiente), no
deja propagar un `CancelledError` limpio: lo convierte en su propia `ModbusIOException` ("Request
cancelled outside library"). Ese `except` nunca se disparaba, y la limpieza (detener el eje)
nunca corría. Corregido ampliando a `except BaseException` en los tres puntos -- `core/` no puede
importar el tipo exacto de pymodbus para atraparlo puntualmente (límite core/adapters, AGENTS.md),
así que se atrapa cualquier excepción. Para no perder la distinción "cancelado a propósito" vs.
"error de infraestructura genuino" en el mensaje que ve el operador, el gateway ahora marca el
`job_id` en `app.state.control_job_cancel_requested` *antes* de llamar `task.cancel()`, y `_run()`
lo consulta para decidir el texto del error en vez de adivinar por el mensaje de la excepción.
Verificado con 9 corridas con distintos delays (20ms–1s) antes de cancelar más las dos rutas
reales (`antenna-positioning`, `scan_cut`) por HTTP y por click real en el navegador: el eje
siempre terminó detenido (`az_rate_deg_s`/`el_rate_deg_s` ≈ 0) y el job siempre reportó
"cancelado por el operador", no un error de Modbus.

**Resuelto (2026-08-20): botón de cancelar en las cuatro rutinas de encendido.** Sin prerequisito
de seguridad nuevo -- son pulsos digitales momentáneos + sondeo de confirmación, no actuación
continua, así que cancelarlas a mitad de camino no deja nada "corriendo indefinidamente" (distinto
riesgo, menor que Jog/Posicionar/Scan Cut, por eso ninguna necesita el `except BaseException` de
limpieza de eje). `ControlCenterView.vue` ahora rastrea el `job_id` de cada una (mismo callback
`onJobId` de `runControlJob` que ya usaba "Posicionar") y agrega un botón "Cancelar" visible
mientras la rutina está en curso, reusando `POST /api/control/jobs/{job_id}/cancel` ya existente
-- sin cambios de backend. Verificado con `type-check`/`lint` en verde y en navegador real
(chrome-devtools) contra `radar_emulator` + gateway reales: forzadas por WS las tres fuentes de
alimentación de `rx.*` (dejando `rfe_on_status`/`stalo_locked_status` en falso a propósito, mismo
atajo ya usado en otros spikes) para que "Receptor power-on" quedara sondeando confirmación en vez
de fallar de inmediato -- click en "Cancelar" durante el sondeo canceló el job real
(`job ... (receiver_power_on) falló: cancelado por el operador`), botón volvió a su estado normal.
Solo se ejercitó Receptor en vivo; General/Transmisor/Unidad de antena comparten el mismo cableado
línea por línea, no variante propia.
- La sección "Posicionar" de `AntennaControlView.vue` (y "Jog") expone `gain_v_per_deg`/
  `max_voltage`/`tolerance_deg`/`timeout_s`/`voltage_reference` como campos numéricos crudos que
  el operador debe llenar a mano en cada uso, sin memoria entre sesiones ni valor sugerido — es la
  misma falta de dato real (PEND-RCP-07) empujada hasta la UI, no una carencia de esta vista.
  Cuando exista una ganancia/tabla de referencia real, considerar precargar (nunca fijar como
  default silencioso) estos campos desde un perfil por eje.
