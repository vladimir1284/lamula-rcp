"""GENERADO por tools/gen_contract.py a partir de contract/schema/dsp_rcp_v0_1.toml. NO EDITAR A MANO.

Contrato DSP↔RCP v0.1 — lado RCP y
banco de pruebas. Es una de las tres implementaciones generadas de la misma
fuente: si las tres no producen los mismos bytes, el codegen está mal.

Las cargas útiles de array (los bloques de momento de un moment_ray, la traza
de un spectrum_frame) NO se desempaquetan aquí campo a campo: se mapean con
`numpy.frombuffer(buf, '<f4')`, que da una vista sin copia sobre el búfer
recibido. Desempaquetarlas con `struct` anularía la razón de que el cable
lleve f32 denso.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

MAGIC = 0x4C4D4453
VERSION_MAJOR = 0
VERSION_MINOR = 1

@dataclass
class Header:
    """Cabecera común a todo mensaje."""

    FORMAT = "<IBBBBI"
    SIZE = 12
    FIELDS = ("magic", "version_major", "version_minor", "msg_type", "flags", "payload_len",)

    magic: int = 0
    version_major: int = 0
    version_minor: int = 0
    msg_type: int = 0
    flags: int = 0
    payload_len: int = 0

    def pack(self) -> bytes:
        return struct.pack(self.FORMAT, *(getattr(self, name) for name in self.FIELDS))

    @classmethod
    def unpack(cls, data: bytes) -> "Header":
        return cls(*struct.unpack(cls.FORMAT, data[: cls.SIZE]))

class MsgType:
    """Tipos de mensaje que viajan sueltos por el cable."""

    MOMENT_RAY = 1
    SPECTRUM_FRAME = 2
    STATUS = 3
    BITE_EVENT = 4
    CONFIG_ACK = 5
    SELFTEST_RESULT = 6
    CAPABILITIES = 7
    CONFIG = 8
    CONTROL = 9
    SELFTEST_REQUEST = 10

@dataclass
class MomentRay:
    """Un radial de momentos: la observación autoritativa que el RCP archiva"""

    FORMAT = "<IQQIHHHHHBBBBHffffffffffff"
    SIZE = 88
    FIELDS = ("seq", "acq_time_utc_ns", "acq_monotonic_ns", "volume_seq", "sweep_seq", "ray_index", "n_gates", "n_pulses", "bins_valid", "n_moments", "sweep_mode", "prf_mode", "ray_flags", "pad0", "az_start_deg", "az_end_deg", "el_start_deg", "el_end_deg", "fixed_angle_deg", "start_range_m", "gate_spacing_m", "prf_hz", "nyquist_velocity", "unambiguous_range_m", "noise_floor_dbm", "radar_constant_db",)

    seq: int = 0
    acq_time_utc_ns: int = 0
    acq_monotonic_ns: int = 0
    volume_seq: int = 0
    sweep_seq: int = 0
    ray_index: int = 0
    n_gates: int = 0
    n_pulses: int = 0
    bins_valid: int = 0
    n_moments: int = 0
    sweep_mode: int = 0
    prf_mode: int = 0
    ray_flags: int = 0
    pad0: int = 0
    az_start_deg: float = 0.0
    az_end_deg: float = 0.0
    el_start_deg: float = 0.0
    el_end_deg: float = 0.0
    fixed_angle_deg: float = 0.0
    start_range_m: float = 0.0
    gate_spacing_m: float = 0.0
    prf_hz: float = 0.0
    nyquist_velocity: float = 0.0
    unambiguous_range_m: float = 0.0
    noise_floor_dbm: float = 0.0
    radar_constant_db: float = 0.0

    def pack(self) -> bytes:
        return struct.pack(self.FORMAT, *(getattr(self, name) for name in self.FIELDS))

    @classmethod
    def unpack(cls, data: bytes) -> "MomentRay":
        return cls(*struct.unpack(cls.FORMAT, data[: cls.SIZE]))

@dataclass
class MomentField:
    """Descriptor de un momento dentro de la carga útil de un moment_ray."""

    FORMAT = "<BBBBIff"
    SIZE = 16
    FIELDS = ("kind", "data_type", "flags", "pad0", "n_gates", "scale", "offset",)

    kind: int = 0
    data_type: int = 0
    flags: int = 0
    pad0: int = 0
    n_gates: int = 0
    scale: float = 0.0
    offset: float = 0.0

    def pack(self) -> bytes:
        return struct.pack(self.FORMAT, *(getattr(self, name) for name in self.FIELDS))

    @classmethod
    def unpack(cls, data: bytes) -> "MomentField":
        return cls(*struct.unpack(cls.FORMAT, data[: cls.SIZE]))

@dataclass
class SpectrumFrame:
    """Traza del analizador de espectro de FI. Detrás van `n_bins` valores f32"""

    FORMAT = "<IQHBBfffI"
    SIZE = 32
    FIELDS = ("seq", "capture_time_utc_ns", "n_bins", "channel", "flags", "center_freq_hz", "span_hz", "ref_level_dbm", "pad0",)

    seq: int = 0
    capture_time_utc_ns: int = 0
    n_bins: int = 0
    channel: int = 0
    flags: int = 0
    center_freq_hz: float = 0.0
    span_hz: float = 0.0
    ref_level_dbm: float = 0.0
    pad0: int = 0

    def pack(self) -> bytes:
        return struct.pack(self.FORMAT, *(getattr(self, name) for name in self.FIELDS))

    @classmethod
    def unpack(cls, data: bytes) -> "SpectrumFrame":
        return cls(*struct.unpack(cls.FORMAT, data[: cls.SIZE]))

@dataclass
class Status:
    """Salud y telemetría. Se emite periódicamente y ante cualquier cambio de"""

    FORMAT = "<IBBBBIIIIIIIIIIIIffffffffffff"
    SIZE = 104
    FIELDS = ("uptime_s", "phase", "severity", "last_error", "n_rx_channels", "capability_flags", "bite_flags", "config_seq", "rays_in", "rays_out", "rays_dropped", "queue_depth", "bins_ok", "bins_total", "trigger_period_cmd_ns", "trigger_period_meas_ns", "pad0", "noise_floor_dbm_0", "noise_floor_dbm_1", "noise_floor_dbm_2", "noise_floor_dbm_3", "dc_offset_i_0", "dc_offset_i_1", "dc_offset_i_2", "dc_offset_i_3", "dc_offset_q_0", "dc_offset_q_1", "dc_offset_q_2", "dc_offset_q_3",)

    uptime_s: int = 0
    phase: int = 0
    severity: int = 0
    last_error: int = 0
    n_rx_channels: int = 0
    capability_flags: int = 0
    bite_flags: int = 0
    config_seq: int = 0
    rays_in: int = 0
    rays_out: int = 0
    rays_dropped: int = 0
    queue_depth: int = 0
    bins_ok: int = 0
    bins_total: int = 0
    trigger_period_cmd_ns: int = 0
    trigger_period_meas_ns: int = 0
    pad0: int = 0
    noise_floor_dbm_0: float = 0.0
    noise_floor_dbm_1: float = 0.0
    noise_floor_dbm_2: float = 0.0
    noise_floor_dbm_3: float = 0.0
    dc_offset_i_0: float = 0.0
    dc_offset_i_1: float = 0.0
    dc_offset_i_2: float = 0.0
    dc_offset_i_3: float = 0.0
    dc_offset_q_0: float = 0.0
    dc_offset_q_1: float = 0.0
    dc_offset_q_2: float = 0.0
    dc_offset_q_3: float = 0.0

    def pack(self) -> bytes:
        return struct.pack(self.FORMAT, *(getattr(self, name) for name in self.FIELDS))

    @classmethod
    def unpack(cls, data: bytes) -> "Status":
        return cls(*struct.unpack(cls.FORMAT, data[: cls.SIZE]))

@dataclass
class BiteEvent:
    """Un suceso de BITE con su instante. Detrás van `text_len` bytes UTF-8 de"""

    FORMAT = "<QIIBBBB"
    SIZE = 20
    FIELDS = ("event_time_utc_ns", "code", "value", "severity", "subsystem", "text_len", "pad0",)

    event_time_utc_ns: int = 0
    code: int = 0
    value: int = 0
    severity: int = 0
    subsystem: int = 0
    text_len: int = 0
    pad0: int = 0

    def pack(self) -> bytes:
        return struct.pack(self.FORMAT, *(getattr(self, name) for name in self.FIELDS))

    @classmethod
    def unpack(cls, data: bytes) -> "BiteEvent":
        return cls(*struct.unpack(cls.FORMAT, data[: cls.SIZE]))

@dataclass
class ConfigAck:
    """Respuesta a un config. `error` distinto de 0 significa que NO se aplicó"""

    FORMAT = "<IBBH"
    SIZE = 8
    FIELDS = ("seq", "error", "pad0", "pad1",)

    seq: int = 0
    error: int = 0
    pad0: int = 0
    pad1: int = 0

    def pack(self) -> bytes:
        return struct.pack(self.FORMAT, *(getattr(self, name) for name in self.FIELDS))

    @classmethod
    def unpack(cls, data: bytes) -> "ConfigAck":
        return cls(*struct.unpack(cls.FORMAT, data[: cls.SIZE]))

@dataclass
class SelftestResult:
    """Resultado del autotest de enlace. El plan (§6.1) lo exige en cada"""

    FORMAT = "<IIIBBBB"
    SIZE = 16
    FIELDS = ("seq", "nonce", "capability_flags", "error", "version_major", "version_minor", "pad0",)

    seq: int = 0
    nonce: int = 0
    capability_flags: int = 0
    error: int = 0
    version_major: int = 0
    version_minor: int = 0
    pad0: int = 0

    def pack(self) -> bytes:
        return struct.pack(self.FORMAT, *(getattr(self, name) for name in self.FIELDS))

    @classmethod
    def unpack(cls, data: bytes) -> "SelftestResult":
        return cls(*struct.unpack(cls.FORMAT, data[: cls.SIZE]))

@dataclass
class Capabilities:
    """Qué sabe hacer esta compilación del DSP. Se responde a un control con"""

    FORMAT = "<IIIIHBB"
    SIZE = 20
    FIELDS = ("moment_mask", "dealias_mask", "estimator_mask", "max_gates", "max_pulses", "n_rx_channels", "pad0",)

    moment_mask: int = 0
    dealias_mask: int = 0
    estimator_mask: int = 0
    max_gates: int = 0
    max_pulses: int = 0
    n_rx_channels: int = 0
    pad0: int = 0

    def pack(self) -> bytes:
        return struct.pack(self.FORMAT, *(getattr(self, name) for name in self.FIELDS))

    @classmethod
    def unpack(cls, data: bytes) -> "Capabilities":
        return cls(*struct.unpack(cls.FORMAT, data[: cls.SIZE]))

@dataclass
class Config:
    """Configuración completa. Se aplica de forma atómica: o entra entera o se"""

    FORMAT = "<IIHHBBBBBBBBffffffffffffffI"
    SIZE = 80
    FIELDS = ("seq", "moment_mask", "n_pulses", "n_gates", "clutter_filter", "dealias_mode", "sweep_mode", "estimator", "rfi_filter", "range_dealias", "prf_ratio_num", "prf_ratio_den", "start_range_m", "gate_spacing_m", "prf_hz", "sqi_threshold", "sig_threshold", "ccor_threshold", "log_threshold", "clutter_width_ms", "radar_constant_db", "noise_floor_dbm", "receiver_gain_db", "zdr_offset_db", "phidp_offset_deg", "wavelength_m", "pad0",)

    seq: int = 0
    moment_mask: int = 0
    n_pulses: int = 0
    n_gates: int = 0
    clutter_filter: int = 0
    dealias_mode: int = 0
    sweep_mode: int = 0
    estimator: int = 0
    rfi_filter: int = 0
    range_dealias: int = 0
    prf_ratio_num: int = 0
    prf_ratio_den: int = 0
    start_range_m: float = 0.0
    gate_spacing_m: float = 0.0
    prf_hz: float = 0.0
    sqi_threshold: float = 0.0
    sig_threshold: float = 0.0
    ccor_threshold: float = 0.0
    log_threshold: float = 0.0
    clutter_width_ms: float = 0.0
    radar_constant_db: float = 0.0
    noise_floor_dbm: float = 0.0
    receiver_gain_db: float = 0.0
    zdr_offset_db: float = 0.0
    phidp_offset_deg: float = 0.0
    wavelength_m: float = 0.0
    pad0: int = 0

    def pack(self) -> bytes:
        return struct.pack(self.FORMAT, *(getattr(self, name) for name in self.FIELDS))

    @classmethod
    def unpack(cls, data: bytes) -> "Config":
        return cls(*struct.unpack(cls.FORMAT, data[: cls.SIZE]))

@dataclass
class Control:
    """Mandato del plano de control. Se responde siempre con un config_ack."""

    FORMAT = "<IBBH"
    SIZE = 8
    FIELDS = ("seq", "command", "pad0", "pad1",)

    seq: int = 0
    command: int = 0
    pad0: int = 0
    pad1: int = 0

    def pack(self) -> bytes:
        return struct.pack(self.FORMAT, *(getattr(self, name) for name in self.FIELDS))

    @classmethod
    def unpack(cls, data: bytes) -> "Control":
        return cls(*struct.unpack(cls.FORMAT, data[: cls.SIZE]))

@dataclass
class SelftestRequest:
    """Arranca el autotest de enlace. Obligatorio en cada reconexión del RCP."""

    FORMAT = "<II"
    SIZE = 8
    FIELDS = ("seq", "nonce",)

    seq: int = 0
    nonce: int = 0

    def pack(self) -> bytes:
        return struct.pack(self.FORMAT, *(getattr(self, name) for name in self.FIELDS))

    @classmethod
    def unpack(cls, data: bytes) -> "SelftestRequest":
        return cls(*struct.unpack(cls.FORMAT, data[: cls.SIZE]))

class Error:
    """Códigos de rechazo del plano de control."""

    OK = 0
    UNSUPPORTED_VERSION = 1
    UNKNOWN_MESSAGE = 2
    BAD_LENGTH = 3
    NOT_IN_SETUP_PHASE = 4
    NOT_CONFIGURED = 5
    MOMENT_UNSUPPORTED = 6
    DEALIAS_UNSUPPORTED = 7
    ESTIMATOR_UNSUPPORTED = 8
    THRESHOLD_OUT_OF_RANGE = 9
    PRF_RANGE_ILLEGAL = 10
    GATE_COUNT_ILLEGAL = 11
    SELFTEST_FAILED = 12
    DRX_LINK_DOWN = 13

class MomentKind:
    """Vocabulario canónico de momentos, común a los planes del DSP y del RCP."""

    UZ = 0
    CZ = 1
    V = 2
    W = 3
    ZDR = 4
    PHIDP = 5
    KDP = 6
    LDR = 7
    RHOHV = 8
    SQI = 9
    CCOR = 10
    SIG = 11
    I = 12
    Q = 13

class RayFlag:
    """Banderas por radial. Un radial con problemas se MARCA, no se descarta."""

    SWEEP_START = 1
    SWEEP_END = 2
    VOLUME_START = 4
    VOLUME_END = 8
    CENSORED = 16
    DEALIAS_FAILED = 32
    CLUTTER_FILTERED = 64
    FIRST_AFTER_CONFIG = 128

class MomentFlag:
    """Banderas por bloque de momento dentro de un radial."""

    HAS_MISSING = 1
    CORRECTED = 2
    FILTERED = 4

class Phase:
    """Fases del DSP. Configurar y adquirir son pasos distintos."""

    SETUP = 0
    RUNNING = 1
    FAULT = 2

class Command:
    """Mandatos del plano de control."""

    ENTER_SETUP = 0
    START = 1
    STOP = 2
    REQUEST_STATUS = 3
    REQUEST_CONFIG = 4
    REQUEST_CAPABILITIES = 5
    RESET_COUNTERS = 6

class SweepMode:
    """Modos de barrido."""

    PPI = 0
    RHI = 1
    SECTOR = 2
    POINT = 3
    MANUAL = 4

class DealiasMode:
    """Modos de extensión del intervalo de velocidad no ambigua."""

    NONE = 0
    DUAL_PRF = 1
    STAGGERED_PRT = 2

class Estimator:
    """Estimadores de momentos."""

    PULSE_PAIR = 0
    SPECTRAL = 1

class ClutterFilter:
    """Filtros de eco fijo."""

    NONE = 0
    GMAP = 1
    NOTCH = 2

class DataType:
    """Codificación de los valores de un bloque de momento."""

    F32 = 0
    I16_SCALED = 1

class Severity:
    """Niveles de severidad, comunes a status y a los sucesos de BITE."""

    INFO = 0
    WARNING = 1
    FAULT = 2
    CONFIG_ERROR = 3

class CapabilityFlag:
    """Modos de proceso que una compilación del DSP puede ofrecer."""

    DUAL_POL = 1
    SPECTRAL_ESTIMATOR = 2
    DUAL_PRF = 4
    STAGGERED_PRT = 8
    RANGE_DEALIAS = 16
    RFI_FILTER = 32
    SPECTRUM_FEED = 64
    IQ_ARCHIVE = 128

class BiteFlag:
    """Catálogo de fallos del DSP."""

    INGEST_DROP = 1
    QUEUE_OVERFLOW = 2
    DRX_LINK_DOWN = 4
    DRX_CONFIG_REJECTED = 8
    TRIGGER_DRIFT = 16
    NOISE_FLOOR_DRIFT = 32
    MOMENT_OVERRUN = 64
    CALIBRATION_STALE = 128
    RCP_LINK_DOWN = 256
    ARCHIVE_FULL = 512
