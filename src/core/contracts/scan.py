"""Scan Worksheet manual (plan §4.3/§8.2 Fase 2: "interactive scans (Scan
Worksheet equivalent)"), distinto del scheduler de volumen automatico y,
sobre todo, distinto de VCP.

**Deliberadamente NO es el concepto VCP de WSR-88D:** VCP vive del lado
RCP<->ORPG (ICD 2620002, Msg 6 "VCP change", Msg 5 definicion de VCP) y es
responsabilidad de Fase 3 ("emulacion RDA completa"), empujado por ORPG,
no algo que este repo defina localmente -- ver
`spike-fase0/RESULTADO-rda-orpg.md` ("`RDA_TCPServer.py` tambien contesta
... process_VCP ... Ese alcance corresponde a Fase 3, no a este spike").
Este modulo es la definicion de un escaneo que el operador arma el mismo
desde la MMI sin pasar por ORPG -- lo que el plan llama "Scan Worksheet
(interactive)", en contraposicion al scheduler automatico.

**PEND-RCP-09 (nuevo, ver docs/alcance/pendientes.md):** cuando se cablee
RCP<->ORPG en Fase 3, reconciliar este modelo con VCP real -- puede que el
scheduler de volumen automatico termine consumiendo VCPs de ORPG en vez
de (o ademas de) este Worksheet manual. No se anticipa esa forma aqui.

**PRF y pulse width son solo datos, todavia sin ejecutor:** no existe
ningun adaptador HAL/DSP que los reciba -- la guarda de PRF x pulse-width
(plan §4.3) sigue bloqueada por PEND-RCP-08. Este contrato define la
forma de un escaneo, no implementa enviarlo a ningun lado.

**Velocidad de rotacion de la antena durante el escaneo: fuera de este
contrato a proposito.** Relacionar PRF/pulse-width/ancho de haz con una
velocidad de barrido es teoria de escaneo de radar real (muestras por
radial para SNR/estimacion de velocidad adecuada) -- inventar esa formula
o un campo con semantica no confirmada seria el mismo error ya evitado en
`antenna_positioning.py`. Ver PEND-RCP-09.
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, model_validator

from .dsp import MomentId


class PpiCut(BaseModel):
    """Elevacion fija, barre azimut -- vista PPI (plan §3)."""

    mode: Literal["ppi"] = "ppi"
    elevation_deg: float = Field(ge=-90, le=90)
    azimuth_start_deg: float = Field(ge=0, lt=360)
    # le=360, no lt=360 como azimuth_start_deg: 360 aqui es una vuelta completa
    # (0 -> 360), un valor distinto de "0" para el extremo final del barrido.
    azimuth_end_deg: float = Field(ge=0, le=360)
    prf_hz: float = Field(gt=0)
    pulse_width_us: float = Field(gt=0)
    moments: list[MomentId] = Field(min_length=1)

    @model_validator(mode="after")
    def _sweep_no_degenerado(self) -> "PpiCut":
        if self.azimuth_start_deg == self.azimuth_end_deg:
            raise ValueError("azimuth_start_deg y azimuth_end_deg no pueden ser iguales (barrido de ancho cero)")
        return self


class RhiCut(BaseModel):
    """Azimut fijo, barre elevacion -- vista RHI (plan §3)."""

    mode: Literal["rhi"] = "rhi"
    azimuth_deg: float = Field(ge=0, lt=360)
    elevation_start_deg: float = Field(ge=-90, le=90)
    elevation_end_deg: float = Field(ge=-90, le=90)
    prf_hz: float = Field(gt=0)
    pulse_width_us: float = Field(gt=0)
    moments: list[MomentId] = Field(min_length=1)

    @model_validator(mode="after")
    def _sweep_no_degenerado(self) -> "RhiCut":
        if self.elevation_start_deg == self.elevation_end_deg:
            raise ValueError("elevation_start_deg y elevation_end_deg no pueden ser iguales (barrido de ancho cero)")
        return self


ScanCut = Annotated[Union[PpiCut, RhiCut], Field(discriminator="mode")]


class ScanWorksheet(BaseModel):
    """Una secuencia de cortes que el operador arma a mano. Sin campo de
    "volumen"/VCP -- ver docstring del modulo."""

    name: str
    cuts: list[ScanCut] = Field(min_length=1)
