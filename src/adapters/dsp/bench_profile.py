"""Perfil de configuracion fijo para el banco de integracion (fase C0).

**Andamio de banco, no comportamiento de operador.** En produccion quien
decide la configuracion del DSP es el Scan Controller, a partir del Scan
Worksheet; ese mapeo sigue sin resolverse (PEND-RCP-10) y este modulo no lo
adelanta ni lo sustituye. Aqui solo se lee un JSON con campos del contrato
`dsp_rcp` y se construye el `Config` tal cual, para poder llevar a un DSP real
de `setup` a `running` sin inventarse una vista de MMI por el camino.

El DSP valida lo que le llega (`crates/rcp-link/src/validate.rs`): momentos
dentro de sus capacidades, estimador soportado, umbrales en rango y, sobre
todo, `start_range_m + n_gates * gate_spacing_m <= c / (2 * prf_hz)`. Un
perfil que no cumpla eso vuelve como `config_ack` con error y el DSP se queda
en `setup`.
"""

from __future__ import annotations

import json
from pathlib import Path

from contract.vendor import dsp_rcp_v0_1 as wire


def _moment_mask(names: list[str]) -> int:
    mask = 0
    for name in names:
        try:
            mask |= 1 << getattr(wire.MomentKind, name)
        except AttributeError as exc:  # nombre que no existe en el contrato
            raise ValueError(
                f"momento desconocido en el perfil: {name!r};"
                f" validos: {[m for m in dir(wire.MomentKind) if not m.startswith('_')]}"
            ) from exc
    return mask


def load_bench_profile(path: Path) -> wire.Config:
    """Construye un `Config` del contrato a partir del JSON de `path`.

    Las claves del JSON son nombres de campo de `wire.Config`, salvo
    `moments`, que es una lista de nombres de `wire.MomentKind` y se traduce a
    `moment_mask`. Una clave que no sea campo del contrato es un error: es
    mucho mas probable que sea una errata que una extension deliberada.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    # JSON no tiene comentarios: las claves con guion bajo delante son notas
    # del fichero, no campos del contrato.
    data = {k: v for k, v in data.items() if not k.startswith("_")}
    if "moments" in data:
        data["moment_mask"] = _moment_mask(data.pop("moments"))
    unknown = set(data) - set(wire.Config.FIELDS)
    if unknown:
        raise ValueError(
            f"campos que no existen en dsp_rcp.Config: {sorted(unknown)}."
            " Si el contrato se movio, re-vendoriza antes de tocar el perfil."
        )
    return wire.Config(**data)
