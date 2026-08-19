"""Rutina de control: "encendido del transmisor" (plan §4.3, Rutina 2 de
seis). Primer borrador, mismo estado que las demas -- probado contra el
simulador, sin confirmar con el product expert (PEND-RCP-07 extendido mas
abajo).

A diferencia de las otras cinco rutinas, esta es la unica donde el
simulador reproduce una secuencia interna con temporizadores propios
(`tx.fsm`, `radar_emulator/config/rd100s.seed.json`, tipo `state_machine`:
OFF -> STARTING -> WARMUP -> READY -> HV_ON -> RADIATING, mas FAULT).
Verificado contra esa maquina, no contra `docs/operacion/rutinas-control.md`
(que describe el diseño propuesto en lenguaje operativo, con algunas
imprecisiones frente a lo que el `tx.fsm` real hace):

**Alcance elegido para esta rutina -- OFF a READY, no mas alla:** el plan
nombra seis rutinas, ninguna llamada "subir HV" o "empezar a radiar"; ese
paso tiene mas sentido como parte de arrancar un escaneo (Scan
Controller/Scheduler, sin construir todavia) que como parte de un
"encendido" que se hace una vez. Subir alta tension y habilitar salida
apenas se enciende el transmisor, sin un escaneo esperando, irradiaria sin
proposito. Es exactamente la pregunta que rutinas-control.md deja abierta
("¿debe llegar hasta 'listo' nada mas, o tambien subir HV y radiar?") --
esta implementacion elige la interpretacion mas conservadora y lo deja
explicito aqui en vez de asumirlo en silencio. `run_transmitter_hv_on`
(subir HV + habilitar salida) queda sin implementar.

**Hallazgo -- las precondiciones no son las que exige el simulador para
esta transicion:** la transicion `OFF -> STARTING` del `tx.fsm` real
**no** exige ningun interlock (`rising(tx.turn_on_tx_command) and not
tx.turn_off_tx_command`, nada mas) -- los seis interlocks de mas abajo
solo los exige la transicion `READY -> HV_ON`, fuera del alcance de esta
rutina. Esta rutina los chequea igual, **como precondicion propia del RCP,
mas estricta que el simulador**, siguiendo el mismo criterio que
`general_power_on.py` (PEND-RCP-06): no tiene sentido empezar a calentar el
magnetron sin sopladores/presion/fase correctos, aunque el simulador no lo
exija para esta transicion. Sin confirmar con el product expert.

**Los seis interlocks reales (no siete como sugiere rutinas-control.md):**
el simulador los agrega en un solo signal interno `tx.interlocks_ok`, que
**no esta expuesto por Modbus** (`kind: VIRT`, sin mapeo) -- el RCP tiene
que leer y combinar el mismo, no puede leer un "interlocks_ok" del HAL.
`tx.interlock_ok_status` (uno de los seis) ya es, el mismo,
`ant.radome_closed_status and sys.standby_system_ok_status` -- por eso son
seis señales, no siete: "radomo cerrado" y "sistema en espera" de
rutinas-control.md son el mismo señal agregado, no dos independientes.

**Comandos que el simulador no usa pero podrian existir en hardware real:**
`tx.turn_on_blowers_command`, `tx.turn_on_fps_command`,
`tx.turn_on_mps_command` estan en el catalogo pero ningun bloque de
`radar_emulator` los lee -- el `tx.fsm` enciende soplador/FPS/MPS como
efecto automatico de entrar a `STARTING`, sin que el RCP los comande por
separado. Puede ser una simplificacion del simulador o el orden real en
hardware -- sin confirmar, esta rutina no los escribe.
"""

from __future__ import annotations

import asyncio
import time

from core.contracts.common import MonotonicMicros
from core.contracts.control import RoutineName, RoutineOutcome, RoutineResult, RoutineStepResult
from core.contracts.hal import HardwareAbstractionLayer

INTERLOCK_SIGNALS = (
    "tx.interlock_ok_status",
    "tx.wg_pressure_ok_status",
    "tx.cb_blower_ok_status",
    "tx.magnetron_blower_ok_status",
    "tx.pha_seq_ok_status",
    "tx.duty_cycle_ok_status",
)
COMMAND_ON = "tx.turn_on_tx_command"
TX_ON_STATUS = "tx.tx_on_status"
READY_STATUS = "tx.ready_status"

# Mismo criterio que general_power_on.py: mas largo que un tick (50 ms en la
# semilla) para no depender de perder el flanco.
PULSE_S = 0.1
# Margen para confirmar que se entro a STARTING -- la transicion es
# inmediata (sin after_ms), un par de ticks de margen alcanza.
STARTING_CONFIRM_TIMEOUT_S = 1.0
POLL_INTERVAL_S = 0.15


def _now_us() -> MonotonicMicros:
    return time.monotonic_ns() // 1000


async def run_transmitter_power_on(
    hal: HardwareAbstractionLayer,
    *,
    warmup_timeout_s: float,
) -> RoutineResult:
    """Enciende el transmisor hasta el estado "listo" (`tx.ready_status`),
    sin subir alta tension ni habilitar salida -- ver docstring del modulo.

    `warmup_timeout_s` es obligatorio, sin default: el tiempo real de
    caldeo del magnetron del RD100S no existe todavia (el simulador usa un
    marcador de posicion de 3 minutos, ver PEND-RCP-07) -- inventar un
    default aqui seria fabricar el mismo tipo de numero sin respaldo que ya
    se evito en `antenna_positioning.py`.
    """

    steps: list[RoutineStepResult] = []

    all_ok = True
    for signal_id in INTERLOCK_SIGNALS:
        reading = await hal.read_digital(signal_id)
        ok = reading.value is True
        steps.append(RoutineStepResult(signal_id=signal_id, ok=ok, detail=f"precondicion (RCP, no exigida por tx.fsm para esta transicion): value={reading.value}"))
        all_ok = all_ok and ok
    if not all_ok:
        return RoutineResult(routine=RoutineName.TRANSMITTER_POWER_ON, outcome=RoutineOutcome.FAILED, steps=steps, at_us=_now_us())

    await hal.write_digital(COMMAND_ON, True)
    await asyncio.sleep(PULSE_S)
    await hal.write_digital(COMMAND_ON, False)
    steps.append(RoutineStepResult(signal_id=COMMAND_ON, ok=True, detail="pulso enviado (flanco de subida)"))

    deadline = time.monotonic() + STARTING_CONFIRM_TIMEOUT_S
    tx_on = False
    while time.monotonic() < deadline:
        reading = await hal.read_digital(TX_ON_STATUS)
        if reading.value is True:
            tx_on = True
            break
        await asyncio.sleep(POLL_INTERVAL_S)
    steps.append(RoutineStepResult(signal_id=TX_ON_STATUS, ok=tx_on, detail=f"value={tx_on} tras el pulso"))
    if not tx_on:
        return RoutineResult(routine=RoutineName.TRANSMITTER_POWER_ON, outcome=RoutineOutcome.FAILED, steps=steps, at_us=_now_us())

    deadline = time.monotonic() + warmup_timeout_s
    while time.monotonic() < deadline:
        ready = await hal.read_digital(READY_STATUS)
        if ready.value is True:
            steps.append(RoutineStepResult(signal_id=READY_STATUS, ok=True, detail="transmisor listo (caldeo completo)"))
            return RoutineResult(routine=RoutineName.TRANSMITTER_POWER_ON, outcome=RoutineOutcome.SUCCESS, steps=steps, at_us=_now_us())

        still_on = await hal.read_digital(TX_ON_STATUS)
        if still_on.value is not True:
            steps.append(RoutineStepResult(signal_id=TX_ON_STATUS, ok=False, detail="tx_on_status cayo durante el caldeo (apagado externo o falla)"))
            return RoutineResult(routine=RoutineName.TRANSMITTER_POWER_ON, outcome=RoutineOutcome.INTERRUPTED, steps=steps, at_us=_now_us())

        await asyncio.sleep(POLL_INTERVAL_S)

    steps.append(RoutineStepResult(signal_id=READY_STATUS, ok=False, detail=f"no se alcanzo ready_status en {warmup_timeout_s}s"))
    return RoutineResult(routine=RoutineName.TRANSMITTER_POWER_ON, outcome=RoutineOutcome.FAILED, steps=steps, at_us=_now_us())
