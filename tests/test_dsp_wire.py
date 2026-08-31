"""Adaptador RCP<->DSP: decodificacion del formato de cable real.

Sustituye a lo que validaba `spike-fase0/dsp_moment_stream_spike.py`, que
ejercitaba un framing inventado en este repo. Aqui las tramas se construyen con
el modulo vendorizado del proyecto DSP, asi que lo que se prueba es el formato
acordado y no uno propio.
"""

from __future__ import annotations

import struct
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from contract.vendor import dsp_rcp_v0_1 as wire
from adapters.dsp.wire import (
    MOMENT_BY_WIRE_VALUE,
    WireFormatError,
    decode_moment_ray,
    encode_control,
    encode_selftest_request,
    parse_frame_header,
)
from core.contracts.dsp import MomentId, RadialStatus


def build_ray(
    *,
    moments: dict[int, list[float]],
    az_start: float = 10.0,
    az_end: float = 11.0,
    el_start: float = 0.5,
    el_end: float = 0.5,
    ray_flags: int = 0,
    n_gates: int | None = None,
    acq_utc_ns: int = 1_800_000_000_000_000_000,
    acq_mono_ns: int = 123_456_789_000,
) -> bytes:
    """Cuerpo de un `moment_ray` construido con el modulo generado."""
    gates = n_gates if n_gates is not None else len(next(iter(moments.values())))
    header = wire.MomentRay(
        seq=7,
        acq_time_utc_ns=acq_utc_ns,
        acq_monotonic_ns=acq_mono_ns,
        volume_seq=3,
        sweep_seq=2,
        ray_index=41,
        n_gates=gates,
        n_pulses=64,
        bins_valid=gates,
        n_moments=len(moments),
        sweep_mode=wire.SweepMode.PPI,
        prf_mode=wire.DealiasMode.NONE,
        ray_flags=ray_flags,
        pad0=0,
        az_start_deg=az_start,
        az_end_deg=az_end,
        el_start_deg=el_start,
        el_end_deg=el_end,
        fixed_angle_deg=0.5,
        start_range_m=125.0,
        gate_spacing_m=250.0,
        prf_hz=600.0,
        nyquist_velocity=8.3,
        unambiguous_range_m=249_827.0,
        noise_floor_dbm=-113.0,
        radar_constant_db=68.5,
    )

    payload = b""
    for kind, values in moments.items():
        payload += wire.MomentField(
            kind=kind,
            data_type=wire.DataType.F32,
            flags=0,
            pad0=0,
            n_gates=len(values),
            scale=1.0,
            offset=0.0,
        ).pack()
        payload += struct.pack(f"<{len(values)}f", *values)

    return header.pack() + payload


# --- Vocabulario ------------------------------------------------------------


def test_los_dos_vocabularios_de_momentos_coinciden():
    """El dominio y el cable nombran los mismos momentos.

    Si el proyecto DSP anade una entrada a `moment_kind` y aqui no se refleja,
    el decodificador la rechaza en vez de tragarla; este test lo dice antes, al
    re-vendorizar, en vez de en produccion.
    """
    del_cable = {
        name
        for name in vars(wire.MomentKind)
        if name.isupper() and not name.startswith("_")
    }
    del_dominio = {member.name for member in MomentId}
    assert del_cable == del_dominio

    # Y el mapeo cubre el vocabulario entero, no un subconjunto.
    assert len(MOMENT_BY_WIRE_VALUE) == len(MomentId)


# --- Cabecera de trama ------------------------------------------------------


def test_cabecera_valida():
    header = wire.Header(
        magic=wire.MAGIC,
        version_major=wire.VERSION_MAJOR,
        version_minor=wire.VERSION_MINOR,
        msg_type=wire.MsgType.MOMENT_RAY,
        flags=0,
        payload_len=88,
    )
    parsed = parse_frame_header(header.pack())
    assert parsed.msg_type == wire.MsgType.MOMENT_RAY
    assert parsed.payload_len == 88


def test_una_trama_del_contrato_hermano_se_rechaza():
    """El DRx<->DSP usa una cabecera del mismo tamano y forma.

    Sin comprobar el magic, un cable cruzado produce una trama que parece
    valida: 12 bytes, campos en su sitio, longitud plausible. Es exactamente el
    fallo que el magic distinto existe para atrapar.
    """
    drx_magic = 0x4C4D4452
    trama = struct.pack("<IBBBBI", drx_magic, 0, 1, 1, 0, 36)
    with pytest.raises(WireFormatError, match="mal enrutado"):
        parse_frame_header(trama)


def test_version_major_incompatible_se_rechaza():
    trama = struct.pack("<IBBBBI", wire.MAGIC, 9, 0, 1, 0, 0)
    with pytest.raises(WireFormatError, match="version_major"):
        parse_frame_header(trama)


# --- Radial de momentos -----------------------------------------------------


def test_decodifica_un_radial_completo():
    uz = [10.0, 20.5, 30.25, -5.0]
    v = [-8.0, 0.0, 4.5, 8.25]
    radial = decode_moment_ray(
        build_ray(moments={wire.MomentKind.UZ: uz, wire.MomentKind.V: v})
    )

    assert set(radial.moments) == {MomentId.UZ, MomentId.V}
    assert radial.moments[MomentId.UZ].values == uz
    assert radial.moments[MomentId.V].values == v
    assert radial.moments[MomentId.UZ].first_gate_range_m == 125.0
    assert radial.moments[MomentId.UZ].gate_spacing_m == 250.0
    assert radial.volume_number == 3
    assert radial.elevation_number == 2
    assert radial.prf_hz == pytest.approx(600.0)
    assert radial.unambiguous_range_m == pytest.approx(249_827.0)


def test_los_dos_relojes_llegan_separados():
    """La hora de pared la mide el DSP; no se sella al recibir."""
    utc_ns = 1_800_000_000_123_456_789
    radial = decode_moment_ray(
        build_ray(
            moments={wire.MomentKind.UZ: [1.0]},
            acq_utc_ns=utc_ns,
            acq_mono_ns=987_654_321_000,
        )
    )
    assert radial.acq_time_utc.tzinfo is not None
    assert radial.acq_time_utc == datetime.fromtimestamp(utc_ns / 1e9, tz=UTC)
    assert radial.acq_monotonic_us == 987_654_321
    # Los dos sentidos no se mezclan: el monotono no es una hora de pared.
    assert radial.acq_monotonic_us != int(radial.acq_time_utc.timestamp() * 1e6)


@pytest.mark.parametrize(
    ("flags", "esperado"),
    [
        (0, RadialStatus.INTERMEDIATE),
        (wire.RayFlag.SWEEP_START, RadialStatus.START_OF_ELEVATION),
        (wire.RayFlag.SWEEP_END, RadialStatus.END_OF_ELEVATION),
        (wire.RayFlag.VOLUME_START, RadialStatus.START_OF_VOLUME),
        (wire.RayFlag.VOLUME_END, RadialStatus.END_OF_VOLUME),
        # Un primer radial de volumen es tambien primer radial de elevacion:
        # gana lo mas externo.
        (
            wire.RayFlag.VOLUME_START | wire.RayFlag.SWEEP_START,
            RadialStatus.START_OF_VOLUME,
        ),
    ],
)
def test_banderas_a_estado_de_radial(flags, esperado):
    radial = decode_moment_ray(
        build_ray(moments={wire.MomentKind.UZ: [1.0]}, ray_flags=flags)
    )
    assert radial.radial_status is esperado


def test_azimut_que_cruza_por_cero():
    """Restar sin modulo daria -359.5 de anchura y el centro en la antipoda."""
    radial = decode_moment_ray(
        build_ray(moments={wire.MomentKind.UZ: [1.0]}, az_start=359.75, az_end=0.25)
    )
    assert radial.azimuth_resolution_deg == pytest.approx(0.5, abs=1e-3)
    assert radial.azimuth_deg == pytest.approx(0.0, abs=1e-3)


def test_azimut_normal_no_se_ve_afectado():
    radial = decode_moment_ray(
        build_ray(moments={wire.MomentKind.UZ: [1.0]}, az_start=10.0, az_end=11.0)
    )
    assert radial.azimuth_resolution_deg == pytest.approx(1.0, abs=1e-3)
    assert radial.azimuth_deg == pytest.approx(10.5, abs=1e-3)


# --- Rechazos ---------------------------------------------------------------


def test_carga_util_corta():
    body = build_ray(moments={wire.MomentKind.UZ: [1.0, 2.0, 3.0, 4.0]})
    with pytest.raises(WireFormatError, match="corta"):
        decode_moment_ray(body[:-6])


def test_sobran_bytes_tras_los_momentos():
    body = build_ray(moments={wire.MomentKind.UZ: [1.0]}) + b"\x00\x00\x00\x00"
    with pytest.raises(WireFormatError, match="sobran"):
        decode_moment_ray(body)


def test_momento_desconocido():
    body = build_ray(moments={200: [1.0]})
    with pytest.raises(WireFormatError, match="desconocido"):
        decode_moment_ray(body)


def test_data_type_no_soportado():
    header = wire.MomentRay.unpack(build_ray(moments={wire.MomentKind.UZ: [1.0]}))
    body = header.pack()
    body += wire.MomentField(
        kind=wire.MomentKind.UZ,
        data_type=wire.DataType.I16_SCALED,
        flags=0,
        pad0=0,
        n_gates=1,
        scale=0.5,
        offset=-32.0,
    ).pack()
    body += struct.pack("<h", 100) + b"\x00\x00"
    with pytest.raises(WireFormatError, match="data_type"):
        decode_moment_ray(body)


def test_conteo_de_celdas_incoherente():
    """El descriptor y el radial tienen que decir lo mismo."""
    body = build_ray(moments={wire.MomentKind.UZ: [1.0, 2.0]}, n_gates=5)
    with pytest.raises(WireFormatError, match="celdas"):
        decode_moment_ray(body)


def test_momento_repetido():
    header = wire.MomentRay.unpack(build_ray(moments={wire.MomentKind.UZ: [1.0]}))
    bloque = wire.MomentField(
        kind=wire.MomentKind.UZ,
        data_type=wire.DataType.F32,
        flags=0,
        pad0=0,
        n_gates=1,
        scale=1.0,
        offset=0.0,
    ).pack() + struct.pack("<f", 1.0)
    header.n_moments = 2
    with pytest.raises(WireFormatError, match="dos veces"):
        decode_moment_ray(header.pack() + bloque + bloque)


def test_radial_sin_anchura_de_azimut():
    body = build_ray(moments={wire.MomentKind.UZ: [1.0]}, az_start=10.0, az_end=10.0)
    with pytest.raises(WireFormatError, match="azimut"):
        decode_moment_ray(body)


def test_elevacion_fuera_de_rango_la_para_el_modelo():
    """El dominio valida aunque el cable no: f32 admite 200 grados, la antena no."""
    body = build_ray(
        moments={wire.MomentKind.UZ: [1.0]}, el_start=200.0, el_end=200.0
    )
    with pytest.raises(ValidationError):
        decode_moment_ray(body)


# --- Plano de control -------------------------------------------------------


def test_selftest_request_va_enmarcado():
    trama = encode_selftest_request(seq=1, nonce=0xDEADBEEF)
    header = parse_frame_header(trama)
    assert header.msg_type == wire.MsgType.SELFTEST_REQUEST
    assert header.payload_len == wire.SelftestRequest.SIZE
    cuerpo = wire.SelftestRequest.unpack(trama[wire.Header.SIZE :])
    assert cuerpo.nonce == 0xDEADBEEF


def test_control_va_enmarcado():
    trama = encode_control(seq=2, command=wire.Command.START)
    header = parse_frame_header(trama)
    assert header.msg_type == wire.MsgType.CONTROL
    assert wire.Control.unpack(trama[wire.Header.SIZE :]).command == wire.Command.START


# --- Camino completo por socket ---------------------------------------------


def test_el_receptor_decodifica_un_volumen_por_socket():
    """Equivalente real del spike de Fase 0, pero con el framing acordado.

    Se levanta el receptor, se le manda un volumen sintetico con el formato de
    cable de verdad, y se comprueba que sale el radial esperado. Va por socket
    y no llamando al decodificador directamente porque lo que se prueba aqui es
    el framing: que `payload_len` cuente lo que dice contar y que el lector no
    se desincronice entre mensajes.
    """
    import asyncio

    from adapters.dsp.moment_stream_receiver import MomentStreamReceiver
    from adapters.dsp.wire import frame

    radiales = [
        build_ray(
            moments={wire.MomentKind.UZ: [float(g) for g in range(8)]},
            az_start=float(i),
            az_end=float(i) + 1.0,
            ray_flags=(
                wire.RayFlag.VOLUME_START | wire.RayFlag.SWEEP_START
                if i == 0
                else wire.RayFlag.VOLUME_END
                if i == 3
                else 0
            ),
        )
        for i in range(4)
    ]

    async def escenario():
        receptor = MomentStreamReceiver()
        await receptor.start("127.0.0.1", 0)
        port = receptor._server.sockets[0].getsockname()[1]

        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        for cuerpo in radiales:
            writer.write(frame(wire.MsgType.MOMENT_RAY, cuerpo))
        # Un status por el mismo enlace: no es un radial y no puede romper nada.
        writer.write(frame(wire.MsgType.STATUS, wire.Status().pack()))
        await writer.drain()

        for _ in range(200):
            await asyncio.sleep(0.005)
            if receptor.radials_received == len(radiales) and (
                receptor.other_messages_received == 1
            ):
                break

        writer.close()
        await receptor.stop()
        return receptor

    receptor = asyncio.run(escenario())

    assert receptor.radials_received == len(radiales)
    assert receptor.other_messages_received == 1
    assert receptor.frame_errors == 0
    assert receptor.latest is not None
    assert receptor.latest.radial_status is RadialStatus.END_OF_VOLUME
    assert receptor.latest.moments[MomentId.UZ].values == [float(g) for g in range(8)]


def test_el_receptor_corta_ante_una_trama_invalida():
    """Un magic ajeno desincroniza el flujo: no se sigue leyendo."""
    import asyncio

    from adapters.dsp.moment_stream_receiver import MomentStreamReceiver

    async def escenario():
        receptor = MomentStreamReceiver()
        await receptor.start("127.0.0.1", 0)
        port = receptor._server.sockets[0].getsockname()[1]

        _, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(struct.pack("<IBBBBI", 0x4C4D4452, 0, 1, 1, 0, 36))
        writer.write(b"\x00" * 36)
        await writer.drain()

        for _ in range(200):
            await asyncio.sleep(0.005)
            if receptor.frame_errors:
                break

        writer.close()
        await receptor.stop()
        return receptor

    receptor = asyncio.run(escenario())
    assert receptor.frame_errors == 1
    assert receptor.radials_received == 0
