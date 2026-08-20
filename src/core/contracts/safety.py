"""RCP internal -- resultado de la guarda de seguridad de parametros (plan
§4.3/§4.4: "Parameter-Safety Guard").

Como `control.py`, no es un contrato RCP<->MMI; es interno a
`core/safety_guard/`. Solo modela la parte de la guarda que necesita
contexto de una senal HAL viva (limites de antena, `signal_id`/`at_us` de
una lectura real -- ver `core/safety_guard/antenna_limits.py`). La otra
mitad del plan -- "prevention of pulse-width x PRF combinations that would
damage the klystron/magnetron" -- resulto no necesitar ninguna senal HAL
(el hardware se autoprotege, ver PEND-RCP-08): es una validacion de
software pura sobre datos que el operador ya escribio, sin nada de HAL que
consultar, asi que vive como `model_validator` en `core/contracts/scan.py`
(`PpiCut`/`RhiCut`), no aqui.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from .common import MonotonicMicros
from .hal import SignalId


class AntennaAxis(StrEnum):
    AZIMUTH = "azimuth"
    ELEVATION = "elevation"


class AntennaMoveDirection(StrEnum):
    """Sentido de movimiento solicitado.

    `UP`/`DOWN` para elevacion (fin de carrera superior/inferior); en
    azimut (giro continuo, sin fin de carrera) cualquiera de los dos vale
    igual para el chequeo termico, que no distingue sentido.
    """

    UP = "up"
    DOWN = "down"


class AntennaLimitCheck(BaseModel):
    """Resultado de un chequeo de la guarda contra un movimiento propuesto.

    `allowed=False` es un rechazo de la guarda (baja responsabilidad,
    complementa el enclavamiento de hardware -- plan §4.3), no una lectura
    directa del HAL: la razon esta en `reason`, siempre en base a las
    senales de `hal.py` vigentes al momento `at_us`.
    """

    axis: AntennaAxis
    direction: AntennaMoveDirection
    allowed: bool
    signal_id: SignalId
    """Senal del HAL efectivamente consultada para esta decision -- para que
    un llamador (p.ej. `core/control_routines/antenna_movement.py`) pueda
    construir un `RoutineStepResult` trazable sin volver a decidir cual
    senal le corresponde a este eje/sentido."""
    reason: str
    at_us: MonotonicMicros
