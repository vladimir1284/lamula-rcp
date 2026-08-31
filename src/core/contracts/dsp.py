"""RCP<->DSP/DRX (Fase 0, plan §6): modelo de dominio del stream de momentos.

Este modulo dejo de ser un borrador inventado localmente. El proyecto LAMULA DSP
congelo el formato de cable `DSP<->RCP v0.1` y aqui esta vendorizado en
`contract/vendor/dsp_rcp_v0_1.py`, anclado por hash en
`contract/vendor/UPSTREAM.toml`. Lo que sigue viviendo en este fichero es el
**modelo de dominio**: lo que ve `src/core/`, en unidades de ingenieria, sin una
sola nocion de bytes. La traduccion cable -> dominio es de
`src/adapters/dsp/wire.py`, segun la regla de AGENTS.md de que el core nunca ve
el crudo.

Que cambio respecto a la congelacion anterior, y por que:

* **`capture_t_us` se parte en dos.** Antes habia un solo instante, monotono del
  lado DSP, y quedaba sin resolver de donde salia la hora de pared que Level-II
  y ORPG exigen: sellarla al recibir mete la latencia del enlace dentro de la
  marca de tiempo de una observacion meteorologica. El contrato de cable ahora
  trae los dos (`acq_time_utc_ns` y `acq_monotonic_ns`), asi que el dominio
  tambien. Esto cierra la asuncion que AGENTS.md marcaba como pendiente de
  confirmar.
* **Entran los tres campos que solo el DSP conoce y que el Msg 31 del ICD
  2620002 pide**: velocidad de Nyquist, rango no ambiguo y PRF. Sin ellos el
  adaptador RCP<->ORPG no puede rellenar el mensaje y tendria que inventarlos.

Lo que NO cambio: el vocabulario de momentos (coincide campo por campo con la
enumeracion `moment_kind` del cable), `RadialStatus` y la forma de
`MomentProfile`.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from .common import MonotonicMicros, UtcInstant


class MomentId(StrEnum):
    """Vocabulario canonico de momentos, plan §6 — no inventar nombres nuevos.

    Coincide uno a uno con `moment_kind` del contrato de cable; el adaptador
    tiene un test que lo comprueba, para que una entrada nueva aguas arriba no
    entre en silencio como momento desconocido.
    """

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

    Nombres de este repo. En el cable esto viaja como banderas de bit
    (`ray_flags`), donde un radial puede ser a la vez principio de volumen y
    principio de elevacion; aqui se colapsa al estado unico que el resto del
    core espera, y el adaptador se encarga de la conversion. El mapeo a los
    codigos de estado de radial del ICD 2620002 (Msg 31/1) es tarea del
    adaptador RCP<->ORPG, no de este contrato.
    """

    START_OF_VOLUME = "start_of_volume"
    START_OF_ELEVATION = "start_of_elevation"
    INTERMEDIATE = "intermediate"
    END_OF_ELEVATION = "end_of_elevation"
    END_OF_VOLUME = "end_of_volume"


class MomentProfile(BaseModel):
    """Un momento a lo largo de un radial, ya en unidades de ingenieria.

    El cable v0.1 entrega f32 en unidades de ingenieria directamente
    (`data_type = f32`, con `scale = 1.0` y `offset = 0.0`), asi que el
    adaptador no reescala nada hoy. El descriptor de cable reserva `scale` y
    `offset` para una futura codificacion en entero de 16 bits; si algun dia se
    activa, la conversion es del adaptador y este modelo no se entera — que es
    justo la razon de que exista la separacion.
    """

    first_gate_range_m: float = Field(ge=0)
    gate_spacing_m: float = Field(gt=0)
    values: list[float]


class RadialMoments(BaseModel):
    """Un radial completo: metadatos de rayo + uno o mas momentos.

    Los dos relojes van por separado y con el nombre diciendo cual es cual:

    * `acq_time_utc` es hora de pared del instante de adquisicion, medida en el
      lado DSP y no al recibir. Es la que se archiva en Level-II y la que va a
      ORPG.
    * `acq_monotonic_us` es el mismo instante en el reloj monotono del DSP.
      Sirve para ordenar radiales y medir intervalos sin que un ajuste de UTC
      los corrompa. **No es comparable con el monotono de este proceso**, asi
      que no se resta contra relojes locales: solo contra otros radiales del
      mismo flujo.
    """

    azimuth_deg: float = Field(ge=0, lt=360)
    elevation_deg: float = Field(ge=-90, le=90)
    azimuth_resolution_deg: float = Field(gt=0)
    elevation_number: int = Field(ge=0)
    volume_number: int = Field(ge=0)
    radial_status: RadialStatus
    acq_time_utc: UtcInstant
    acq_monotonic_us: MonotonicMicros

    # Solo el DSP los conoce y el Msg 31 del ICD 2620002 los exige.
    nyquist_velocity_ms: float = Field(ge=0)
    unambiguous_range_m: float = Field(ge=0)
    prf_hz: float = Field(gt=0)

    moments: dict[MomentId, MomentProfile]
