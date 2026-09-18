# LAMULA RCP

> **Radar Control Processor & Operator MMI** para el radar meteorológico Gematronik.

LAMULA RCP es la solución en casa para el control de radar meteorológico, reemplazando la suite heredada (Ravis 1.3 + RCP + Rainbow) sin dependencias del fabricante original.

El RCP ejecuta la lógica de control del radar, gestiona rutinas de encendido y posicionado, ingiere los momentos calculados por el DSP/DRX sobre un enlace de 1 GbE, archiva la observación volumétrica en formato **NEXRAD Level-II** y alimenta estos datos en tiempo real a **ORPG** mediante una emulación completa del estándar WSR-88D RDA (ICD 2620002).

---

## 🏗 Arquitectura y Principios

- **HAL Intercambiable (Hardware Abstraction Layer):** Una interfaz abstracta única con dos adaptadores intercambiables:
  - Adaptador real (Modbus TCP / Profibus sobre SBC).
  - Adaptador simulador (fiel a la planta, integrado con `radar_emulator`).
- **Orquestación Soft Real-Time:** El backend en Python orquesta el control y la transmisión de datos sin asumir tiempos de respuesta rígidos (*hard real-time* vive en el DSP/DRX/Hardware).
- **Procesamiento de Productos Delegado:** El RCP no genera productos meteorológicos; archiva observaciones base y sirve como RDA para **ORPG** (LAMULA ORPG), quien genera los productos.
- **MMI Web (Vue 3 + TypeScript):** Interfaz para operador único en red privada *air-gapped* que reproduce el conjunto funcional operativo de Ravis (Control Center, Visualización del Sistema, Control de Antena, Scan Worksheet, BITE, Visores PPI/RHI/ASCOPE, etc.).

---

## 🛠 Stack Tecnológico

- **Backend:** Python 3.12, FastAPI, Uvicorn, asyncio, Pydantic v2, pymodbus, NumPy.
- **Frontend (MMI):** Vue 3, TypeScript, Vite, Pinia, Tailwind CSS, shadcn-vue / Reka UI, PixiJS (WebGL para PPI/RHI), uPlot (ASCOPE).
- **Contratos:** Definiciones centralizadas en `src/core/contracts/` con generación automática de tipos para TypeScript en MMI.
- **Documentación:** MkDocs con tema Material.

---

## 📁 Estructura del Repositorio

```text
.
├── contract/             # Esquemas y anclas de contratos vendorizados (UPSTREAM.toml)
├── docs/                 # Documentación del proyecto (alcance, interfaces, operaciones, fases)
├── mmi/                  # Frontend en Vue 3 / TypeScript para la MMI del operador
├── src/                  # Código fuente del backend (core y adaptadores)
│   ├── adapters/         # Adaptadores HAL, DSP, Modbus, UDP, etc.
│   └── core/             # Lógica central, controladores, contratos Pydantic y rutinas
├── tests/                # Pruebas unitarias y de integración (pytest)
├── tools/                # Herramientas auxiliares y scripts de verificación de contratos
├── AGENTS.md             # Guía para agentes de desarrollo e instrucciones de trabajo
├── Makefile              # Atajos para verificación local y CI (make check, test, docs)
├── mkdocs.yml            # Configuración del sitio de documentación
└── pyproject.toml        # Configuración del proyecto Python y dependencias
```

---

## 🚀 Desarrollo y Comandos Útiles

El proyecto utiliza [`uv`](https://github.com/astral-sh/uv) para la gestión de entornos virtuales y dependencias de Python, y `pnpm` / `npm` para el frontend en `mmi/`.

### Ejecutar comprobaciones (CI / Gates locales)

Puedes ejecutar los mismos checks que corre el CI a través del `Makefile`:

```bash
# Ejecuta lint (comprobación de contratos vendorizados), tests de pytest y compilación estricta de documentación
make check

# Correr solo los tests de Python
make test

# Verificar el estado de la documentación
make docs

# Verificar tipos en el frontend MMI
make mmi-check
```

### Ejecución de Pruebas Manualmente

```bash
uv run pytest tests -q
```

### Compilar y Servir la Documentación Localmente

```bash
uvx --with mkdocs-material==9.* mkdocs serve
```

---

## 📜 Documentación del Proyecto

La documentación detallada se encuentra en el directorio `docs/` y se compila con MkDocs:

- **Contexto y Alcance:** `docs/alcance/contexto.md`
- **Decisiones de Diseño:** `docs/alcance/decisiones.md`
- **Contrato RCP↔DSP:** `docs/interfaces/dsp.md`
- **Plan de Proyecto Original:** `docs/referencia/project-plan.md`
- **Fases de Implementación:** `docs/implementacion/fases.md`
