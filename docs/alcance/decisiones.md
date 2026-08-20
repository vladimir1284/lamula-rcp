# Decisiones de diseño

Registro de las decisiones ya tomadas. El agente de desarrollo **no debe revertir ninguna sin
discutirlo**. A diferencia de `radar_emulator`, aquí casi todas provienen directamente del
documento de plan de proyecto ([Project Plan](../referencia/project-plan.md)), no de una sesión de diseño de
este repo — se citan con la sección de origen.

---

## D-01 · El RCP es cliente Modbus, único maestro

**Decisión.** El HAL-simulador del RCP implementa un cliente Modbus TCP. Nunca un servidor.

**Por qué.** Es la contraparte fijada del lado servidor en `radar_emulator`
(`docs/interfaces/modbus.md`: *"El emulador actúa como servidor Modbus TCP. El controlador es
el cliente y el único maestro"*). No es una decisión de este repo, es la mitad que falta de una
decisión ya tomada en el otro.

---

## D-02 · ORPG feed vive en el RCP, no en el DSP

**Decisión.** El RCP archiva la observación volumétrica y alimenta ORPG. El DSP solo entrega
momentos al RCP.

**Por qué.** Plan, nota de revisión punto 1: el RCP es el nodo que gestiona el archivo de
observaciones; el DSP es headless. *Consecuencia entre proyectos:* el plan del DSP debe
actualizarse para quitar su contrato `DSP↔ORPG` — no es tarea de este repo, pero bloquea si no
ocurre en paralelo (ver [pendientes](pendientes.md)).

---

## D-03 · Enlace RCP↔DSP es 1 GbE

**Decisión.** Fuera de la FPGA, 1 Gb Ethernet basta. El camino de alta tasa (ADC/DDC/decimación,
10GbE dentro del DRX) queda interno a la FPGA/DRX, fuera de alcance del RCP.

**Por qué.** Plan, nota de revisión punto 2.

---

## D-04 · Solo se archiva la observación volumétrica, formato NEXRAD Level-II

**Decisión.** El RCP archiva base data (Z/V/W + dual-pol, por volumen), no productos derivados.
Level-II es el formato primario de archivo/salida.

**Por qué.** Plan, nota de revisión punto 3. La generación de producto es responsabilidad
exclusiva de ORPG.

---

## D-05 · La emulación RDA se implementa completa, no parcial

**Decisión.** RCP↔ORPG (ICD 2620002) es un entregable crítico de Stage 1 completo: máquina de
estados RDA, Msg 31/1, Msg 2 (status), Msg 11/12 (loopback), Msg 6 (control), Msg 13/15
(clutter/bypass), VCP, servidor TCP con login. No un encoder parcial.

**Por qué.** Plan, nota de revisión punto 4: el sistema depende 100% de ORPG para producto, así
que esta interfaz no puede quedar a medias.

---

## D-06 · HAL con dos adaptadores intercambiables, nada más arriba distingue cuál

**Decisión.** Una interfaz HAL abstracta; adaptador real (Modbus/Profibus vía SBC) y adaptador
simulador (contra `radar_emulator`) la implementan por igual.

**Por qué.** Plan §4.3: valida en simulador ahora, comisiona en hardware después. El adaptador
simulador es, en la práctica, el cliente Modbus + receptor UDP descritos en
[contexto.md](contexto.md#relacion-con-radar_emulator).

---

## D-07 · Single operator, arbitraje de control colapsado a passive/active

**Decisión.** Se descarta el protocolo RCL heredado y el arbitraje de cuatro niveles de Ravis.
Un solo toggle passive (monitor) / active (control).

**Por qué.** Plan §1, §4.3: un solo operador, red air-gapped, sin requisito de multi-operador ni
control-authority arbitration.

---

## D-08 · Stack: Python 3.12 + FastAPI + Pydantic v2 + asyncio; Vue 3 + TS + Vite en frontend

**Decisión.** Backend según plan §5: FastAPI/Uvicorn, Pydantic v2 para contratos, asyncio para
orquestación soft-real-time, pymodbus para el cliente Modbus, NumPy/SciPy para momentos y
codificación Level-II, SQLite para metadata de scan/status/evento. Frontend: Vue 3 + TypeScript +
Vite, Pinia + Vue Router, Tailwind, PixiJS (PPI/RHI) + uPlot (ASCOPE).

**Por qué.** Plan §5, tabla completa. Preferencia del equipo ya fijada, no decisión de este repo.

**Resuelto (2026-08-19), primer intento:** componentes = PrimeVue. El plan (§5) marcaba esto
"decisión necesaria" entre PrimeVue y shadcn-vue (Reka UI). Se eligió PrimeVue por los widgets
batteries-included (DataTable, Dialog, Knob, Gauge) que se necesitan para controles de antena y
BITE en Fase 2, frente al costo de construirlos a mano sobre un set headless.

**Revertido el mismo día, al scaffoldear la MMI:** `primevue@5.0.1` (la última versión al momento
de instalar) mostró en dev un banner "Invalid PrimeUI License" — PrimeVue se relicenció bajo
"PrimeUI" a partir de v5: ya no es MIT libre sin condiciones, requiere license key incluso en el
tier gratuito ("Community"), con límites de tamaño de organización (< $1M USD de ingresos
anuales, < 5 developers, < 10 empleados, < $3M de capital externo) y renovación anual de
elegibilidad. Esto no se supo hasta después de tomar la decisión — la elección original no pesó
licenciamiento porque hasta v4 PrimeVue era MIT sin condiciones.

**Resuelto definitivamente:** componentes = **shadcn-vue (Reka UI)**. Sin licencia de terceros
que gestionar (Reka UI es MIT); el costo es construir a mano los widgets no estándar (knob,
gauge) que Fase 2 va a necesitar para controles de antena/BITE — se acepta ese costo a cambio de
no depender de una license key en un sistema air-gapped de shelf-life largo. Ver
[pendientes.md](pendientes.md#pend-rcp-02-libreria-de-componentes-frontend).

---

## D-09 · Empaquetado offline, air-gapped

**Decisión.** Docker Compose (bundle de imágenes offline) como opción primaria; PyInstaller como
alternativa. Sin acceso a paquetes en el target de despliegue.

**Por qué.** Plan §5, §12: entorno de desarrollo/CI puede tener acceso a paquetes (o un mirror
interno), el target de despliegue no.

**Resuelto (2026-08-19):** vendorizado de wheels Python vía `uv` con lockfile (`uv.lock`) —
resolución/instalación en CI, wheels cacheados en capa Docker. Ver
[pendientes.md](pendientes.md#pend-rcp-03-herramienta-de-empaquetado-de-dependencias-python-para-el-target-offline).

---

## D-10 · `core/contracts/mmi.py` se extiende con `DspStreamStatus`, no con momentos por WS

**Decisión (2026-08-19).** Al conectar el stub de stream DSP
(`spike-fase0/dsp_moment_stream_spike.py`) al gateway (Fase 1), el contrato RCP↔MMI ya congelado
se amplía con un campo `dsp: DspStreamStatus | None` en `SystemStatusSnapshot` (contadores +
último volumen/elevación/status), **no** con un tipo de mensaje WS que lleve momentos completos.

**Por qué.** `mmi.py` documenta explícitamente que las vistas PPI/RHI/ASCOPE (que sí necesitarían
momentos en vivo) son de Fase 2/3 — resolver la forma de ese streaming ahora sería inventarla sin
acuerdo del equipo, justo lo que el contrato existe para evitar. Un campo de estado resumido no
choca con eso: no es la vista PPI, es visibilidad de "¿está llegando el stream, hasta dónde
llegó?" para el operador/diagnóstico.

**Nota:** es una ampliación de un contrato marcado como congelado (AGENTS.md), no una
reinterpretación de algo ya decidido — se registra aquí para que quede trazable. Ver
[pendientes.md](pendientes.md#pend-rcp-05-el-dsp-externo-no-tiene-aun-una-interfaz-de-referencia-ejecutable).

---

## D-11 · PEND-RCP-07 (Rutinas 2–6) se acepta como suficientemente confirmado por silencio

**Decisión (2026-08-20).** El usuario indica que el product expert no ha objetado nada de
`docs/operacion/rutinas-control.md` para las Rutinas 2–6 (solo la Rutina 1 tuvo feedback
explícito, absorbido como PEND-27/PEND-28 en `radar_emulator`). Con esto, PEND-RCP-07 se cierra
como "aceptado", se sigue con otro trabajo de Fase 2/3.

**Por qué.** Decisión operativa del usuario para no bloquear el avance, no una confirmación
técnica nueva del experto.

**Salvedad importante:** esto es **inferencia por ausencia de objeción**, no una revisión línea
por línea confirmada como la que sí ocurrió para la Rutina 1 (PEND-RCP-06). Si en algún momento
el product expert señala algo concreto sobre Rutinas 2–6, tiene prioridad sobre esta decisión sin
necesidad de discutirla primero (a diferencia del resto de decisiones de este documento).
