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
`Lamula RCP — Project Plan.md`. El plan no dice literalmente qué reloj usa el feed a ORPG.
Confirmar con el equipo antes de congelar el contrato RCP↔ORPG en Fase 0: NEXRAD Level-II exige
timestamp absoluto de la observación, así que probablemente no hay alternativa, pero debe quedar
explícito y no asumido.

### PEND-RCP-02 · Librería de componentes frontend

Plan §5: "PrimeVue o shadcn-vue (Reka UI) — *decisión necesaria*". Sin resolver. No bloquea la
Fase 0 (contratos + spikes backend), sí bloquea el arranque de la MMI en Fase 1.

### PEND-RCP-03 · Herramienta de empaquetado de dependencias Python para el target offline

El plan (§5, §12) fija Docker Compose como opción primaria y PyInstaller como alternativa, pero
no fija cómo se vendorizan los wheels de Python para el mirror interno / build offline (pip-tools
+ index local, `uv` con lockfile, o imagen Docker que ya trae todo). Decisión de tooling, no de
arquitectura — resolver en Fase 0 al montar CI.

### PEND-RCP-04 · Disponibilidad de ORPG real o stub CM_TCP para Fase 0

El plan (§8.2, Fase 0) pide un "handshake mínimo RDA↔ORPG" como spike de la Fase 0. No está
confirmado si hay acceso, en esta etapa, a un build real de ORPG o si hace falta construir un
stub CM_TCP propio antes de poder ejecutar ese spike. Sin esto, el spike de loopback (Msg 11/12)
no tiene con qué hablar.

### PEND-RCP-05 · El DSP externo no tiene aún una interfaz de referencia ejecutable

El plan asume el contrato RCP↔DSP "acordado con el proyecto DSP" (plan §6, §12), pero no hay,
al momento de crear este repo, un simulador o especificación del stream de momentos equivalente
a lo que `radar_emulator` ya ofrece para HAL. La ingestión DSP/DRX de Fase 1 puede quedar
bloqueada por esto igual que Fase 0 lo estaría sin `radar_emulator`.
