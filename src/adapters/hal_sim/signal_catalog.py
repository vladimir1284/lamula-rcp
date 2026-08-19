"""Catalogo vendorizado de senales RD100S (heredado de `radar_emulator`).

Copia filtrada de `radar_emulator/config/rd100s.seed.json` -- decision
2026-08-19 (ver docs/alcance/pendientes.md, seccion "Heredados de
radar_emulator"): este repo mantiene su propia copia en vez de leer en vivo
del checkout sibling, para no depender de su filesystem en dev/CI. Puede
desincronizarse si `radar_emulator` cambia su mapa; resincronizar a mano
(`rd100s_signal_catalog.json`) si eso pasa.

Solo se vendorizan las 111 senales de kind DI/DO/AI/AO -- las de kind VIRT
(`ant.az_position`, `ant.el_position`, `ant.az_rate`, `ant.el_rate`,
`tx.interlocks_ok`) no tienen `modbus` (es null en la fuente): la posicion
de antena se expone por UDP, no por Modbus (ver `udp_encoder.py` y
`HardwareAbstractionLayer.read_antenna_position`), y `tx.interlocks_ok` es
interno al emulador, no observable por el controlador en absoluto.

Todo lo que ya estaba marcado como provisional en `radar_emulator` se
hereda tal cual: PEND-06 (escalado de senales analogicas: la fuente linkea
raw_range<->range de forma lineal, "PENDIENTE: confirmar codificacion y
rango crudo del modulo real"), PEND-07 (direcciones de 4069/4117/4150
inferidas por analogia) y PEND-08 (unit IDs arbitrarios).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

_CATALOG_PATH = Path(__file__).parent / "rd100s_signal_catalog.json"

ModbusSpace = Literal["coil", "holding"]
SignalKind = Literal["DI", "DO", "AI", "AO"]


@dataclass(frozen=True)
class RawEncoding:
    raw_lo: int
    raw_hi: int


@dataclass(frozen=True)
class SignalSpec:
    """Una fila del catalogo: identidad + destino Modbus + escalado opcional."""

    id: str
    subsystem: str
    kind: SignalKind
    type: Literal["bool", "float"]
    unit_id: int
    space: ModbusSpace
    address: int
    writable: bool
    units: str | None = None
    eng_lo: float | None = None
    eng_hi: float | None = None
    raw: RawEncoding | None = None

    def to_engineering(self, raw_value: int) -> float:
        """PEND-06: escalado lineal raw<->ingenieria, no confirmado contra hardware real."""
        if self.raw is None or self.eng_lo is None or self.eng_hi is None:
            raise ValueError(f"{self.id}: no tiene escalado de ingenieria (no es AI/AO)")
        span_raw = self.raw.raw_hi - self.raw.raw_lo
        span_eng = self.eng_hi - self.eng_lo
        return self.eng_lo + (raw_value - self.raw.raw_lo) * span_eng / span_raw

    def to_raw(self, eng_value: float) -> int:
        if self.raw is None or self.eng_lo is None or self.eng_hi is None:
            raise ValueError(f"{self.id}: no tiene escalado de ingenieria (no es AI/AO)")
        span_raw = self.raw.raw_hi - self.raw.raw_lo
        span_eng = self.eng_hi - self.eng_lo
        raw = self.raw.raw_lo + (eng_value - self.eng_lo) * span_raw / span_eng
        return max(self.raw.raw_lo, min(self.raw.raw_hi, round(raw)))


def _load(path: Path) -> dict[str, SignalSpec]:
    entries = json.loads(path.read_text())
    catalog: dict[str, SignalSpec] = {}
    for entry in entries:
        modbus = entry["modbus"]
        raw_enc = None
        eng_lo = eng_hi = None
        if "raw" in entry:
            lo, hi = entry["raw"]["raw_range"]
            raw_enc = RawEncoding(raw_lo=lo, raw_hi=hi)
        if "range" in entry:
            eng_lo, eng_hi = entry["range"]
        catalog[entry["id"]] = SignalSpec(
            id=entry["id"],
            subsystem=entry["subsystem"],
            kind=entry["kind"],
            type=entry["type"],
            unit_id=modbus["unit_id"],
            space=modbus["space"],
            address=modbus["address"],
            writable="w" in modbus["access"],
            units=entry.get("units"),
            eng_lo=eng_lo,
            eng_hi=eng_hi,
            raw=raw_enc,
        )
    return catalog


CATALOG: dict[str, SignalSpec] = _load(_CATALOG_PATH)


def get(signal_id: str) -> SignalSpec:
    try:
        return CATALOG[signal_id]
    except KeyError:
        raise KeyError(f"senal desconocida en el catalogo RD100S: {signal_id!r}") from None
