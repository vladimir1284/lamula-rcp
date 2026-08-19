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

## Fase 2 — Control, Safety & Scanning (semanas 11–18)

Las seis rutinas de control sobre el simulador; guarda de seguridad de parámetros; movimiento y
posicionamiento de antena; Scan Worksheet manual; scheduler de volumen automático; System
Visualization + BITE.

**Salida:** M2 — control activo sobre simulador.

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
