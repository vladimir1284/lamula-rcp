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
ningun adaptador HAL/DSP que los reciba -- `scan_controller.py` no los
aplica a nada (PEND-RCP-10). Este contrato define la forma de un escaneo,
no implementa enviarlo a ningun lado.

**Guarda de duty cycle (PEND-RCP-08, parcialmente resuelto 2026-08-20):**
el feedback del experto confirma que `Duty Cycle Ok/Fault` es una senal de
hardware pura (la tarjeta del modulador corta la transmision ella misma,
`tx.duty_cycle_ok_status` en el catalogo) -- el RCP nunca necesito una
senal HAL nueva ni un adaptador de forma de onda para esto, el bloqueo
original estaba mal planteado. Lo que el RCP si debe hacer es la cuenta en
software al momento de captura del dato (VCP personalizado, este
Worksheet manual): `duty = prf_hz * pulse_width_us * 1e-6`, rechazada aqui
mismo si excede `DUTY_CYCLE_LIMIT`. **`DUTY_CYCLE_LIMIT` es un marcador de
posicion generico (0.001, "limite tipico/estandar" del reporte del
experto), no el limite real de este RD100S** -- el mismo reporte da otros
tres casos (magnetron VMS1157 0.0006, MRL-5 0.0005, modulador de estado
solido La Habana 0.0005/0.0008, hasta 0.002 segun modo) sin confirmar cual
aplica aca; el catalogo usa nomenclatura `tx.magnetron_*`, lo que sugiere
el caso magnetron y no el de estado solido, pero es inferencia por nombre
de senal, no confirmacion directa. Perfiles predefinidos (VCP fijo por el
sistema) no pasan por esta guarda -- no existe todavia mecanismo de
perfiles en este repo.

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

from .common import MonotonicMicros
from .control import RoutineOutcome, RoutineStepResult
from .dsp import MomentId

DUTY_CYCLE_LIMIT = 0.001
"""Marcador de posicion generico (PEND-RCP-08), no el limite real del
RD100S -- ver docstring del modulo."""


def _check_duty_cycle(prf_hz: float, pulse_width_us: float) -> None:
    duty = prf_hz * pulse_width_us * 1e-6
    if duty > DUTY_CYCLE_LIMIT:
        raise ValueError(
            f"duty cycle {duty:.6f} excede el limite {DUTY_CYCLE_LIMIT} "
            f"(prf_hz={prf_hz}, pulse_width_us={pulse_width_us})"
        )


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

    @model_validator(mode="after")
    def _duty_cycle_dentro_de_limite(self) -> "PpiCut":
        _check_duty_cycle(self.prf_hz, self.pulse_width_us)
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

    @model_validator(mode="after")
    def _duty_cycle_dentro_de_limite(self) -> "RhiCut":
        _check_duty_cycle(self.prf_hz, self.pulse_width_us)
        return self


ScanCut = Annotated[Union[PpiCut, RhiCut], Field(discriminator="mode")]


class ScanWorksheet(BaseModel):
    """Una secuencia de cortes que el operador arma a mano. Sin campo de
    "volumen"/VCP -- ver docstring del modulo.

    **Nota (2026-08-20):** la vista MMI "Scan Worksheet"
    (`mmi/src/views/ScanWorksheetView.vue`) y los endpoints del gateway
    (`GET/POST/DELETE /api/scan/worksheet`) todavia no usan este modelo --
    implementan una lista plana de `ScanCut` sin nombre ni el minimo de un
    corte (`min_length=1` aqui exigiria al menos uno; el gateway arranca
    con la lista vacia). Es una decision de alcance para el primer borrador
    (un unico worksheet implicito, sin necesidad de nombre todavia), no una
    inconsistencia pasada por alto. Si en algun momento se necesita mas de
    un worksheet nombrado (o el `min_length=1` importa de verdad), este
    modelo es el punto de partida para esa migracion."""

    name: str
    cuts: list[ScanCut] = Field(min_length=1)


class AxisPositioningParams(BaseModel):
    """Los cuatro parametros obligatorios (sin default, ver
    `core/control_routines/antenna_positioning.py`) que la Rutina 6 exige
    para posicionar UN eje. `core/scan_controller.py` necesita uno de estos
    por eje (azimut y elevacion pueden tener ganancias/tolerancias reales
    distintas) -- vive aqui, no en `control.py`, porque solo tiene sentido
    junto a `PpiCut`/`RhiCut`."""

    gain_v_per_deg: float
    max_voltage: float
    tolerance_deg: float
    timeout_s: float


class ScanCutResult(BaseModel):
    """Resultado de `core.scan_controller.run_scan_cut`.

    Mismo espiritu que `RoutineResult` (`core/contracts/control.py`), pero
    sin `routine: RoutineName`: el Scan Controller no es una de las seis
    rutinas del plan (Sec. 4.3), es un orquestador que las consume -- no le
    corresponde ese campo cerrado."""

    outcome: RoutineOutcome
    steps: list[RoutineStepResult]
    at_us: MonotonicMicros
