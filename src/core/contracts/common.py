"""Primitivas compartidas por los tres contratos internos (HAL, DSP, MMI).

Dos relojes, no uno (AGENTS.md "Reglas que no se negocian"): `MonotonicMicros`
para telemetria interna y orquestacion soft-real-time; `datetime` (UTC) para
todo lo que un operador o un archivo NEXRAD deba interpretar como un instante
real. Ningun campo de este modulo mezcla los dos sentidos bajo un nombre
generico como "timestamp".
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import Field

# Microsegundos de un reloj monotono sin origen absoluto (arranque del
# proceso que lo produce). Nunca comparar valores de dos procesos distintos.
MonotonicMicros = Annotated[int, Field(ge=0)]


class SignalQuality(StrEnum):
    """Calidad de una lectura, comun a HAL y a cualquier valor derivado.

    `FAULT` no aparece en `radar_emulator` (docs/interfaces/modbus.md) porque
    el simulador no modela perdida de comunicacion con un modulo; se incluye
    aqui porque D-06 exige que ambos adaptadores implementen la misma
    interfaz, y el adaptador real si puede perder un nodo RS-485.
    """

    OK = "ok"
    OUT_OF_RANGE = "range"
    FAULT = "fault"
