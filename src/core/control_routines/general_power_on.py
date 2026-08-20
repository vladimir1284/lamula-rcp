"""Rutina de control: "general radar power-on" (plan §4.3, la mas simple de las seis).

Procedimiento confirmado por el product expert (`ControlRoutines.md`,
2026-08-20 -- absorbido en `radar_emulator/docs/alcance/pendientes.md`
PEND-27/PEND-28, ver tambien PEND-RCP-06 en docs/alcance/pendientes.md de este
repo y `docs/operacion/rutinas-control.md`):

1. Cuatro precondiciones antes de encender (`PRECONDITIONS`): standby, linea
   electrica, ambiente y **modo remoto** -- esta ultima confirmada por el
   experto, no estaba en el primer borrador.
2. Pulso `sys.turn_on_radar_conmand`, igual que antes.
3. Confirmacion post-pulso por lectura directa (`POST_PULSE_CHECKS`): ya no
   se infiere el exito de que las precondiciones "sigan bien" -- el experto
   confirmo dos senales reales para esto, `sys.system_on_ok_status` y
   `sys.mdb_fan_ok_status`.
4. Chequeo final de ventilacion (`CABINET_FAN_CHECKS`): Tx/Rx/AU Cabinet Fan
   Ok Status. `sys.cabinet_fans_ok` en `radar_emulator` es la version
   agregada (VIRT, interna al simulador, sin equivalente en hardware real
   segun el catalogo); esta rutina lee las cuatro senales reales por
   separado y hace el AND ella misma, mismo criterio que
   `transmitter_power_on.py` con `tx.interlock_ok_status` en vez de leer
   `tx.interlocks_ok`. Si el pulso y los dos chequeos de (3) salen bien pero
   falla algun Cabinet Fan, el radar SI quedo encendido -- se reporta
   `INTERRUPTED`, no `FAILED`, para no decir que el encendido no ocurrio.

PEND-27/PEND-28 (`radar_emulator`) siguen sin confirmar: el mapeo de canal
fisico de Rx/AU Cabinet Fan, y la reconciliacion de "Tx Cabinet Fan Ok
Status" del ICD compartido con los blowers ya existentes en la semilla.
"""

from __future__ import annotations

import asyncio
import time

from core.contracts.common import MonotonicMicros
from core.contracts.control import RoutineName, RoutineOutcome, RoutineResult, RoutineStepResult
from core.contracts.hal import HardwareAbstractionLayer

PRECONDITIONS = (
    "sys.standby_system_ok_status",
    "sys.line_parameters_ok_status",
    "sys.environment_ok_status",
    "sys.remote_mode_ok_status",
)
COMMAND_ON = "sys.turn_on_radar_conmand"

# Confirmacion directa de que el encendido tomo -- ya no se infiere de que
# las precondiciones "sigan bien" (ver PEND-RCP-06, resuelto en esta parte).
POST_PULSE_CHECKS = (
    "sys.system_on_ok_status",
    "sys.mdb_fan_ok_status",
)

# Paso final de la rutina (ControlRoutines.md, Rutina 1, punto 3.3): "Tx
# Cabinet Fan Ok Status" se lee de los blowers de Tx ya implementados
# (ADAM 4051), no de un canal propio -- ver PEND-28 en radar_emulator sobre
# por que ese ICD no coincide con la semilla en ADAM 4024/DI0.
CABINET_FAN_CHECKS = (
    "tx.cb_blower_ok_status",
    "tx.magnetron_blower_ok_status",
    "sys.rx_cabinet_fan_ok_status",
    "sys.au_cabinet_fan_ok_status",
)

# radar_emulator/docs/interfaces/modbus.md#comandos-por-flanco: "Turn On Radar"
# es flanco de subida, no nivel -- un pulso mas corto que el tick (50 ms en la
# semilla) puede perderse. 100 ms deja margen sin depender del tick exacto del
# adaptador activo (real o simulado).
PULSE_S = 0.1
# Margen tras el pulso antes de releer confirmacion -- mismo criterio que
# spike-fase1/hal_sim_spike.py para no asumir read-your-write inmediato (hal.py).
CONFIRM_MARGIN_S = 0.15


def _now_us() -> MonotonicMicros:
    return time.monotonic_ns() // 1000


async def run_general_power_on(hal: HardwareAbstractionLayer) -> RoutineResult:
    steps: list[RoutineStepResult] = []

    async def _check_all(signal_ids: tuple[str, ...], *, detail_prefix: str) -> bool:
        all_ok = True
        for signal_id in signal_ids:
            reading = await hal.read_digital(signal_id)
            ok = reading.value is True
            steps.append(
                RoutineStepResult(
                    signal_id=signal_id,
                    ok=ok,
                    detail=f"{detail_prefix}: value={reading.value} quality={reading.quality}",
                )
            )
            all_ok = all_ok and ok
        return all_ok

    if not await _check_all(PRECONDITIONS, detail_prefix="precondicion"):
        return RoutineResult(
            routine=RoutineName.GENERAL_POWER_ON,
            outcome=RoutineOutcome.FAILED,
            steps=steps,
            at_us=_now_us(),
        )

    await hal.write_digital(COMMAND_ON, True)
    await asyncio.sleep(PULSE_S)
    await hal.write_digital(COMMAND_ON, False)
    steps.append(
        RoutineStepResult(
            signal_id=COMMAND_ON,
            ok=True,
            detail="pulso enviado (flanco de subida, sin espera de confirmacion propia)",
        )
    )

    await asyncio.sleep(CONFIRM_MARGIN_S)
    if not await _check_all(POST_PULSE_CHECKS, detail_prefix="post-pulso"):
        return RoutineResult(
            routine=RoutineName.GENERAL_POWER_ON,
            outcome=RoutineOutcome.FAILED,
            steps=steps,
            at_us=_now_us(),
        )

    if not await _check_all(CABINET_FAN_CHECKS, detail_prefix="cabinet-fan"):
        return RoutineResult(
            routine=RoutineName.GENERAL_POWER_ON,
            outcome=RoutineOutcome.INTERRUPTED,
            steps=steps,
            at_us=_now_us(),
        )

    return RoutineResult(
        routine=RoutineName.GENERAL_POWER_ON,
        outcome=RoutineOutcome.SUCCESS,
        steps=steps,
        at_us=_now_us(),
    )
