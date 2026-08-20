"""Rutina de control: "movimiento de antena" (plan §4.3, Rutina 5 de seis).

Primer borrador, igual estado que `general_power_on.py`: probado contra el
simulador, sin confirmar con el product expert -- ver PEND-RCP-07
(docs/alcance/pendientes.md) y la seccion "Rutina 5" de
docs/operacion/rutinas-control.md, que tiene las mismas preguntas abiertas
en lenguaje operativo.

**Diferencia de unidad que el diseno de rutinas-control.md no distingue:**
esa pagina describe la rutina como "enviar una velocidad deseada (grados/s)
al eje". La senal real (`ant.speed_reference_driver_az`/`_el`, ver catalogo
vendorizado) esta en **voltios** (rango ±10 V), no en grados/s -- es una
referencia analogica a un variador, igual que en el radar real. El bloque
`axis` del simulador la convierte con un `gain_deg_s_per_volt` (3.6 az, 1.5
el) marcado como PENDIENTE de confirmar ahi mismo; no existe hoy ninguna
ganancia real del RD100S que el RCP pueda usar para traducir grados/s a
voltios. Por eso esta rutina recibe `voltage_reference` en voltios, no una
velocidad en grados/s -- inventar una ganancia aqui seria un numero mas sin
respaldo, igual de sin confirmar que los que ya estan marcados PEND. La
conversion grados/s -> voltios queda pendiente de una ganancia real
(extension de PEND-RCP-07).

**Por que esta rutina consulta la guarda no solo antes de mover, sino
tambien mientras se mueve:** el bloque `axis` de elevacion sí lee su propio
fin de carrera (`inhibit_up`/`inhibit_down`) y se autolimita; el de azimut
**no** lee `ant.i2t_drive_az_status` -- el simulador calcula la falla
termica pero no corta el drive el mismo (ver docstring de
`core/safety_guard/antenna_limits.py`). Sin este sondeo activo, un viaje en
azimut que dispara la proteccion termica a mitad de camino seguiria
recibiendo la referencia de voltaje indefinidamente del lado del RCP.

**Lo que esta rutina NO confirma:** que el eje alcance la magnitud de
velocidad pedida (eso exigiria la misma ganancia real que no existe);
solo confirma sentido de giro (signo de `az_rate_deg_s`/`el_rate_deg_s`
coincide con el signo de `voltage_reference`) y que efectivamente hay
movimiento, vía `hal.read_antenna_position()` (fuente UDP, no Modbus).
"""

from __future__ import annotations

import asyncio
import time

from core.contracts.common import MonotonicMicros
from core.contracts.control import RoutineName, RoutineOutcome, RoutineResult, RoutineStepResult
from core.contracts.hal import HardwareAbstractionLayer
from core.contracts.safety import AntennaAxis, AntennaMoveDirection
from core.safety_guard import check_antenna_movement

AU_ON_STATUS = "ant.au_on_status"
ENABLE_DRIVE_SIGNAL = {
    AntennaAxis.AZIMUTH: "ant.enable_drive_az_conmand",
    AntennaAxis.ELEVATION: "ant.enable_drive_el_conmand",
}
SPEED_REFERENCE_SIGNAL = {
    AntennaAxis.AZIMUTH: "ant.speed_reference_driver_az",
    AntennaAxis.ELEVATION: "ant.speed_reference_driver_el",
}

# Umbral para distinguir "el eje se esta moviendo" de ruido/cero -- no una
# tolerancia de magnitud (esa exigiria la ganancia real, ver docstring del
# modulo). Igual de marcador de posicion que el resto de esta rutina.
MOVING_EPS_DEG_S = 0.05
STOPPED_EPS_DEG_S = 0.05

# Ciclo de sondeo y tope de espera para confirmar arranque de movimiento.
# El bloque `axis` del simulador acelera de forma limitada
# (`accel_deg_s2`, tambien PENDIENTE de confirmar) -- 5 s da margen amplio
# sin depender de ese valor exacto.
POLL_INTERVAL_S = 0.15
CONFIRM_TIMEOUT_S = 5.0


def _now_us() -> MonotonicMicros:
    return time.monotonic_ns() // 1000


def _rate_deg_s(position, axis: AntennaAxis) -> float:
    return position.az_rate_deg_s if axis is AntennaAxis.AZIMUTH else position.el_rate_deg_s


async def run_antenna_movement(
    hal: HardwareAbstractionLayer,
    axis: AntennaAxis,
    voltage_reference: float,
) -> RoutineResult:
    """Comanda el eje `axis` con `voltage_reference` voltios (±10 V, ver
    catalogo) de referencia de velocidad. `voltage_reference == 0.0` es un
    pedido de detencion: se trata distinto (nunca lo rechaza la guarda,
    no exige `ant.au_on_status`) porque frenar nunca es la accion insegura.
    """

    steps: list[RoutineStepResult] = []
    speed_signal = SPEED_REFERENCE_SIGNAL[axis]

    if voltage_reference == 0.0:
        await hal.write_analog(speed_signal, 0.0)
        steps.append(
            RoutineStepResult(signal_id=speed_signal, ok=True, detail="referencia puesta a 0 V (detencion solicitada)")
        )
        deadline = time.monotonic() + CONFIRM_TIMEOUT_S
        while time.monotonic() < deadline:
            position = await hal.read_antenna_position()
            rate = _rate_deg_s(position, axis)
            if abs(rate) <= STOPPED_EPS_DEG_S:
                steps.append(
                    RoutineStepResult(
                        signal_id=speed_signal,
                        ok=True,
                        detail=f"eje detenido: rate={rate:.3f} deg/s",
                    )
                )
                return RoutineResult(routine=RoutineName.ANTENNA_MOVEMENT, outcome=RoutineOutcome.SUCCESS, steps=steps, at_us=_now_us())
            await asyncio.sleep(POLL_INTERVAL_S)
        steps.append(
            RoutineStepResult(signal_id=speed_signal, ok=False, detail=f"no se confirmo detencion en {CONFIRM_TIMEOUT_S}s")
        )
        return RoutineResult(routine=RoutineName.ANTENNA_MOVEMENT, outcome=RoutineOutcome.FAILED, steps=steps, at_us=_now_us())

    au_on = await hal.read_digital(AU_ON_STATUS)
    steps.append(RoutineStepResult(signal_id=AU_ON_STATUS, ok=au_on.value is True, detail=f"precondicion: value={au_on.value}"))
    if au_on.value is not True:
        return RoutineResult(routine=RoutineName.ANTENNA_MOVEMENT, outcome=RoutineOutcome.FAILED, steps=steps, at_us=_now_us())

    direction = AntennaMoveDirection.UP if voltage_reference > 0 else AntennaMoveDirection.DOWN
    guard = await check_antenna_movement(hal, axis, direction)
    steps.append(RoutineStepResult(signal_id=guard.signal_id, ok=guard.allowed, detail=f"guarda: {guard.reason}"))
    if not guard.allowed:
        return RoutineResult(routine=RoutineName.ANTENNA_MOVEMENT, outcome=RoutineOutcome.FAILED, steps=steps, at_us=_now_us())

    enable_signal = ENABLE_DRIVE_SIGNAL[axis]
    await hal.write_digital(enable_signal, True)
    steps.append(RoutineStepResult(signal_id=enable_signal, ok=True, detail="variador habilitado"))
    await hal.write_analog(speed_signal, voltage_reference)
    steps.append(RoutineStepResult(signal_id=speed_signal, ok=True, detail=f"referencia comandada: {voltage_reference} V"))

    # A partir de aca el eje esta recibiendo una referencia de voltaje != 0 --
    # si la tarea (asyncio) que corre esta rutina se cancela (job cancelado
    # desde la MMI) en cualquier `await` de este bloque, dejaria el eje
    # girando indefinidamente sin pasar por ninguno de los dos caminos que ya
    # lo detienen (guarda/timeout de mas abajo). `except BaseException` (no
    # solo `asyncio.CancelledError`) a proposito: verificado contra un HAL
    # real que si la cancelacion llega mientras un `await hal.write_analog`/
    # `read_*` esta en vuelo, pymodbus no deja propagar un `CancelledError`
    # limpio -- lo convierte en su propia `ModbusIOException` ("Request
    # cancelled outside library"), que `except CancelledError` no atrapaba
    # (bug encontrado end-to-end: la antena seguia girando tras "cancelar").
    # `core/` no puede importar pymodbus para atrapar ese tipo exacto (limite
    # core/adapters, AGENTS.md), asi que se atrapa cualquier excepcion aca;
    # se re-lanza despues de detener para que quien cancelo
    # (adapters/gateway/app.py) siga viendo el error/cancelacion propagarse.
    deadline = time.monotonic() + CONFIRM_TIMEOUT_S
    try:
        while time.monotonic() < deadline:
            await asyncio.sleep(POLL_INTERVAL_S)

            guard = await check_antenna_movement(hal, axis, direction)
            if not guard.allowed:
                await hal.write_analog(speed_signal, 0.0)
                if axis is AntennaAxis.AZIMUTH:
                    await hal.write_digital(enable_signal, False)
                steps.append(
                    RoutineStepResult(
                        signal_id=guard.signal_id,
                        ok=False,
                        detail=f"guarda rechazo continuar, movimiento detenido: {guard.reason}",
                    )
                )
                return RoutineResult(routine=RoutineName.ANTENNA_MOVEMENT, outcome=RoutineOutcome.INTERRUPTED, steps=steps, at_us=_now_us())

            position = await hal.read_antenna_position()
            rate = _rate_deg_s(position, axis)
            if (rate > 0) == (voltage_reference > 0) and abs(rate) > MOVING_EPS_DEG_S:
                steps.append(
                    RoutineStepResult(
                        signal_id=speed_signal,
                        ok=True,
                        detail=f"movimiento confirmado en el sentido pedido: rate={rate:.3f} deg/s",
                    )
                )
                return RoutineResult(routine=RoutineName.ANTENNA_MOVEMENT, outcome=RoutineOutcome.SUCCESS, steps=steps, at_us=_now_us())

        await hal.write_analog(speed_signal, 0.0)
        steps.append(
            RoutineStepResult(
                signal_id=speed_signal,
                ok=False,
                detail=f"no se confirmo movimiento en {CONFIRM_TIMEOUT_S}s, referencia devuelta a 0 V",
            )
        )
        return RoutineResult(routine=RoutineName.ANTENNA_MOVEMENT, outcome=RoutineOutcome.FAILED, steps=steps, at_us=_now_us())
    except BaseException:
        await hal.write_analog(speed_signal, 0.0)
        raise
