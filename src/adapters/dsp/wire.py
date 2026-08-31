"""Adaptador RCP<->DSP -- traduccion del formato de cable al modelo de dominio.

Este es el unico sitio del repo que sabe que el stream de momentos tiene bytes.
`src/core/` ve `RadialMoments` en unidades de ingenieria y nunca un buffer, que
es la regla de AGENTS.md sobre el crudo, la misma que ya rige para Modbus.

El formato lo define el proyecto LAMULA DSP y esta vendorizado en
`contract/vendor/dsp_rcp_v0_1.py`. Nada de aqui reimplementa la disposicion de
los campos: los tamanos y las cadenas de `struct` salen del modulo generado.

Sobre rendimiento: los valores de un momento se desempaquetan con `struct` a una
lista de Python porque `MomentProfile.values` es `list[float]` y este repo aun no
depende de NumPy. Cuando NumPy entre (esta en la pila del plan), el sitio donde
poner `numpy.frombuffer(buf, "<f4")` sobre una vista sin copia es exactamente
`_decode_moment_block`; el cable lleva f32 denso justo para permitirlo.
"""

from __future__ import annotations

import struct
from datetime import UTC, datetime

from contract.vendor import dsp_rcp_v0_1 as wire
from core.contracts.dsp import MomentId, MomentProfile, RadialMoments, RadialStatus

#: Valor de `moment_kind` en el cable -> miembro del vocabulario del dominio.
#: Se construye por NOMBRE, no por numero: si el proyecto DSP anade un momento,
#: aqui falta la entrada y el decodificador lo dice en vez de quedarse callado.
#: `test_wire.py` comprueba que los dos vocabularios siguen coincidiendo.
MOMENT_BY_WIRE_VALUE: dict[int, MomentId] = {
    getattr(wire.MomentKind, member.name): member
    for member in MomentId
    if hasattr(wire.MomentKind, member.name)
}


class WireFormatError(ValueError):
    """Trama que no cumple el contrato. Nunca se ignora en silencio."""


def parse_frame_header(data: bytes) -> wire.Header:
    """Valida y devuelve la cabecera comun de 12 B.

    Comprueba `magic` y `version_major` antes que nada: el contrato hermano
    DRx<->DSP usa una cabecera del mismo tamano y forma, asi que un cable
    cruzado produce una trama que "parece" valida hasta que se mira el magic.
    """
    if len(data) < wire.Header.SIZE:
        raise WireFormatError(
            f"cabecera corta: {len(data)} B, se esperaban {wire.Header.SIZE}"
        )

    header = wire.Header.unpack(data)
    if header.magic != wire.MAGIC:
        raise WireFormatError(
            f"magic {header.magic:#010x} no es el de DSP<->RCP ({wire.MAGIC:#010x});"
            " puede ser un flujo DRx<->DSP mal enrutado"
        )
    if header.version_major != wire.VERSION_MAJOR:
        raise WireFormatError(
            f"version_major {header.version_major} incompatible con"
            f" {wire.VERSION_MAJOR}"
        )
    return header


def _radial_status(ray_flags: int) -> RadialStatus:
    """Colapsa las banderas de bit del cable al estado unico del dominio.

    Un radial puede llevar varias banderas a la vez —principio de volumen es
    tambien principio de elevacion—, asi que el orden de comprobacion es el
    orden de prioridad: lo mas externo gana. Se pierde informacion a proposito;
    el adaptador RCP<->ORPG, que si necesita el detalle, lee el cable, no esto.
    """
    if ray_flags & wire.RayFlag.VOLUME_START:
        return RadialStatus.START_OF_VOLUME
    if ray_flags & wire.RayFlag.VOLUME_END:
        return RadialStatus.END_OF_VOLUME
    if ray_flags & wire.RayFlag.SWEEP_START:
        return RadialStatus.START_OF_ELEVATION
    if ray_flags & wire.RayFlag.SWEEP_END:
        return RadialStatus.END_OF_ELEVATION
    return RadialStatus.INTERMEDIATE


def _azimuth_center_and_width(start_deg: float, end_deg: float) -> tuple[float, float]:
    """Centro y anchura de un radial, tolerando el cruce por 360 grados.

    Restar sin mas da -359.5 en vez de 0.5 para un radial que abre en 359.75 y
    cierra en 0.25, y el centro saldria en el lado opuesto de la antena. El
    modulo 360 lo arregla; que el resultado caiga en [0, 360) lo exige el
    modelo de dominio.
    """
    width = (end_deg - start_deg) % 360.0
    center = (start_deg + width / 2.0) % 360.0
    return center, width


def _decode_moment_block(
    payload: bytes, offset: int, ray: wire.MomentRay
) -> tuple[MomentId, MomentProfile, int]:
    """Un descriptor de momento mas sus valores. Devuelve el offset siguiente."""
    end = offset + wire.MomentField.SIZE
    if end > len(payload):
        raise WireFormatError("carga util corta: falta un descriptor de momento")

    field = wire.MomentField.unpack(payload[offset:end])

    if field.data_type != wire.DataType.F32:
        raise WireFormatError(
            f"data_type {field.data_type} no soportado; v0.1 solo define f32"
        )
    if field.n_gates != ray.n_gates:
        raise WireFormatError(
            f"el momento declara {field.n_gates} celdas y el radial {ray.n_gates}"
        )

    kind = MOMENT_BY_WIRE_VALUE.get(field.kind)
    if kind is None:
        raise WireFormatError(
            f"momento desconocido {field.kind}; el vocabulario del cable creció"
            " y este adaptador no se actualizó"
        )

    values_end = end + 4 * field.n_gates
    if values_end > len(payload):
        raise WireFormatError(
            f"carga util corta: {kind} declara {field.n_gates} celdas"
            f" y solo quedan {len(payload) - end} bytes"
        )

    values = list(struct.unpack_from(f"<{field.n_gates}f", payload, end))

    profile = MomentProfile(
        first_gate_range_m=ray.start_range_m,
        gate_spacing_m=ray.gate_spacing_m,
        values=values,
    )
    return kind, profile, values_end


def decode_moment_ray(body: bytes) -> RadialMoments:
    """Cuerpo completo de un `moment_ray` (cabecera + carga util) -> dominio."""
    if len(body) < wire.MomentRay.SIZE:
        raise WireFormatError(
            f"moment_ray corto: {len(body)} B, se esperaban al menos"
            f" {wire.MomentRay.SIZE}"
        )

    ray = wire.MomentRay.unpack(body)
    payload = body[wire.MomentRay.SIZE :]

    azimuth_deg, azimuth_width_deg = _azimuth_center_and_width(
        ray.az_start_deg, ray.az_end_deg
    )
    if azimuth_width_deg <= 0.0:
        raise WireFormatError(
            "el radial no barre azimut alguno: az_start y az_end coinciden"
        )

    moments: dict[MomentId, MomentProfile] = {}
    offset = 0
    for _ in range(ray.n_moments):
        kind, profile, offset = _decode_moment_block(payload, offset, ray)
        if kind in moments:
            raise WireFormatError(f"el radial trae {kind} dos veces")
        moments[kind] = profile

    if offset != len(payload):
        raise WireFormatError(
            f"sobran {len(payload) - offset} bytes tras los {ray.n_moments}"
            " bloques de momento"
        )

    return RadialMoments(
        azimuth_deg=azimuth_deg,
        elevation_deg=(ray.el_start_deg + ray.el_end_deg) / 2.0,
        azimuth_resolution_deg=azimuth_width_deg,
        elevation_number=ray.sweep_seq,
        volume_number=ray.volume_seq,
        radial_status=_radial_status(ray.ray_flags),
        # El instante viene medido en el DSP, no se sella al recibir: sellarlo
        # aqui metería la latencia del enlace dentro de la marca de tiempo de
        # una observacion meteorologica.
        acq_time_utc=datetime.fromtimestamp(ray.acq_time_utc_ns / 1e9, tz=UTC),
        acq_monotonic_us=ray.acq_monotonic_ns // 1000,
        nyquist_velocity_ms=ray.nyquist_velocity,
        unambiguous_range_m=ray.unambiguous_range_m,
        prf_hz=ray.prf_hz,
        moments=moments,
    )


def frame(msg_type: int, body: bytes) -> bytes:
    """Envuelve un cuerpo con la cabecera comun. Para el plano de control."""
    header = wire.Header(
        magic=wire.MAGIC,
        version_major=wire.VERSION_MAJOR,
        version_minor=wire.VERSION_MINOR,
        msg_type=msg_type,
        flags=0,
        payload_len=len(body),
    )
    return header.pack() + body


def encode_selftest_request(seq: int, nonce: int) -> bytes:
    """Autotest de enlace. Obligatorio en cada reconexion del RCP."""
    body = wire.SelftestRequest(seq=seq, nonce=nonce).pack()
    return frame(wire.MsgType.SELFTEST_REQUEST, body)


def encode_control(seq: int, command: int) -> bytes:
    """Mandato del plano de control; ver `wire.Command`."""
    body = wire.Control(seq=seq, command=command).pack()
    return frame(wire.MsgType.CONTROL, body)
