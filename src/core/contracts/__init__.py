"""Contratos congelados en Fase 0 (docs/implementacion/fases.md).

RCP<->MMI, RCP<->DSP/DRX y RCP<->HAL viven aqui, versionados como esquemas
Pydantic. RCP<->ORPG queda fuera deliberadamente: es el ICD 2620002 fijo, no
se define localmente (AGENTS.md), y el spike de handshake esta bloqueado por
PEND-RCP-04.
"""
