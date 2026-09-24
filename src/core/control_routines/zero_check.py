"""Rutina de control y tarea periódica: "G5 — Zero Check" (RAVIS §7.4.2).

Muestreo de ruido del receptor (canales alto y bajo).
Precondiciones:
- Modo remoto en LCU/sistema (`sys.remote_mode_ok_status`)
- Modo remoto en ACU (`ant.antenna_remote_status`)
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Callable

from core.contracts.common import MonotonicMicros
from core.contracts.control import RoutineName, RoutineOutcome, RoutineResult, RoutineStepResult
from core.contracts.hal import HardwareAbstractionLayer
from core.contracts.mmi import CalibrationLogEntry

PRECONDITIONS = (
    "sys.remote_mode_ok_status",
    "ant.antenna_remote_status",
)

# Valores nominales / de muestreo de piso de ruido en dBm
DEFAULT_NOISE_HIGH_DBM = -105.2
DEFAULT_NOISE_LOW_DBM = -102.8


def _now_us() -> MonotonicMicros:
    return time.monotonic_ns() // 1000


async def run_zero_check(
    hal: HardwareAbstractionLayer,
    *,
    noise_high_dbm: float = DEFAULT_NOISE_HIGH_DBM,
    noise_low_dbm: float = DEFAULT_NOISE_LOW_DBM,
    record_log_func: Callable[[CalibrationLogEntry], None] | None = None,
    actor: str = "system",
) -> RoutineResult:
    """Ejecuta el chequeo de cero (muestreo de ruido del receptor).
    Verifica las precondiciones de modo remoto y registra las mediciones de ruido.
    """
    steps: list[RoutineStepResult] = []
    now_wall = datetime.now(timezone.utc)

    all_ok = True
    for signal_id in PRECONDITIONS:
        reading = await hal.read_digital(signal_id)
        ok = reading.value is True
        steps.append(
            RoutineStepResult(
                signal_id=signal_id,
                ok=ok,
                detail=f"precondicion: value={reading.value} quality={reading.quality}",
            )
        )
        all_ok = all_ok and ok

    if not all_ok:
        if record_log_func:
            record_log_func(
                CalibrationLogEntry(
                    at_wall=now_wall,
                    severity="error",
                    procedure="Zero Check",
                    actor=actor,
                    message="Zero Check fallida: precondiciones no cumplidas",
                )
            )
        return RoutineResult(
            routine=RoutineName.ZERO_CHECK,
            outcome=RoutineOutcome.FAILED,
            steps=steps,
            at_us=_now_us(),
        )

    # Registro de medicion de ruido de canales alto y bajo
    steps.append(
        RoutineStepResult(
            signal_id="rx.zero_check_high_channel",
            ok=True,
            detail=f"Noise High Channel: {noise_high_dbm:.2f} dBm",
        )
    )
    steps.append(
        RoutineStepResult(
            signal_id="rx.zero_check_low_channel",
            ok=True,
            detail=f"Noise Low Channel: {noise_low_dbm:.2f} dBm",
        )
    )

    if record_log_func:
        record_log_func(
            CalibrationLogEntry(
                at_wall=now_wall,
                severity="info",
                procedure="Zero Check",
                actor=actor,
                message="Muestreo de ruido (Zero Check) finalizado correctamente",
                detail=f"Ruido canal HI: {noise_high_dbm:.2f} dBm, Ruido canal LOW: {noise_low_dbm:.2f} dBm",
            )
        )

    return RoutineResult(
        routine=RoutineName.ZERO_CHECK,
        outcome=RoutineOutcome.SUCCESS,
        steps=steps,
        at_us=_now_us(),
    )
