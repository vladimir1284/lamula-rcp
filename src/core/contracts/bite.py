"""RCP internal -- eventos del System Status & BITE Manager (plan §4.4:
"Aggregates subsystem status; manages BITE/fault messages, filtering and
history; surfaces ORPG-link health").

Como `control.py`/`safety.py`, no es un contrato RCP<->MMI; es interno a
`core/bite/`. Salud del enlace ORPG queda fuera -- esa interfaz no existe
todavia (PEND-RCP-04), no hay nada que agregar.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from .common import MonotonicMicros
from .hal import SignalId


class BiteTransition(StrEnum):
    FAULT = "fault"
    CLEARED = "cleared"


class BiteEvent(BaseModel):
    """Un cambio de estado de una senal monitoreada -- ni severidad ni
    subsistema son campos propios: severidad no existe como metadato en el
    catalogo de senales (no se inventa una escala sin respaldo), y
    subsistema se deriva de `signal_id` (prefijo antes del primer punto,
    igual convencion que el resto del repo) en vez de duplicarlo."""

    signal_id: SignalId
    transition: BiteTransition
    detail: str
    at_us: MonotonicMicros
