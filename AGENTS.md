# Instrucciones para el agente de desarrollo

## Antes de escribir código

Lee, en este orden:

1. `docs/alcance/contexto.md` — qué es y qué no es este sistema, y cómo se relaciona con
   `radar_emulator` (el otro proyecto del mismo equipo).
2. `docs/alcance/decisiones.md` — decisiones ya congeladas por el plan de proyecto. **Ninguna se
   revierte sin discutirlo.**
3. `docs/alcance/pendientes.md` — huecos abiertos, incluidos los heredados de `radar_emulator`
   (mismo contrato Modbus/UDP, mismos valores provisionales del otro lado).
4. `docs/implementacion/fases.md` — el plan de trabajo.

## Lo primero que hay que hacer

La **fase 0**: congelar los cuatro contratos (RCP↔MMI, RCP↔DSP, RCP↔HAL, RCP↔ORPG) y verificar,
contra una instancia real de `radar_emulator`, que el cliente Modbus del RCP interroga
correctamente los diez unit IDs de la semilla RD100S y que el receptor UDP decodifica el stream
`RD100S-ENC-UDP v1`. Sin esto no hay HAL-simulador que valga.

## Reglas que no se negocian

- **`src/core/` no importa nada de `src/adapters/`.** HAL real y HAL-simulador (contra
  `radar_emulator`) son intercambiables detrás de una sola interfaz; nada por encima del HAL
  distingue cuál está activo.
- **Hard real-time vive en hardware/DRX, no en este backend.** El core hace orquestación soft
  real-time: nunca asumas que un `await` responde en el mismo tick que lo dispara.
- **Dos relojes, no uno.** El archivo Level-II y el feed a ORPG llevan hora de pared real (es
  observación meteorológica con marca de tiempo absoluta — NEXRAD lo exige). La telemetría interna
  de diagnóstico y el scheduling soft-real-time pueden usar reloj monótono. No mezclar los dos
  sentidos bajo un solo campo `timestamp`. **Esto es una asunción de diseño, no está en el plan
  original explícitamente — confirmar con el equipo antes de congelarlo en el contrato RCP↔ORPG.**
- **El RCP↔ORPG es el ICD 2620002 fijo, no un esquema propio.** No lo reinterpretes por
  conveniencia; cualquier ambigüedad se discute con el proyecto LAMULA ORPG, no se resuelve
  localmente.
- **Este sistema apunta a un único modelo de radar** (a diferencia de `radar_emulator`, que es
  deliberadamente configurable para cualquier radar). No repliques aquí la abstracción
  "configuración JSON sin nada cableado" solo por simetría con el emulador — el plan fija radar
  único, operador único, red air-gapped.
- Marca `// PEND-nn` en cada punto donde uses un valor provisional, igual que `radar_emulator`.

## Cuando encuentres una contradicción

Este repo es nuevo: casi todo en `docs/alcance/` es traducción del documento de plan de proyecto
(`docs/referencia/project-plan.md`) a la convención de documentación de
`radar_emulator`. Si algo no cuadra entre el plan y esta traducción, **pregunta antes de
elegir** — el documento de plan manda.

## Documentación

El sitio se compila con `mkdocs build --strict`. Si añades una página, entra en el `nav` de
`mkdocs.yml` o el build falla.
