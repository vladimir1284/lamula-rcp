"""Rutina de control: "posicionamiento de antena" (plan §4.3, Rutina 6 de
seis, la ultima).

Primer borrador con una diferencia deliberada frente a `general_power_on.py`
y `antenna_movement.py`: **esta rutina no fija ningun valor propio**. Las
otras dos rutinas ya implementadas usan constantes marcadas como
provisionales (`PULSE_S`, `MOVING_EPS_DEG_S`, ...) pero al menos apoyadas en
algo real -- un tick conocido, un rango de senal, una ganancia que existe
aunque no este confirmada. Aqui no hay nada de eso: `radar_emulator` no
modela ningun lazo de posicionamiento (docs/operacion/rutinas-control.md,
"Rutina 6" -- "diseño enteramente nuevo, sin nada que imitar"), asi que una
ganancia de control, una tolerancia final o un timeout inventados aqui
serian un numero mas sin ningun respaldo -- ni siquiera el respaldo debil de
"esto es lo que puso el equipo de radar_emulator como marcador de
posicion". Por eso `gain_v_per_deg`, `max_voltage`, `tolerance_deg` y
`timeout_s` son parametros obligatorios sin default: quien llame a esta
rutina (el Scan Worksheet o el scheduler, ninguno construido todavia) es
quien tiene que traerlos, no esta funcion. Ver PEND-RCP-07.

Se apoya en la Rutina 5 (`run_antenna_movement`) para cada paso de control,
tal como describe el diseño de rutinas-control.md: mide posicion, calcula
error, pide una velocidad (aqui, un voltaje) proporcional al error, y para
dentro de la tolerancia. `run_antenna_movement` ya reenvia el rechazo de la
guarda de seguridad de parametros (limite de antena / termica de azimut)
como `INTERRUPTED`, y esta rutina lo propaga tal cual -- no lo intenta
resolver ni reintenta con otro voltaje.

**Limitacion conocida, no resuelta:** al ser un control proporcional simple
(sin frenado anticipado por distancia de parada), un movimiento con mucho
error inicial puede sobrepasar el objetivo antes de que el eje frene, ya
que la desaceleracion del bloque `axis` del simulador esta limitada
(`accel_deg_s2`) y aqui no se calcula ninguna distancia de frenado contra
ese limite. Es exactamente la pregunta que rutinas-control.md deja abierta
para el experto ("¿el acercamiento final debe frenar de forma gradual...?")
-- no se resuelve aqui inventando una formula de frenado sin un valor real
de aceleracion.
"""

from __future__ import annotations

import time

from core.contracts.common import MonotonicMicros
from core.contracts.control import RoutineName, RoutineOutcome, RoutineResult, RoutineStepResult
from core.contracts.hal import HardwareAbstractionLayer
from core.contracts.safety import AntennaAxis
from core.control_routines.antenna_movement import run_antenna_movement

POSITION_SIGNAL = {
    AntennaAxis.AZIMUTH: "ant.az_position",
    AntennaAxis.ELEVATION: "ant.el_position",
}

DEFAULT_POLL_INTERVAL_S = 0.15


def _now_us() -> MonotonicMicros:
    return time.monotonic_ns() // 1000


def _current_deg_and_valid(position, axis: AntennaAxis) -> tuple[float, bool]:
    if axis is AntennaAxis.AZIMUTH:
        return position.az_deg, position.az_valid
    return position.el_deg, position.el_valid


def _azimuth_error_deg(target_deg: float, current_deg: float) -> float:
    """Distancia angular con signo mas corta (azimut gira continuo,
    `wrap: true` en el bloque `axis` del simulador -- ver
    `core/safety_guard/antenna_limits.py`)."""
    return ((target_deg - current_deg + 180.0) % 360.0) - 180.0


async def run_antenna_positioning(
    hal: HardwareAbstractionLayer,
    axis: AntennaAxis,
    target_deg: float,
    *,
    gain_v_per_deg: float,
    max_voltage: float,
    tolerance_deg: float,
    timeout_s: float,
    poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
) -> RoutineResult:
    """Posiciona `axis` en `target_deg` pidiendo, en cada paso, un voltaje
    proporcional al error via la Rutina 5 (`run_antenna_movement`). Todos
    los parametros con nombre son obligatorios a proposito -- ver docstring
    del modulo.
    """

    steps: list[RoutineStepResult] = []
    position_signal = POSITION_SIGNAL[axis]
    deadline = time.monotonic() + timeout_s

    while time.monotonic() < deadline:
        position = await hal.read_antenna_position()
        current_deg, valid = _current_deg_and_valid(position, axis)

        if not valid:
            steps.append(
                RoutineStepResult(
                    signal_id=position_signal,
                    ok=False,
                    detail="lectura de posicion invalida (encoder degradado), no se puede posicionar",
                )
            )
            return RoutineResult(routine=RoutineName.ANTENNA_POSITIONING, outcome=RoutineOutcome.FAILED, steps=steps, at_us=_now_us())

        error_deg = _azimuth_error_deg(target_deg, current_deg) if axis is AntennaAxis.AZIMUTH else target_deg - current_deg

        if abs(error_deg) <= tolerance_deg:
            stop_result = await run_antenna_movement(hal, axis, 0.0)
            steps.extend(stop_result.steps)
            steps.append(
                RoutineStepResult(
                    signal_id=position_signal,
                    ok=stop_result.outcome == RoutineOutcome.SUCCESS,
                    detail=f"dentro de tolerancia (error={error_deg:.3f} deg), eje detenido",
                )
            )
            outcome = RoutineOutcome.SUCCESS if stop_result.outcome == RoutineOutcome.SUCCESS else RoutineOutcome.FAILED
            return RoutineResult(routine=RoutineName.ANTENNA_POSITIONING, outcome=outcome, steps=steps, at_us=_now_us())

        voltage = max(-max_voltage, min(max_voltage, gain_v_per_deg * error_deg))
        move_result = await run_antenna_movement(hal, axis, voltage)
        steps.extend(move_result.steps)
        steps.append(
            RoutineStepResult(
                signal_id=position_signal,
                ok=move_result.outcome == RoutineOutcome.SUCCESS,
                detail=f"error={error_deg:.3f} deg -> voltaje comandado={voltage:.3f} V (outcome={move_result.outcome})",
            )
        )

        if move_result.outcome != RoutineOutcome.SUCCESS:
            # La Rutina 5 ya fallo o fue interrumpida (guarda de seguridad de
            # parametros, o el eje nunca arranco) -- no tiene sentido seguir
            # pidiendo voltajes nuevos, se propaga tal cual.
            return RoutineResult(routine=RoutineName.ANTENNA_POSITIONING, outcome=move_result.outcome, steps=steps, at_us=_now_us())

    steps.append(
        RoutineStepResult(signal_id=position_signal, ok=False, detail=f"no se alcanzo la tolerancia en {timeout_s}s")
    )
    await run_antenna_movement(hal, axis, 0.0)
    return RoutineResult(routine=RoutineName.ANTENNA_POSITIONING, outcome=RoutineOutcome.FAILED, steps=steps, at_us=_now_us())
