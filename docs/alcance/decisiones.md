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

**Pendiente dentro de esta decisión:** PrimeVue vs. shadcn-vue (Reka UI) para componentes —
marcado explícitamente "decisión necesaria" en el plan (§5). Ver
[pendientes.md](pendientes.md#pend-rcp-02-libreria-de-componentes-frontend).

---

## D-09 · Empaquetado offline, air-gapped

**Decisión.** Docker Compose (bundle de imágenes offline) como opción primaria; PyInstaller como
alternativa. Sin acceso a paquetes en el target de despliegue.

**Por qué.** Plan §5, §12: entorno de desarrollo/CI puede tener acceso a paquetes (o un mirror
interno), el target de despliegue no.
