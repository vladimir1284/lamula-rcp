"""RCP<->DSP/DRX (Fase 0, plan §6): formato de suscripcion/stream de momentos.

Dependencia externa (PEND-RCP-05): al momento de escribir esto no existe
implementacion de referencia ni simulador equivalente al `radar_emulator` del
HAL. Este contrato es una primera congelacion basada solo en lo que el plan
ya fija — enlace 1 GbE (D-03), vocabulario de momentos canonico (plan §6),
RCP como unico archivador (D-02) — no en un acuerdo verificado con el
proyecto DSP. Cada valor no confirmado lleva su propio PEND.

No se ha corrido, ni puede correrse todavia, un spike consumidor contra un
emisor real o simulado (a diferencia de HAL). Tratar como borrador sujeto a
romperse en cuanto exista una implementacion de referencia del lado DSP.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from .common import MonotonicMicros


class MomentId(StrEnum):
    """Vocabulario canonico de momentos, plan §6 — no inventar nombres nuevos."""

    UZ = "UZ"  # reflectividad no corregida
    CZ = "CZ"  # reflectividad corregida
    V = "V"  # velocidad radial
    W = "W"  # ancho espectral
    ZDR = "ZDR"  # reflectividad diferencial
    PHIDP = "PHIDP"  # fase diferencial (ΦDP)
    KDP = "KDP"  # fase diferencial especifica
    LDR = "LDR"  # relacion de despolarizacion lineal
    RHOHV = "RHOHV"  # coeficiente de correlacion (ρHV)
    SQI = "SQI"  # indice de calidad de senal
    CCOR = "CCOR"  # correccion de clutter
    SIG = "SIG"  # indicador de significancia
    I = "I"  # canal en fase, crudo
    Q = "Q"  # canal en cuadratura, crudo


class RadialStatus(StrEnum):
    """Framing de barrido/volumen dentro del stream de radiales.

    PEND-RCP-05: nombres de este repo, no un vocabulario acordado con DSP.
    El mapeo a los codigos de estado de radial del ICD 2620002 (Msg 31/1) es
    tarea del adaptador RCP<->ORPG, no de este contrato.
    """

    START_OF_VOLUME = "start_of_volume"
    START_OF_ELEVATION = "start_of_elevation"
    INTERMEDIATE = "intermediate"
    END_OF_ELEVATION = "end_of_elevation"
    END_OF_VOLUME = "end_of_volume"


class MomentProfile(BaseModel):
    """Un momento a lo largo de un radial, ya en unidades de ingenieria.

    PEND-RCP-05: si el DSP entrega crudo con escala/offset (probable para no
    saturar el enlace de 1 GbE, D-03) esa conversion es responsabilidad del
    adaptador `src/adapters/dsp/`, igual que la regla ya establecida para
    Modbus en docs/interfaces/modbus.md de `radar_emulator`. El core nunca ve
    el crudo.
    """

    first_gate_range_m: float = Field(ge=0)
    gate_spacing_m: float = Field(gt=0)
    values: list[float]


class RadialMoments(BaseModel):
    """Un radial completo: metadatos de rayo + uno o mas momentos.

    `capture_t_us` es el reloj monotono del lado DSP (AGENTS.md, "dos
    relojes"): el RCP le asigna hora de pared solo al archivar en Level-II o
    alimentar a ORPG, nunca antes. PEND-RCP-01 aplica igual aqui: confirmar
    con el equipo antes de congelar version 1 en firme.
    """

    azimuth_deg: float = Field(ge=0, lt=360)
    elevation_deg: float = Field(ge=-90, le=90)
    azimuth_resolution_deg: float = Field(gt=0)
    elevation_number: int = Field(ge=0)
    volume_number: int = Field(ge=0)
    radial_status: RadialStatus
    capture_t_us: MonotonicMicros
    moments: dict[MomentId, MomentProfile]
