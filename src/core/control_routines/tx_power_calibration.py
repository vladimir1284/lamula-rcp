"""Rutina de control guiada por wizard: "G3 — TX Power Calibration" (RAVIS §7.4.1 / §14).

Procedimiento guiado de calibración de potencia de transmisión con entrada
manual de lecturas del operador y verificación del temporizador de caldeo de radiación.

Precondiciones:
- Modo remoto en LCU/sistema (`sys.remote_mode_ok_status`)
- Modo remoto en ACU (`ant.antenna_remote_status`)
- Radiación activa (`tx.radiating_status`)
- Tiempo de caldeo de radiación transcurrido (mínimo 20 min = 1200 s)

PEND-RCP-16 (ver docs/alcance/pendientes.md): esta rutina cubre una unica
lectura escalar de potencia pico y un unico offset de acoplador. El RAVIS
§7.4.1 describe una tabla por ancho de pulso (`PerPulseWidthInputTable`) mas
`TX Pwr Transl. coeff.`, `TX Power Nom.` y `Actual lin. Power`, que no estan
implementados aqui -- alcance deliberadamente acotado a este slice de wizard,
sin confirmar aun con el product expert.
"""

from __future__ import annotations

import inspect
import time
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from core.contracts.common import MonotonicMicros, SignalQuality
from core.contracts.control import RoutineName, RoutineOutcome, RoutineResult, RoutineStepResult
from core.contracts.hal import HardwareAbstractionLayer
from core.contracts.mmi import CalibrationLogEntry

PRECONDITIONS = (
    "sys.remote_mode_ok_status",
    "ant.antenna_remote_status",
    "tx.radiating_status",
)


def _now_us() -> MonotonicMicros:
    return time.monotonic_ns() // 1000


async def run_tx_power_calibration(
    hal: HardwareAbstractionLayer,
    *,
    actor: str = "operator",
    step_input_func: Callable[[], Awaitable[dict[str, Any]]] | None = None,
    on_step_change_func: Callable[[int, int, str, str], Awaitable[None] | None] | None = None,
    record_log_func: Callable[[CalibrationLogEntry], None] | None = None,
    warmup_duration_s: float = 1200.0,
    required_warmup_s: float = 1200.0,
) -> RoutineResult:
    """Ejecuta la calibración guiada de potencia TX.
    Soporta pasos interactivos donde espera confirmación/entrada del operador.
    """
    steps: list[RoutineStepResult] = []
    now_wall = datetime.now(timezone.utc)

    # Paso 1: Verificación de Precondiciones y Caldeo de Radiación
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

    if required_warmup_s > 0 and warmup_duration_s < required_warmup_s:
        steps.append(
            RoutineStepResult(
                signal_id="tx.radiating_status",
                ok=False,
                detail=f"caldeo insuficiente: {warmup_duration_s:.0f}s / {required_warmup_s:.0f}s requeridos",
            )
        )
        all_ok = False

    if not all_ok:
        if record_log_func:
            record_log_func(
                CalibrationLogEntry(
                    at_wall=now_wall,
                    severity="error",
                    procedure="TX Power Calibration",
                    actor=actor,
                    message="Calibración TX fallida: precondiciones o tiempo de caldeo de radiación no cumplidos",
                )
            )
        return RoutineResult(
            routine=RoutineName.TX_POWER_CALIBRATION,
            outcome=RoutineOutcome.FAILED,
            steps=steps,
            at_us=_now_us(),
        )

    if record_log_func:
        record_log_func(
            CalibrationLogEntry(
                at_wall=now_wall,
                severity="info",
                procedure="TX Power Calibration",
                actor=actor,
                message="Paso 1/3 completado: Precondiciones y caldeo de radiación verificados",
            )
        )

    # Paso 2: Entrada de Potencia Pico Medida (Input del operador)
    if on_step_change_func:
        res = on_step_change_func(
            2, 3, "Entrada de Potencia de Referencia", "Ingrese la potencia pico medida en kW con un medidor de potencia externo"
        )
        if inspect.isawaitable(res):
            await res

    measured_power_kw = 250.0  # valor nominal si no hay callback
    if step_input_func:
        input_data = await step_input_func()
        measured_power_kw = float(input_data.get("measured_power_kw", 250.0))

    try:
        sample_reading = await hal.read_analog("tx.tx_peak_power_sample")
        sample_val: float | None = sample_reading.value
        sample_quality = sample_reading.quality
    except Exception:
        sample_val = None
        sample_quality = SignalQuality.FAULT

    sample_str = f"{sample_val:.2f} kW" if sample_val is not None else "no disponible"

    steps.append(
        RoutineStepResult(
            signal_id="tx.tx_peak_power_sample",
            ok=True,
            detail=(
                f"Potencia pico medida: {measured_power_kw:.2f} kW "
                f"(muestra HAL: {sample_str}, quality={sample_quality})"
            ),
        )
    )

    if record_log_func:
        record_log_func(
            CalibrationLogEntry(
                at_wall=datetime.now(timezone.utc),
                severity="info",
                procedure="TX Power Calibration",
                actor=actor,
                message=f"Paso 2/3 completado: Potencia pico medida registrada: {measured_power_kw:.2f} kW",
                detail=f"Muestra HAL: {sample_str} (quality={sample_quality})",
            )
        )

    # Paso 3: Ajuste / Confirmación de Offset de Acoplador
    if on_step_change_func:
        res = on_step_change_func(
            3, 3, "Ajuste de Desfase de Acoplador", "Confirme el offset de atenuación del acoplador direccionador (dB)"
        )
        if inspect.isawaitable(res):
            await res

    coupler_offset_db = 0.0
    if step_input_func:
        input_data = await step_input_func()
        coupler_offset_db = float(input_data.get("coupler_offset_db", 0.0))

    steps.append(
        RoutineStepResult(
            signal_id="tx.directional_coupler_offset",
            ok=True,
            detail=f"Offset de acoplador confirmado: {coupler_offset_db:.2f} dB",
        )
    )

    if record_log_func:
        record_log_func(
            CalibrationLogEntry(
                at_wall=datetime.now(timezone.utc),
                severity="info",
                procedure="TX Power Calibration",
                actor=actor,
                message=f"Paso 3/3 completado: Calibración de potencia TX finalizada con éxito (offset: {coupler_offset_db:.2f} dB)",
            )
        )

    return RoutineResult(
        routine=RoutineName.TX_POWER_CALIBRATION,
        outcome=RoutineOutcome.SUCCESS,
        steps=steps,
        at_us=_now_us(),
    )
