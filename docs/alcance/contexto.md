# Contexto y alcance

## Qué es este sistema

El **Radar Control Processor (RCP)**: el software que controla un radar meteorológico
Gematronik, ingiere los momentos pre-calculados del DSP/DRX, archiva la observación volumétrica
como NEXRAD Level-II, y alimenta esa base data a **ORPG** mediante una emulación completa de RDA
WSR-88D (ICD 2620002). ORPG genera todos los productos meteorológicos; el RCP no genera ninguno.

Es el sucesor en casa de Ravis 1.3 + RCP + Rainbow, sin dependencia de Gematronik. El plan
completo — objetivos, alcance, arquitectura, stack, fases, riesgos — vive en
[Project Plan](../referencia/project-plan.md). Este documento no lo repite: lo traduce a la
convención de documentación que ya usa `radar_emulator` (mismo equipo), y añade el vínculo entre
ambos proyectos.

## Qué no es

!!! warning "No genera productos meteorológicos"
    Esa responsabilidad es 100% de ORPG (proyecto separado, LAMULA ORPG). El RCP entrega base
    data por radial; no hay ruta de producto en casa.

!!! warning "No es el DSP"
    El procesamiento de señal (I/Q → momentos) es un componente/proyecto separado. El RCP
    consume momentos ya calculados sobre un enlace de 1 GbE.

No hay reingeniería de hardware aquí: se asume acceso y conocimiento completo de la interfaz del
radar. No hay hard real-time en este backend (vive en hardware/DRX). No hay hardening de
seguridad (red air-gapped, un solo operador).

## Relación con `radar_emulator`

`radar_emulator` es la **planta** — el otro lado de la interfaz de hardware. Su propia
documentación es explícita: *"El controlador no forma parte de este proyecto"*. Ese
controlador es este repo.

Las dos interfaces que el RCP debe implementar como **cliente/receptor** están ya especificadas
del lado servidor/emisor en `radar_emulator`:

| Interfaz | En `radar_emulator` | Rol del RCP |
|---|---|---|
| Modbus TCP | servidor (`docs/interfaces/modbus.md`) | cliente, único maestro |
| UDP de encoder (`RD100S-ENC-UDP v1`) | emisor (`docs/interfaces/udp-encoder.md`) | receptor |
| WebSocket (operador del banco) | servidor | no aplica al RCP — es la UI del banco de pruebas, no del RCP |

El HAL-simulador del RCP (adaptador de HAL, no el HAL real de campo) es, en la práctica, un
cliente Modbus TCP + receptor UDP conforme a esos dos documentos. Cualquier cambio de versión en
`RD100S-ENC-UDP` o en el mapa Modbus de `radar_emulator` es un cambio de contrato entre proyectos,
no un detalle interno de ninguno de los dos.

## Los cuatro contratos (Fase 0, plan §6)

- **RCP↔MMI** — REST + WebSocket, tipado Pydantic → TypeScript generado.
- **RCP↔DSP/DRX** — stream de momentos sobre 1 GbE. Dependencia externa (proyecto DSP).
- **RCP↔HAL** — interfaz abstracta que implementan por igual el adaptador real y el adaptador
  simulador (contra `radar_emulator`).
- **RCP↔ORPG** — ICD 2620002 fijo, no un esquema propio. Dependencia externa (proyecto ORPG).

## Estado

!!! danger "Repo recién creado, sin código todavía"
    Este documento y el resto de `docs/alcance/` son la traducción inicial del plan de proyecto.
    No hay decisiones de implementación tomadas aún salvo las que el propio plan ya fija (ver
    [Decisiones](decisiones.md)). La Fase 0 (spikes de Modbus/UDP contra `radar_emulator`,
    congelamiento de los cuatro contratos) no se ha ejecutado.
