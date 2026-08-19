"""Guarda de seguridad de parametros -- parte de limites de antena (plan
§4.3/§4.4: "Parameter-Safety Guard ... antenna limit checks").

Complementa el enclavamiento de hardware, no lo sustituye (plan: "low
safety responsibility"): esta guarda solo lee senales ya calculadas por el
adaptador HAL activo (real o `SimulatedHAL`) y decide si un movimiento
propuesto deberia rechazarse antes de pedirselo a la Rutina 5 (movimiento
de antena, `core/control_routines/antenna_movement.py`), que es quien la
invoca tanto antes de empezar a mover como durante el movimiento. Esta
guarda en si misma no escribe nada al HAL ni detiene un movimiento en
curso -- es la rutina, no la guarda, quien actua sobre el resultado.

Verificado contra `radar_emulator/config/rd100s.seed.json` (no solo contra
el catalogo vendorizado) al escribir esto:

- **Elevacion**: dos capas separadas en el simulador. El bloque `axis` que
  integra la posicion tiene su propio `limits_deg: [-2.0, 92.0]` como tope
  fisico duro (la posicion nunca cruza ese rango, sea lo que sea que pida
  la referencia de velocidad); por separado, dos bloques de expresion
  calculan `ant.el_upper_limit_status`/`el_lower_limit_status` (interruptor
  de fin de carrera que dispara un poco antes, en 91.5°/-1.5°) y el propio
  bloque `axis` los lee como `inhibit_up`/`inhibit_down` para frenar el
  movimiento en esa direccion. Esta guarda consulta esas dos senales de
  interruptor (lo que el HAL expone), no el limite dentro del bloque `axis`
  (interno al simulador, sin equivalente en el HAL real). Sin proteccion
  termica de motor modelada para este eje -- la senal
  `ant.i2t_drive_el_status` existe en el catalogo pero ningun bloque la
  calcula (sin cablear, se queda en su valor inicial `false`). Por eso esta
  guarda no la consulta: leerla daria una falsa sensacion de cobertura.
- **Azimut**: sin fin de carrera (gira continuo), pero si proteccion
  termica real (bloque `i2t`, umbral 30 A durante 5 s equivalentes,
  `ant.i2t_drive_az_status`), que solo se rearma con un flanco de subida en
  `ant.turn_on_off_au_conmand` (encender la unidad de antena de nuevo) -- no
  hay comando de "reset" independiente para esta falla, a diferencia de
  `tx.reset_faults_command` en el transmisor. A diferencia del bloque
  `axis` de elevacion, el de azimut **no** lee `ant.i2t_drive_az_status`
  como su propio inhibit -- el simulador calcula la falla pero no corta el
  drive el mismo. Quien tiene que reaccionar y bajar
  `ant.enable_drive_az_conmand` al verla activa es el RCP (exactamente el
  rol de esta guarda) -- ver `core/control_routines/antenna_movement.py`.

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
                signal_id=limit_signal,
                reason=f"{limit_signal} activo: fin de carrera de elevacion alcanzado",
                at_us=_now_us(),
            )
        return AntennaLimitCheck(
            axis=axis,
            direction=direction,
            allowed=True,
            signal_id=limit_signal,
            reason=f"{limit_signal} inactivo",
            at_us=_now_us(),
        )

    reading = await hal.read_digital(AZ_THERMAL_TRIP_SIGNAL)
    if reading.value is True:
        return AntennaLimitCheck(
            axis=axis,
            direction=direction,
            allowed=False,
            signal_id=AZ_THERMAL_TRIP_SIGNAL,
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
        signal_id=AZ_THERMAL_TRIP_SIGNAL,
        reason=f"{AZ_THERMAL_TRIP_SIGNAL} inactivo",
        at_us=_now_us(),
    )
