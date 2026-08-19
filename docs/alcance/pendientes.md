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
