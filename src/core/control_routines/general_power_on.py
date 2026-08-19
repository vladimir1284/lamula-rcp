"""Rutina de control: "general radar power-on" (plan §4.3, la mas simple de las seis).

A diferencia del transmisor -- que en `radar_emulator` tiene una maquina de
estados completa (`tx.fsm`: OFF/STARTING/WARMUP/READY/HV_ON/RADIATING/FAULT,
ver `radar_emulator/docs/configuracion/bloques.md`) -- `sys.turn_on_radar_conmand`
no tiene ningun bloque de logica del lado del emulador: es un DO plano sin
efecto simulado propio. Por eso se eligio esta como primera rutina de Fase 2:
sienta el patron de `core/control_routines/` sin arrastrar sincronizacion
contra un FSM del otro lado.

**PEND-RCP-06** (ver docs/alcance/pendientes.md): las tres precondiciones de
abajo y su orden son una inferencia de este repo a partir de los nombres del
catalogo vendorizado (`sys.line_parameters_ok_status`, `sys.environment_ok_status`,
`sys.standby_system_ok_status`), no una secuencia fijada por un manual de
fabricante ni confirmada por el product expert -- a diferencia del ICD
RCP<->ORPG, esta secuencia si es responsabilidad de este repo (plan: "reglas
de limite propiedad del product expert"), pero sigue sin confirmar. Ademas no
existe en el catalogo una senal de confirmacion tipo "radar_on_status": el
exito de la rutina se infiere de que las tres precondiciones sigan en OK
despues del pulso, no de una lectura directa de "encendido". Confirmar ambas
cosas con el equipo antes de considerar esta rutina algo mas que un primer
borrador.
"""

from __future__ import annotations

import asyncio
import time

from core.contracts.common import MonotonicMicros
from core.contracts.control import RoutineName, RoutineOutcome, RoutineResult, RoutineStepResult
from core.contracts.hal import HardwareAbstractionLayer

PRECONDITIONS = (
    "sys.line_parameters_ok_status",
    "sys.environment_ok_status",
    "sys.standby_system_ok_status",
)
COMMAND_ON = "sys.turn_on_radar_conmand"

# radar_emulator/docs/interfaces/modbus.md#comandos-por-flanco: "Turn On Radar"
# es flanco de subida, no nivel -- un pulso mas corto que el tick (50 ms en la
# semilla) puede perderse. 100 ms deja margen sin depender del tick exacto del
# adaptador activo (real o simulado).
PULSE_S = 0.1
# Margen tras el pulso antes de releer precondiciones -- mismo criterio que
# spike-fase1/hal_sim_spike.py para no asumir read-your-write inmediato (hal.py).
CONFIRM_MARGIN_S = 0.15


def _now_us() -> MonotonicMicros:
    return time.monotonic_ns() // 1000


async def run_general_power_on(hal: HardwareAbstractionLayer) -> RoutineResult:
    steps: list[RoutineStepResult] = []

    async def _check_preconditions(*, detail_prefix: str) -> bool:
        all_ok = True
        for signal_id in PRECONDITIONS:
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

    if not await _check_preconditions(detail_prefix="precondicion"):
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
    if not await _check_preconditions(detail_prefix="post-pulso"):
        return RoutineResult(
            routine=RoutineName.GENERAL_POWER_ON,
            outcome=RoutineOutcome.FAILED,
            steps=steps,
            at_us=_now_us(),
        )

    return RoutineResult(
        routine=RoutineName.GENERAL_POWER_ON,
        outcome=RoutineOutcome.SUCCESS,
        steps=steps,
        at_us=_now_us(),
    )
