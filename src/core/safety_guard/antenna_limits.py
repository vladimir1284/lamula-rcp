"""Guarda de seguridad de parametros -- parte de limites de antena (plan
§4.3/§4.4: "Parameter-Safety Guard ... antenna limit checks").

Complementa el enclavamiento de hardware, no lo sustituye (plan: "low
safety responsibility"): esta guarda solo lee senales ya calculadas por el
adaptador HAL activo (real o `SimulatedHAL`) y decide si un movimiento
propuesto deberia rechazarse antes de pedirselo a la Rutina 5 (movimiento
de antena, todavia sin implementar -- PEND-RCP-07). No escribe nada al HAL
ni detiene un movimiento en curso por si misma.

Verificado contra `radar_emulator/config/rd100s.seed.json` (no solo contra
el catalogo vendorizado) al escribir esto:

- **Elevacion**: fin de carrera fisico por expresion (`el_position >= 91.5`
  / `<= -1.5`), sin proteccion termica de motor modelada -- la senal
  `ant.i2t_drive_el_status` existe en el catalogo pero ningun bloque la
  calcula (sin cablear, se queda en su valor inicial `false`). Por eso esta
  guarda no la consulta: leerla daria una falsa sensacion de cobertura.
- **Azimut**: sin fin de carrera (gira continuo), pero si proteccion
  termica real (bloque `i2t`, umbral 30 A durante 5 s equivalentes,
  `ant.i2t_drive_az_status`), que solo se rearma con un flanco de subida en
  `ant.turn_on_off_au_conmand` (encender la unidad de antena de nuevo) -- no
  hay comando de "reset" independiente para esta falla, a diferencia de
  `tx.reset_faults_command` en el transmisor.

Ambos limites (fin de carrera de elevacion, umbral termico de azimut) son
valores de marcador de posicion del simulador -- PEND-RCP-07. Esta guarda
no depende de sus valores numericos, solo de los booleanos ya calculados
del lado del HAL.
"""

from __future__ import annotations

import time

from core.contracts.common import MonotonicMicros
from core.contracts.hal import HardwareAbstractionLayer
from core.contracts.safety import AntennaAxis, AntennaLimitCheck, AntennaMoveDirection

EL_UPPER_LIMIT_SIGNAL = "ant.el_upper_limit_status"
EL_LOWER_LIMIT_SIGNAL = "ant.el_lower_limit_status"
AZ_THERMAL_TRIP_SIGNAL = "ant.i2t_drive_az_status"


def _now_us() -> MonotonicMicros:
    return time.monotonic_ns() // 1000


async def check_antenna_movement(
    hal: HardwareAbstractionLayer,
    axis: AntennaAxis,
    direction: AntennaMoveDirection,
) -> AntennaLimitCheck:
    """Decide si un movimiento propuesto (eje + sentido) deberia permitirse."""

    if axis is AntennaAxis.ELEVATION:
        limit_signal = EL_UPPER_LIMIT_SIGNAL if direction is AntennaMoveDirection.UP else EL_LOWER_LIMIT_SIGNAL
        reading = await hal.read_digital(limit_signal)
        if reading.value is True:
            return AntennaLimitCheck(
                axis=axis,
                direction=direction,
                allowed=False,
                reason=f"{limit_signal} activo: fin de carrera de elevacion alcanzado",
                at_us=_now_us(),
            )
        return AntennaLimitCheck(
            axis=axis,
            direction=direction,
            allowed=True,
            reason=f"{limit_signal} inactivo",
            at_us=_now_us(),
        )

    reading = await hal.read_digital(AZ_THERMAL_TRIP_SIGNAL)
    if reading.value is True:
        return AntennaLimitCheck(
            axis=axis,
            direction=direction,
            allowed=False,
            reason=(
                f"{AZ_THERMAL_TRIP_SIGNAL} activo: proteccion termica del motor de azimut "
                "enclavada, requiere apagar/encender la unidad de antena para rearmar"
            ),
            at_us=_now_us(),
        )
    return AntennaLimitCheck(
        axis=axis,
        direction=direction,
        allowed=True,
        reason=f"{AZ_THERMAL_TRIP_SIGNAL} inactivo",
        at_us=_now_us(),
    )
