# Fases

Estructura tomada de [Project Plan](../referencia/project-plan.md) §8.2. Este documento no reescribe el plan;
señala en qué fase está el repo y qué hay que hacer primero dentro de ella.

!!! note "Fase 0 en curso"
    Spikes de Modbus, UDP y RDA↔ORPG ya corridos — ver `spike-fase0/RESULTADO.md` y
    `spike-fase0/RESULTADO-rda-orpg.md` en la raíz del repo. Tres de los cuatro contratos
    (RCP↔HAL, RCP↔DSP/DRX, RCP↔MMI) ya están congelados como esquemas Pydantic en
    `src/core/contracts/`. Falta: RCP↔ORPG — el handshake mínimo ya corre contra un stub CM_TCP
    propio ([PEND-RCP-04](../alcance/pendientes.md#pend-rcp-04-disponibilidad-de-orpg-real-o-stub-cm_tcp-para-fase-0)
    parcialmente resuelto). Dirección del eco del loopback confirmada por el usuario (producción
    real, no sign-off de LAMULA ORPG); falta alinear el spike a esa dirección y acceso a un ORPG
    real antes de congelar el contrato.

## Fase 0 — Inception & Architecture (semanas 1–3)

**Foco:** congelar los cuatro contratos (RCP↔MMI, RCP↔DSP, RCP↔HAL, RCP↔ORPG); repo/CI/flujo de
agentes; arquitectura del simulador (del lado RCP: el HAL-simulador que habla con
`radar_emulator`); design system; spikes: render WebGL de PPI, camino Modbus, handshake mínimo
RDA↔ORPG/CM_TCP.

**Salida:** arquitectura y contratos con línea base.

### Lo primero dentro de esta fase

1. ✅ Spike Modbus: cliente pymodbus contra una instancia corriendo de `radar_emulator`, leyendo y
   escribiendo los diez unit IDs de la semilla RD100S sobre una sola conexión TCP (FC01/03/05/06/
   15/16). Verifica desde el lado consumidor lo que `radar_emulator` ya resolvió del lado servidor
   (PEND-21 de ese proyecto). Ver `spike-fase0/RESULTADO.md`.
2. ✅ Spike UDP: receptor de `RD100S-ENC-UDP v1` — parseo de los 36 octetos, manejo de envolvente de
   `seq`, detección de reinicio del emisor (`seq` y `t_us` retrocediendo juntos), timeout de
   pérdida de stream, más las ocho degradaciones de §6 disparadas en vivo desde el emulador
   (pérdida, ráfaga, duplicación, congelación, encoder inválido, salto de secuencia, silencio).
   Ver `spike-fase0/RESULTADO.md`.
3. ✅ Spike RDA↔ORPG: handshake mínimo de loopback (Msg 11/12), corrido contra un stub CM_TCP
   propio (no hay ORPG real disponible todavía) — ver `spike-fase0/RESULTADO-rda-orpg.md`.
   Dirección del eco confirmada por el usuario (legacy `RDA_Backend_Py` corrió en producción real
   haciendo ingesta de productos al ORPG); el spike todavía implementa la lectura literal del ICD,
   no esa dirección — ver [PEND-RCP-04](../alcance/pendientes.md#pend-rcp-04-disponibilidad-de-orpg-real-o-stub-cm_tcp-para-fase-0).
4. Congelar los cuatro contratos como esquemas Pydantic versionados:
   - ✅ RCP↔HAL, RCP↔DSP/DRX, RCP↔MMI — `src/core/contracts/{hal,dsp,mmi}.py`.
   - ⏸️ RCP↔ORPG — sigue pospuesto: falta alinear el spike a la dirección de eco confirmada y
     acceso a un ORPG real. Es el ICD 2620002 fijo
     (AGENTS.md); no se define localmente sin el equipo LAMULA ORPG.

## Fase 1 — Foundations & Simulator (semanas 4–10)

Interfaz HAL + adaptador simulador (HW + stream DSP/DRX + inyección de fallos); esqueleto del
gateway; shell de la MMI (Control Center, conectar, log de mensajes); primer pipe de datos en
vivo sim→WS→PPI.

**Salida:** M1 — vertical slice.

!!! note "Fase 1 en curso"
    ✅ Adaptador `hal_sim` (`src/adapters/hal_sim/SimulatedHAL`): cliente Modbus TCP (una
    conexión, diez unit IDs) + receptor UDP de encoder, contra un catálogo de 111 señales
    vendorizado de `radar_emulator` — ver `spike-fase1/RESULTADO-hal-sim.md`, probado contra una
    instancia real de `radar_emulator`, no un stub propio.

    ✅ Esqueleto del gateway (`src/adapters/gateway`, FastAPI): `GET /api/status`,
    `POST /api/control`, `WS /ws` (`SessionMessage`/`AntennaMessage`/`HeartbeatMessage`/
    `OperatorEventMessage` de `core/contracts/mmi.py`) sobre `SimulatedHAL` — primer "pipe de
    datos en vivo sim→WS" probado extremo a extremo, ver `spike-fase1/RESULTADO-gateway.md`.
    Sin autenticación, sin persistencia de sesión, sin buffer de eventos para reconexión.

    ✅ Stream DSP conectado al gateway (`src/adapters/dsp/MomentStreamReceiver`): recibe el
    stub `dsp_moment_stream_spike.py --role dsp` y expone estado resumido
    (`DspStreamStatus`) en `GET /api/status` — ver `spike-fase1/RESULTADO-dsp-gateway.md`.
    Decisión: no se streamean momentos completos por WS todavía (eso es la vista PPI de
    Fase 2/3); `core/contracts/mmi.py` se extendió solo con ese campo de estado.

    ✅ Inyección de fallos: `SimulatedHAL` verificado contra las degradaciones reales de
    `radar_emulator` (`encoder_invalid`, `freeze`, `silence`, vía su canal WS de control) — ver
    `spike-fase1/RESULTADO-fault-injection.md`.

    ✅ Shell MMI (`mmi/`, Vue3+TS+Vite+Pinia+Vue Router, shadcn-vue/Reka UI+Tailwind v4 — PEND-RCP-02
    revertido de PrimeVue a shadcn-vue el mismo día por licenciamiento, ver D-08): vista Control
    Center que conecta al gateway (REST `/api/status`, WS `/ws`), muestra autoridad de control con
    botón tomar/ceder, posición de antena en vivo y log de mensajes. Probado en navegador contra el
    gateway + `radar_emulator` reales — ver `spike-fase1/RESULTADO-mmi-shell.md`.

    Con esto quedan cubiertos todos los puntos de Fase 1 listados arriba.

## Fase 2 — Control, Safety & Scanning (semanas 11–18)

Las seis rutinas de control sobre el simulador; guarda de seguridad de parámetros; movimiento y
posicionamiento de antena; Scan Worksheet manual; scheduler de volumen automático; System
Visualization + BITE.

**Salida:** M2 — control activo sobre simulador.

!!! note "Fase 2 en curso"
    ✅ Primera rutina de control (`core/control_routines/general_power_on.py`): "general radar
    power-on" contra `SimulatedHAL`, elegida como punto de entrada porque
    `sys.turn_on_radar_conmand` no tiene ningún bloque de lógica del lado de `radar_emulator` (a
    diferencia de `tx.fsm`) — sienta el patrón de `core/control_routines/` sin arrastrar
    sincronización contra un FSM simulado. Precondiciones + pulso + confirmación probados contra
    una instancia real, ver `spike-fase2/RESULTADO-general-power-on.md`.

    ✅ Guarda de seguridad de parámetros, parte de límites de antena
    (`core/safety_guard/antenna_limits.py`): rechaza un movimiento de elevación propuesto contra
    `ant.el_upper_limit_status`/`el_lower_limit_status` (fin de carrera físico), y de azimut
    contra `ant.i2t_drive_az_status` (protección térmica del motor) — ver
    `spike-fase2/RESULTADO-parameter-guard.md`, probado contra una instancia real de
    `radar_emulator`. Consumida por las Rutinas 5 y 6.

    ✅ Rutina 5 — movimiento de antena (`core/control_routines/antenna_movement.py`): comanda
    `ant.speed_reference_driver_{az,el}` (voltios, no grados/s — hallazgo nuevo, ver
    `spike-fase2/RESULTADO-antenna-movement.md`) tras chequear `ant.au_on_status` y la guarda de
    límites de antena, y sigue consultando la guarda mientras se mueve porque el simulador no
    corta el drive de azimut por sí mismo ante la falla térmica. Probada contra una instancia
    real de `radar_emulator`, incluidos los casos de interrupción a mitad de camino.

    ✅ Rutina 6 — posicionamiento de antena (`core/control_routines/antenna_positioning.py`),
    última de las seis: control proporcional apoyado en la Rutina 5 en cada paso, sin ningún
    valor propio de ganancia/tolerancia/timeout (parámetros obligatorios, sin default — a
    diferencia del resto, aquí no hay ni siquiera un marcador de posición del simulador que
    tomar prestado). Probada contra una instancia real de `radar_emulator`, ver
    `spike-fase2/RESULTADO-antenna-positioning.md`. Limitación conocida sin resolver: sin cálculo
    de distancia de frenado, puede sobrepasar el objetivo mientras el eje desacelera.

    ✅ Rutina 2 — encendido del transmisor (`core/control_routines/transmitter_power_on.py`),
    hasta `tx.ready_status` únicamente (no sube HV ni radía — decisión de alcance explícita, ver
    docstring). Única rutina con secuencia y temporizador reales del lado del simulador
    (`tx.fsm`); probada contra una instancia real de `radar_emulator`, incluida una corrida
    completa esperando el caldeo real de ~180 s, ver
    `spike-fase2/RESULTADO-transmitter-power-on.md`. Hallazgo: la transición de encendido del
    `tx.fsm` no exige los seis interlocks (solo los exige al subir HV, fuera del alcance de esta
    rutina); se chequean igual como precondición propia del RCP.

    ✅ Rutina 3 — encendido del receptor (`core/control_routines/receiver_power_on.py`): tres
    fuentes de alimentación como precondición, pulso a `rx.turn_on_rfe_conmand` (confirmado como
    flanco en `radar_emulator/docs/interfaces/modbus.md`), confirmación vía
    `rfe_on_status`/`stalo_locked_status`. El subsistema `rx` no tiene ningún bloque de lógica en
    la semilla — el camino de éxito solo se probó forzando también esas señales, ver
    `spike-fase2/RESULTADO-receiver-power-on.md`.

    ✅ Rutina 4 — encendido de la unidad de antena
    (`core/control_routines/antenna_unit_power_on.py`), última de las seis: radomo cerrado como
    precondición, `ant.turn_on_off_au_conmand` tratado como nivel (no pulso — mismo criterio que
    `enable_drive_az/el_conmand` en la Rutina 5, sin confirmar). Mismo problema que la Rutina 3:
    ningún bloque calcula `au_on_status` ni los `drive_{az,el}_ok_status`, ver
    `spike-fase2/RESULTADO-antenna-unit-power-on.md`.

    Con esto, las seis rutinas del plan tienen primer borrador implementado y probado contra el
    simulador.

    ✅ System Status & BITE Manager (`core/bite/manager.py`): sondea un conjunto fijo de señales
    `*_ok_status`/`*_fault_status`/`*_over_current_status` (más las dos excepciones de
    protección térmica de antena) y reporta solo transiciones sano↔falla, con historial acotado y
    filtrado por subsistema — ver `spike-fase2/RESULTADO-bite-manager.md`. A diferencia de las
    seis rutinas, no depende de ninguna confirmación del product expert (agregación mecánica, no
    procedimiento operativo nuevo). Salud del enlace ORPG (parte del plan §4.4) fuera de alcance
    porque esa interfaz no existe (PEND-RCP-04).

    ✅ BITE cableado al gateway (`adapters/gateway/app.py`): tarea de fondo que sondea
    `BiteManager` cada 0.5 s (independiente de cuántos clientes WS estén conectados, evita la
    condición de carrera de sondear el mismo estado mutable desde el loop de cada conexión) y
    hace broadcast de `BiteEventMessage`; `GET /api/status.active_bite_faults` expone el
    snapshot. Probado extremo a extremo (REST + WS) contra `radar_emulator` real, ver
    `spike-fase2/RESULTADO-bite-gateway.md`. Falta la vista en la MMI (`mmi/`) que lo consuma.

    ✅ Contrato de datos del Scan Worksheet manual (`core/contracts/scan.py`): `PpiCut`/`RhiCut`
    (unión discriminada, mismo patrón que `WsMessage` en `mmi.py`), con `prf_hz`/`pulse_width_us`
    como datos puros — todavía sin ejecutor (ni guarda que los valide, PEND-RCP-08, ni adaptador
    de forma de onda). Deliberadamente **no** es VCP: ese concepto es de `RCP↔ORPG` y está
    asignado a Fase 3 (PEND-RCP-09, nuevo). Sin Scan Controller que lo consuma todavía.

    ⏸️ Sin resolver: secuencia/criterio de éxito de la Rutina 1 no confirmados con el product
    expert (PEND-RCP-06); para las Rutinas 2–6 (PEND-RCP-07): tiempo de caldeo/umbral de
    sobrecorriente reales para la Rutina 2, tiempo de enganche del STALO para la Rutina 3, si
    la unidad de antena es pulso o nivel para la Rutina 4, la ganancia real volt→grados/s para la
    Rutina 5, y la tolerancia/timeout/perfil de frenado reales para la Rutina 6; la mitad de la
    guarda de parámetros sobre PRF × pulse-width, bloqueada por falta de Scan Worksheet y de un
    contrato de forma de onda (PEND-RCP-08); reconciliación con VCP real (PEND-RCP-09); Scan
    Controller que consuma el Worksheet; scheduler de volumen; System Visualization (vista MMI).

## Fase 3 — Data Views, Calibration, Archive & ORPG Feed (semanas 19–27)

PPI/RHI/ASCOPE completos + gestión de color de 256 niveles + multi-tipo + freeze/zoom; control
DRX/RSP + calibración de un punto/TX; archivo Level-II de la observación volumétrica; emulación
RDA completa + feed Level-II por radial a ORPG; máquina de estados, status, loopback, VCP y
comandos de control entrantes.

**Salida:** M3 — capacidad completa de operador + feed a ORPG sobre simulador.

## Fase 4 — Hardening & Simulator Acceptance (semanas 28–34)

Rendimiento, pruebas de resistencia/soak, cobertura completa de inyección de fallos/BITE, suite
de aceptación basada en simulador, conformidad RDA/ORPG contra ORPG real o stubbed, instalador
offline, documentación de operador, plan de ensayo de puesta en marcha.

**Salida:** M4 — aceptación en simulador, listo para comisionamiento.

## Lo primero que debe hacer el agente

1. Leer [Contexto](../alcance/contexto.md) y [Decisiones](../alcance/decisiones.md) enteros.
   Ninguna decisión se revierte sin discutirlo.
2. Leer [Pendientes](../alcance/pendientes.md), incluidos los heredados de `radar_emulator`.
3. Ejecutar los spikes de la **Fase 0** y reportar el resultado antes de escribir código de
   producción del HAL-simulador o de los contratos.
