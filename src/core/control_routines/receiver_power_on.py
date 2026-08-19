"""Rutina de control: "encendido del receptor analogico" (plan §4.3,
Rutina 3 de seis). Primer borrador, sin confirmar con el product expert
(PEND-RCP-07).

**Hallazgo -- el subsistema `rx` es el mas vacio de los seis en el
simulador:** a diferencia de `sys.turn_on_radar_conmand` (Rutina 1, sin
logica pero al menos con precondiciones reales que cambian) o `tx.fsm`
(Rutina 2, con maquina de estados y temporizador reales),
`radar_emulator/config/rd100s.seed.json` no tiene **ningun** bloque que
calcule ninguna senal `rx.*` -- ni las tres fuentes de alimentacion
(`rx.p_15_v_ps_ok_status`, `rx.n_15_v_ps_ok_status`,
`rx.p_12_v_ps_ok_status`), ni `rx.rfe_on_status`, ni
`rx.stalo_locked_status`, ni `rx.rfe_fault_status`. Todas quedan
permanentemente en su valor inicial (`false`) salvo que algo las fuerce por
el canal de control WS. Esto significa que, a diferencia de las otras
rutinas ya implementadas, **no hay ninguna forma de probar el camino de
exito de esta rutina contra el simulador sin forzar tambien las senales de
exito** (`rfe_on_status`/`stalo_locked_status`), no solo las precondiciones
-- ver `spike-fase2/RESULTADO-receiver-power-on.md`.

**Comando confirmado como pulso, no nivel:** `docs/interfaces/modbus.md`
de `radar_emulator` (seccion "Comandos por flanco") lista explicitamente
el par `Turn On RFE` / `Turn Off RFE` junto con Tx y Radar -- mismo patron
de pulso que las Rutinas 1 y 2, no un problema abierto como en la Rutina 4
(unidad de antena).

**`confirm_timeout_s` es obligatorio, sin default:** a diferencia del
caldeo del magnetron (Rutina 2), que al menos tiene un valor de marcador
de posicion puesto por el simulador, aqui no hay ninguna pista de cuanto
tarda el oscilador local (STALO) en engancharse -- ni siquiera un
marcador de posicion inventado por el equipo de `radar_emulator`. Ver
docstring de `antenna_positioning.py` para el mismo criterio.
"""

from __future__ import annotations

import asyncio
import time

from core.contracts.common import MonotonicMicros
from core.contracts.control import RoutineName, RoutineOutcome, RoutineResult, RoutineStepResult
from core.contracts.hal import HardwareAbstractionLayer

POWER_SUPPLY_SIGNALS = (
    "rx.p_15_v_ps_ok_status",
    "rx.n_15_v_ps_ok_status",
    "rx.p_12_v_ps_ok_status",
)
COMMAND_ON = "rx.turn_on_rfe_conmand"
RFE_ON_STATUS = "rx.rfe_on_status"
STALO_LOCKED_STATUS = "rx.stalo_locked_status"

# Mismo criterio que general_power_on.py / transmitter_power_on.py: mas
# largo que un tick (50 ms en la semilla) para no depender de perder el
# flanco.
PULSE_S = 0.1
POLL_INTERVAL_S = 0.15


def _now_us() -> MonotonicMicros:
    return time.monotonic_ns() // 1000


async def run_receiver_power_on(
    hal: HardwareAbstractionLayer,
    *,
    confirm_timeout_s: float,
) -> RoutineResult:
    """Enciende el receptor analogico (RFE) y espera a que el oscilador
    local quede enganchado. `confirm_timeout_s` es obligatorio -- ver
    docstring del modulo, no hay ningun valor real ni de marcador de
    posicion que usar como default.
    """

    steps: list[RoutineStepResult] = []

    all_ok = True
    for signal_id in POWER_SUPPLY_SIGNALS:
        reading = await hal.read_digital(signal_id)
        ok = reading.value is True
        steps.append(RoutineStepResult(signal_id=signal_id, ok=ok, detail=f"precondicion: value={reading.value}"))
        all_ok = all_ok and ok
    if not all_ok:
        return RoutineResult(routine=RoutineName.RECEIVER_POWER_ON, outcome=RoutineOutcome.FAILED, steps=steps, at_us=_now_us())

    await hal.write_digital(COMMAND_ON, True)
    await asyncio.sleep(PULSE_S)
    await hal.write_digital(COMMAND_ON, False)
    steps.append(RoutineStepResult(signal_id=COMMAND_ON, ok=True, detail="pulso enviado (flanco de subida)"))

    deadline = time.monotonic() + confirm_timeout_s
    while time.monotonic() < deadline:
        rfe_on = await hal.read_digital(RFE_ON_STATUS)
        stalo = await hal.read_digital(STALO_LOCKED_STATUS)
        if rfe_on.value is True and stalo.value is True:
            steps.append(RoutineStepResult(signal_id=RFE_ON_STATUS, ok=True, detail="RFE encendido y STALO enganchado"))
            return RoutineResult(routine=RoutineName.RECEIVER_POWER_ON, outcome=RoutineOutcome.SUCCESS, steps=steps, at_us=_now_us())
        await asyncio.sleep(POLL_INTERVAL_S)

    final_rfe = await hal.read_digital(RFE_ON_STATUS)
    final_stalo = await hal.read_digital(STALO_LOCKED_STATUS)
    steps.append(
        RoutineStepResult(
            signal_id=RFE_ON_STATUS,
            ok=False,
            detail=f"no se confirmo en {confirm_timeout_s}s: rfe_on={final_rfe.value} stalo_locked={final_stalo.value}",
        )
    )
    return RoutineResult(routine=RoutineName.RECEIVER_POWER_ON, outcome=RoutineOutcome.FAILED, steps=steps, at_us=_now_us())
