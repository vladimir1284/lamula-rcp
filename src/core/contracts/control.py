"""RCP core -- rutinas de control (Fase 2, plan §4.3/§8.2: "seis rutinas de control").

Forma comun del resultado de una rutina. No es un contrato RCP<->MMI (eso es
`mmi.py`, que puede exponer esto envuelto en su propio mensaje mas adelante,
igual que hizo `DspStreamStatus` en D-10); es interno a `core/control_routines/`.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from .common import MonotonicMicros
from .hal import SignalId


class RoutineName(StrEnum):
    """Las seis rutinas del plan (§4.3). Solo `GENERAL_POWER_ON` tiene
    implementacion en `core/control_routines/` por ahora; el resto queda
    listado aqui para que el contrato no se reinvente rutina a rutina."""

    GENERAL_POWER_ON = "general_power_on"
    TRANSMITTER_POWER_ON = "transmitter_power_on"
    RECEIVER_POWER_ON = "receiver_power_on"
    ANTENNA_UNIT_POWER_ON = "antenna_unit_power_on"
    ANTENNA_MOVEMENT = "antenna_movement"
    ANTENNA_POSITIONING = "antenna_positioning"


class RoutineOutcome(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    # A diferencia de FAILED (nunca escribe nada si las precondiciones no se
    # cumplen), INTERRUPTED es una rutina que si llego a comandar algo pero
    # tuvo que detenerse a mitad de camino -- p.ej. la guarda de seguridad de
    # parametros (core/safety_guard/) rechazo continuar durante un
    # movimiento de antena.
    INTERRUPTED = "interrupted"


class RoutineStepResult(BaseModel):
    """Un chequeo de precondicion o una escritura de comando dentro de la rutina."""

    signal_id: SignalId
    ok: bool
    detail: str


class RoutineResult(BaseModel):
    routine: RoutineName
    outcome: RoutineOutcome
    steps: list[RoutineStepResult]
    at_us: MonotonicMicros
