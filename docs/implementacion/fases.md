# Fases

Estructura tomada de `Lamula RCP — Project Plan.md` §8.2. Este documento no reescribe el plan;
señala en qué fase está el repo y qué hay que hacer primero dentro de ella.

!!! note "Este repo arranca en Fase 0, sin ejecutar todavía"
    Todo lo que existe hoy es el scaffold: estructura de carpetas, `AGENTS.md`,
    `docs/alcance/`. Ningún contrato está congelado, ningún spike se ha corrido.

## Fase 0 — Inception & Architecture (semanas 1–3)

**Foco:** congelar los cuatro contratos (RCP↔MMI, RCP↔DSP, RCP↔HAL, RCP↔ORPG); repo/CI/flujo de
agentes; arquitectura del simulador (del lado RCP: el HAL-simulador que habla con
`radar_emulator`); design system; spikes: render WebGL de PPI, camino Modbus, handshake mínimo
RDA↔ORPG/CM_TCP.

**Salida:** arquitectura y contratos con línea base.

### Lo primero dentro de esta fase

1. Spike Modbus: cliente pymodbus contra una instancia corriendo de `radar_emulator`, leyendo y
   escribiendo los diez unit IDs de la semilla RD100S sobre una sola conexión TCP (FC01/03/05/06/
   15/16). Verifica desde el lado consumidor lo que `radar_emulator` ya resolvió del lado servidor
   (PEND-21 de ese proyecto).
2. Spike UDP: receptor de `RD100S-ENC-UDP v1` — parseo de los 36 octetos, manejo de envolvente de
   `seq`, detección de reinicio del emisor (`seq` y `t_us` retrocediendo juntos), timeout de
   pérdida de stream.
3. Spike RDA↔ORPG: handshake mínimo de loopback (Msg 11/12) contra ORPG real o un stub CM_TCP —
   bloqueado por [PEND-RCP-04](../alcance/pendientes.md#pend-rcp-04-disponibilidad-de-orpg-real-o-stub-cm_tcp-para-fase-0).
4. Congelar los cuatro contratos como esquemas Pydantic versionados.

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
