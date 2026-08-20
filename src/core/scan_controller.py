"""RCP core -- Scan Controller, alcance acotado (decision de sesion 2026-08-20).

El plan (project-plan.md, tabla de componentes) describe "Scan Controller &
Scheduler | Sequences interactive and automated volume scans; drives the
control routines". Esta primera version cubre solo la mitad de "secuenciar":
dado un corte del Scan Worksheet manual (`core/contracts/scan.py`,
`PpiCut`/`RhiCut`), posiciona el eje fijo y barre el eje movil, apoyandose en
las Rutinas 5 y 6 ya construidas (`core/control_routines/`).

**Lo que este modulo deliberadamente NO hace, alcance de esta sesion:**

- **No sube alta tension ni empieza a radiar.** `core/control_routines/
  transmitter_power_on.py` se detiene a proposito en `tx.ready_status`
  (ver su docstring): "subir HV/radiar" quedo identificado ahi como trabajo
  que tiene mas sentido al arrancar un escaneo, no como parte del encendido.
  Sigue sin construirse -- es seguridad critica (alta tension) y no hay
  decision explicita de como secuenciarlo (¿antes de posicionar? ¿despues de
  llegar al inicio del barrido? ¿que enclavamientos revisar de nuevo?). No
  se inventa esa secuencia aqui.
- **No aplica `prf_hz`/`pulse_width_us` a ningun adaptador de forma de
  onda.** No existe ninguno -- ver PEND-RCP-08 (`docs/alcance/
  pendientes.md`), bloqueado por falta de contrato con un generador de
  forma de onda/DRX y de la tabla de limites de ciclo de trabajo del
  klystron/magnetron (propiedad del product expert). Los dos campos viajan
  en `cut` sin usarse -- documentado, no un olvido.

Este controlador es puramente "hacia donde apunta la antena y durante
cuanto tiempo", no "que transmite ni que recibe".

**Deteccion de fin de barrido -- diseno propio de este repo, sin nada que
imitar del simulador ni del plan** (mismo criterio que ya justifico los
parametros obligatorios de la Rutina 6): se acumula el delta angular con
signo entre lecturas sucesivas de posicion (formula ya usada en
`antenna_positioning.py` para la distancia angular corta de azimut,
generalizada aqui para ambos ejes -- funciona igual para elevacion porque
los deltas por vuelta de sondeo son pequenos, nunca cerca de la frontera
0/360 donde el `wrap` de azimut importa). El barrido termina cuando lo
acumulado alcanza el ancho total pedido (`azimuth_end_deg -
azimuth_start_deg`, o el equivalente de elevacion), dentro de
`sweep_tolerance_deg`. Sin confirmar con el product expert -- ver
PEND-RCP-10.

**`sweep_voltage_magnitude` es obligatorio, sin default** -- mismo criterio
que `antenna_positioning.py`: no existe ganancia real volt->grados/s
confirmada (extension de PEND-RCP-07) ni una relacion PRF/pulse-width/ancho
de haz -> velocidad de rotacion confirmada (PEND-RCP-09), asi que quien
llama a `run_scan_cut` es quien tiene que traerla, no esta funcion.
"""

from __future__ import annotations

import asyncio
import time

from core.contracts.common import MonotonicMicros
from core.contracts.control import RoutineOutcome, RoutineStepResult
from core.contracts.hal import HardwareAbstractionLayer
from core.contracts.safety import AntennaAxis, AntennaMoveDirection
from core.contracts.scan import AxisPositioningParams, PpiCut, RhiCut, ScanCutResult
from core.control_routines.antenna_movement import run_antenna_movement
from core.control_routines.antenna_positioning import run_antenna_positioning
from core.safety_guard import check_antenna_movement

DEFAULT_POLL_INTERVAL_S = 0.15


def _now_us() -> MonotonicMicros:
    return time.monotonic_ns() // 1000


def _signed_delta_deg(current_deg: float, previous_deg: float) -> float:
    """Distancia angular con signo mas corta entre dos lecturas sucesivas.

    Misma formula que `antenna_positioning._azimuth_error_deg`, generalizada
    a ambos ejes -- ver docstring del modulo: para elevacion el resultado es
    identico a la resta simple porque el delta por vuelta de sondeo nunca se
    acerca a la frontera 0/360 donde el modulo importaria."""
    return ((current_deg - previous_deg + 180.0) % 360.0) - 180.0


def _current_deg(position, axis: AntennaAxis) -> float:
    return position.az_deg if axis is AntennaAxis.AZIMUTH else position.el_deg


async def run_scan_cut(
    hal: HardwareAbstractionLayer,
    cut: PpiCut | RhiCut,
    *,
    azimuth_positioning: AxisPositioningParams,
    elevation_positioning: AxisPositioningParams,
    sweep_voltage_magnitude: float,
    sweep_tolerance_deg: float,
    sweep_timeout_s: float,
    poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
) -> ScanCutResult:
    """Posiciona el eje fijo de `cut` y barre el eje movil de punta a punta.

    `PpiCut`: eje fijo = elevacion (`cut.elevation_deg`), eje de barrido =
    azimut (`cut.azimuth_start_deg` -> `cut.azimuth_end_deg`).
    `RhiCut`: eje fijo = azimut (`cut.azimuth_deg`), eje de barrido =
    elevacion (`cut.elevation_start_deg` -> `cut.elevation_end_deg`).

    Ver docstring del modulo para lo que esta funcion NO hace (HV/radiar,
    PRF/pulse-width) y para el criterio de deteccion de fin de barrido.
    """

    if sweep_voltage_magnitude <= 0:
        raise ValueError("sweep_voltage_magnitude debe ser > 0 -- es una magnitud, el sentido lo decide el corte")

    steps: list[RoutineStepResult] = []

    if isinstance(cut, PpiCut):
        fixed_axis, fixed_target = AntennaAxis.ELEVATION, cut.elevation_deg
        fixed_params = elevation_positioning
        swept_axis, start_deg, end_deg = AntennaAxis.AZIMUTH, cut.azimuth_start_deg, cut.azimuth_end_deg
        swept_params = azimuth_positioning
    else:
        fixed_axis, fixed_target = AntennaAxis.AZIMUTH, cut.azimuth_deg
        fixed_params = azimuth_positioning
        swept_axis, start_deg, end_deg = AntennaAxis.ELEVATION, cut.elevation_start_deg, cut.elevation_end_deg
        swept_params = elevation_positioning

    # --- paso 1: posicionar el eje fijo -----------------------------------
    fixed_result = await run_antenna_positioning(
        hal, fixed_axis, fixed_target,
        gain_v_per_deg=fixed_params.gain_v_per_deg,
        max_voltage=fixed_params.max_voltage,
        tolerance_deg=fixed_params.tolerance_deg,
        timeout_s=fixed_params.timeout_s,
    )
    steps.extend(fixed_result.steps)
    if fixed_result.outcome != RoutineOutcome.SUCCESS:
        return ScanCutResult(outcome=fixed_result.outcome, steps=steps, at_us=_now_us())

    # --- paso 2: posicionar el eje de barrido al inicio -------------------
    start_result = await run_antenna_positioning(
        hal, swept_axis, start_deg,
        gain_v_per_deg=swept_params.gain_v_per_deg,
        max_voltage=swept_params.max_voltage,
        tolerance_deg=swept_params.tolerance_deg,
        timeout_s=swept_params.timeout_s,
    )
    steps.extend(start_result.steps)
    if start_result.outcome != RoutineOutcome.SUCCESS:
        return ScanCutResult(outcome=start_result.outcome, steps=steps, at_us=_now_us())

    # --- paso 3: arrancar el barrido continuo (Rutina 5) -------------------
    total_sweep_deg = end_deg - start_deg
    direction = 1.0 if total_sweep_deg > 0 else -1.0
    voltage = direction * sweep_voltage_magnitude

    start_move = await run_antenna_movement(hal, swept_axis, voltage)
    steps.extend(start_move.steps)
    if start_move.outcome != RoutineOutcome.SUCCESS:
        return ScanCutResult(outcome=start_move.outcome, steps=steps, at_us=_now_us())

    position = await hal.read_antenna_position()
    previous_deg = _current_deg(position, swept_axis)
    steps.append(
        RoutineStepResult(
            signal_id="ant.az_position" if swept_axis is AntennaAxis.AZIMUTH else "ant.el_position",
            ok=True,
            detail=f"barrido iniciado en {previous_deg:.3f} deg, objetivo total={total_sweep_deg:.3f} deg",
        )
    )

    # --- paso 4: sondear hasta completar el barrido, con guarda propia ----
    traveled_deg = 0.0
    deadline = time.monotonic() + sweep_timeout_s
    position_signal = "ant.az_position" if swept_axis is AntennaAxis.AZIMUTH else "ant.el_position"
    # AntennaMoveDirection solo distingue fin-de-carrera de elevacion; en
    # azimut (giro continuo) el chequeo termico no distingue sentido -- ver
    # docstring de `AntennaMoveDirection` (core/contracts/safety.py).
    direction_for_guard = AntennaMoveDirection.UP if voltage > 0 else AntennaMoveDirection.DOWN

    while time.monotonic() < deadline:
        await asyncio.sleep(poll_interval_s)

        guard = await check_antenna_movement(hal, swept_axis, direction_for_guard)
        if not guard.allowed:
            stop_result = await run_antenna_movement(hal, swept_axis, 0.0)
            steps.extend(stop_result.steps)
            steps.append(
                RoutineStepResult(
                    signal_id=guard.signal_id,
                    ok=False,
                    detail=f"guarda rechazo continuar el barrido a mitad de camino: {guard.reason}",
                )
            )
            return ScanCutResult(outcome=RoutineOutcome.INTERRUPTED, steps=steps, at_us=_now_us())

        position = await hal.read_antenna_position()
        current_deg = _current_deg(position, swept_axis)
        traveled_deg += _signed_delta_deg(current_deg, previous_deg)
        previous_deg = current_deg

        if abs(traveled_deg) >= abs(total_sweep_deg) - sweep_tolerance_deg:
            stop_result = await run_antenna_movement(hal, swept_axis, 0.0)
            steps.extend(stop_result.steps)
            steps.append(
                RoutineStepResult(
                    signal_id=position_signal,
                    ok=stop_result.outcome == RoutineOutcome.SUCCESS,
                    detail=f"barrido completo: recorrido={traveled_deg:.3f} deg de {total_sweep_deg:.3f} deg pedidos",
                )
            )
            outcome = RoutineOutcome.SUCCESS if stop_result.outcome == RoutineOutcome.SUCCESS else RoutineOutcome.FAILED
            return ScanCutResult(outcome=outcome, steps=steps, at_us=_now_us())

    await run_antenna_movement(hal, swept_axis, 0.0)
    steps.append(
        RoutineStepResult(
            signal_id=position_signal,
            ok=False,
            detail=f"no se completo el barrido en {sweep_timeout_s}s: recorrido={traveled_deg:.3f} deg de {total_sweep_deg:.3f} deg pedidos",
        )
    )
    return ScanCutResult(outcome=RoutineOutcome.FAILED, steps=steps, at_us=_now_us())
