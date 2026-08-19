"""Rutina de control: "encendido de la unidad de antena" (plan §4.3,
Rutina 4 de seis). Primer borrador, sin confirmar con el product expert
(PEND-RCP-07).

**Igual que el receptor (Rutina 3), el subsistema de unidad de antena no
tiene ningun bloque de logica en `radar_emulator/config/rd100s.seed.json`:**
ni `ant.au_on_status`, ni `ant.drive_az_ok_status`, ni
`ant.drive_el_ok_status` los calcula nada -- quedan en su valor inicial
`false` salvo que algo los fuerce por el canal WS de control. Por eso el
camino de exito de esta rutina, igual que el del receptor, solo se puede
probar contra el simulador forzando tambien esas senales, no solo la
precondicion -- ver `spike-fase2/RESULTADO-antenna-unit-power-on.md`.

**Pulso o nivel -- ambiguedad real, no resuelta aqui:**
`docs/operacion/rutinas-control.md` (Rutina 4) ya señala que el catalogo
tiene una sola orden para esta rutina (`ant.turn_on_off_au_conmand`), no un
par Encender/Apagar como Tx, RFE o el encendido general. La lista de
"Comandos por flanco" de `radar_emulator/docs/interfaces/modbus.md` nombra
explicitamente esos tres pares como pulso -- `turn_on_off_au_conmand` **no**
esta en esa lista. Mismo criterio ya usado para
`ant.enable_drive_az/el_conmand` en `antenna_movement.py`: un comando unico
sin contraparte de apagado, no listado como flanco, se trata como **nivel**
-- se escribe `True` y se deja asi (esta rutina no implementa apagado). Sin
confirmar con el product expert; si el radar real lo maneja como pulso,
esta implementacion queda mal.
"""

from __future__ import annotations

import asyncio
import time

from core.contracts.common import MonotonicMicros
from core.contracts.control import RoutineName, RoutineOutcome, RoutineResult, RoutineStepResult
from core.contracts.hal import HardwareAbstractionLayer

RADOME_CLOSED_STATUS = "ant.radome_closed_status"
COMMAND_ON = "ant.turn_on_off_au_conmand"
AU_ON_STATUS = "ant.au_on_status"
DRIVE_OK_SIGNALS = ("ant.drive_az_ok_status", "ant.drive_el_ok_status")

POLL_INTERVAL_S = 0.15


def _now_us() -> MonotonicMicros:
    return time.monotonic_ns() // 1000


async def run_antenna_unit_power_on(
    hal: HardwareAbstractionLayer,
    *,
    confirm_timeout_s: float,
) -> RoutineResult:
    """Enciende la unidad de antena (`ant.turn_on_off_au_conmand` como
    nivel, no pulso -- ver docstring del modulo) y espera a que quede
    encendida con ambos variadores en buen estado. `confirm_timeout_s` es
    obligatorio: no hay ningun valor real ni de marcador de posicion que
    usar como default.
    """

    steps: list[RoutineStepResult] = []

    radome = await hal.read_digital(RADOME_CLOSED_STATUS)
    steps.append(RoutineStepResult(signal_id=RADOME_CLOSED_STATUS, ok=radome.value is True, detail=f"precondicion: value={radome.value}"))
    if radome.value is not True:
        return RoutineResult(routine=RoutineName.ANTENNA_UNIT_POWER_ON, outcome=RoutineOutcome.FAILED, steps=steps, at_us=_now_us())

    await hal.write_digital(COMMAND_ON, True)
    steps.append(RoutineStepResult(signal_id=COMMAND_ON, ok=True, detail="comando puesto a nivel alto (no es un pulso)"))

    deadline = time.monotonic() + confirm_timeout_s
    while time.monotonic() < deadline:
        au_on = await hal.read_digital(AU_ON_STATUS)
        drive_readings = [await hal.read_digital(s) for s in DRIVE_OK_SIGNALS]
        if au_on.value is True and all(r.value is True for r in drive_readings):
            steps.append(RoutineStepResult(signal_id=AU_ON_STATUS, ok=True, detail="unidad de antena encendida, variadores OK"))
            return RoutineResult(routine=RoutineName.ANTENNA_UNIT_POWER_ON, outcome=RoutineOutcome.SUCCESS, steps=steps, at_us=_now_us())
        await asyncio.sleep(POLL_INTERVAL_S)

    au_on = await hal.read_digital(AU_ON_STATUS)
    drive_readings = [await hal.read_digital(s) for s in DRIVE_OK_SIGNALS]
    steps.append(
        RoutineStepResult(
            signal_id=AU_ON_STATUS,
            ok=False,
            detail=f"no se confirmo en {confirm_timeout_s}s: au_on={au_on.value} drives={[r.value for r in drive_readings]}",
        )
    )
    return RoutineResult(routine=RoutineName.ANTENNA_UNIT_POWER_ON, outcome=RoutineOutcome.FAILED, steps=steps, at_us=_now_us())
