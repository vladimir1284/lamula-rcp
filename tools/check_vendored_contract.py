#!/usr/bin/env python3
"""Comprueba el ancla del contrato DSP↔RCP vendorizado.

El contrato `DSP↔RCP` lo posee el proyecto LAMULA DSP (plan del DSP §6). Aquí
sólo se consume: `contract/vendor/dsp_rcp_v0_1.py` y
`mmi/src/contracts/dsp_rcp_v0_1.ts` son copias byte a byte de su salida
generada. Este comprobador falla si:

  * un fichero vendorizado no coincide con el SHA-256 anotado en
    `contract/vendor/UPSTREAM.toml` — alguien lo editó, o una herramienta lo
    reescribió sin querer (Prettier sobre `mmi/src/` es el candidato obvio, por
    eso el fichero lleva `/* eslint-disable */` y hay que dejarlo fuera del
    formateo);
  * el repositorio del DSP está accesible y su salida generada ha cambiado
    respecto a lo vendorizado, lo que significa que el contrato se movió aguas
    arriba y aquí nadie se enteró.

Lo segundo es aviso y no fallo cuando el repositorio del DSP no está montado: el
CI de este repo no puede depender de que lo esté. Con `--strict` sí falla, para
el trabajo local donde los dos repositorios conviven.

Uso:
    python3 tools/check_vendored_contract.py
    python3 tools/check_vendored_contract.py --strict
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN = ROOT / "contract" / "vendor" / "UPSTREAM.toml"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Falla, y no solo avisa, si el repositorio del DSP no esta o divergio.",
    )
    args = ap.parse_args()

    pin = tomllib.loads(PIN.read_text(encoding="utf-8"))
    errors: list[str] = []
    warnings: list[str] = []

    for entry in pin["file"]:
        path = ROOT / entry["path"]
        if not path.exists():
            errors.append(f"falta {entry['path']}")
            continue
        actual = sha256(path)
        if actual != entry["sha256"]:
            errors.append(
                f"{entry['path']} no coincide con el ancla\n"
                f"    esperado {entry['sha256']}\n"
                f"    obtenido {actual}\n"
                "    Nada vendorizado se edita a mano. Si el cambio viene del DSP,"
                " re-vendoriza y actualiza UPSTREAM.toml."
            )

    upstream_root = (ROOT / pin["upstream"]["repo_path"]).resolve()
    if not upstream_root.is_dir():
        warnings.append(
            f"repositorio del DSP no encontrado en {upstream_root};"
            " no se comprueba divergencia con el origen"
        )
    else:
        watched = [(e["source"], e["sha256"]) for e in pin["file"]]
        watched += [(e["source"], e["sha256"]) for e in pin["watch"]]
        for source, expected in watched:
            path = upstream_root / source
            if not path.exists():
                warnings.append(f"el origen ya no tiene {source}")
                continue
            actual = sha256(path)
            if actual != expected:
                message = (
                    f"el origen cambio: {source}\n"
                    f"    vendorizado {expected}\n"
                    f"    origen      {actual}\n"
                    "    El contrato se movio aguas arriba. Re-vendoriza y sube el ancla."
                )
                (errors if args.strict else warnings).append(message)

    for warning in warnings:
        print(f"AVISO: {warning}", file=sys.stderr)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors:
        return 1

    version = pin["contract"]
    print(
        "contrato vendorizado integro: "
        f"{pin['upstream']['project']} "
        f"v{version['version_major']}.{version['version_minor']}"
        f" @ {pin['upstream']['commit']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
