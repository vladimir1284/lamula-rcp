"""RCP internal -- resultado de la guarda de seguridad de parametros (plan
§4.3/§4.4: "Parameter-Safety Guard").

Como `control.py`, no es un contrato RCP<->MMI; es interno a
`core/safety_guard/`. Solo modela hoy la parte de la guarda que tiene
senales reales que vigilar (limites de antena, ver
`core/safety_guard/antenna_limits.py`). La otra mitad del plan --
"prevention of pulse-width x PRF combinations that would damage the
klystron/magnetron" -- no tiene todavia ningun dato que consultar (ni senal
HAL, ni campo en `core/contracts/dsp.py`, ni contrato con el Scan
Worksheet/generador de forma de onda) y queda fuera de este modulo -- ver
PEND-RCP-08 en docs/alcance/pendientes.md.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from .common import MonotonicMicros


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
    reason: str
    at_us: MonotonicMicros
