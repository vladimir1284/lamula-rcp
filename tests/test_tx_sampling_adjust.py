"""Pruebas para G2 TX Sampling Adjust (/api/tx-sampling-adjust*).

Cubre los tres estados requeridos:
1. ok: HAL conectado respondiendo lecturas analógicas válidas, Set y Save funcionan correctamente.
2. stale: HAL desconectado o fallando en lectura analógica degrada lecturas a None sin responder HTTP 500.
3. error de guardado: POST /api/tx-sampling-adjust/save devuelve 409 cuando no hay parámetros puestos
   o cuando el radar está radiando.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from adapters.dsp import MomentStreamReceiver
from adapters.gateway.app import create_app
from adapters.hal_sim import SimulatedHAL
from core.contracts.common import MonotonicMicros, SignalQuality
from core.contracts.hal import SignalReading


@pytest.fixture
def client_app(tmp_path):
    hal = SimulatedHAL()
    dsp = MomentStreamReceiver()
    app = create_app(
        hal,
        dsp,
        dsp_bind_host="127.0.0.1",
        dsp_port=0,
        scan_worksheet_path=tmp_path / "scan_worksheet.json",
        power_limits_path=tmp_path / "power_limits.json",
        config_profile_path=tmp_path / "config_profile.json",
        tx_sampling_adjust_path=tmp_path / "tx_sampling_adjust.json",
    )
    with TestClient(app) as test_client:
        yield test_client, app, hal


def test_tx_sampling_adjust_stale_without_hal(client_app):
    client, app, hal = client_app
    # Sin HAL conectado / excepción en read_analog
    res = client.get("/api/tx-sampling-adjust")
    assert res.status_code == 200
    data = res.json()
    assert data["tx_sample_readout"] is None
    assert data["tx_frequency_readout_mhz"] is None
    assert data["commanded_lo_freq_readout_mhz"] is None
    assert data["tx_start_sample_readout"] is None
    assert data["tx_stop_sample_readout"] is None
    assert data["bus_ok"] is False
    assert data["radiating"] is False
    assert data["params"] is None


def test_tx_sampling_adjust_ok_with_hal(client_app):
    client, app, hal = client_app

    def mock_read_analog(sig: str):
        mapping = {
            "tx.tx_sample": 128.0,
            "tx.tx_frequency": 2800.0,
            "tx.commanded_lo_freq": 2770.0,
            "tx.tx_start_sample": 32.0,
            "tx.tx_stop_sample": 256.0,
        }
        val = mapping.get(sig, 0.0)
        return SignalReading(value=val, quality=SignalQuality.OK, at_us=MonotonicMicros(1000))

    with patch.object(hal, "is_connected", return_value=True), patch.object(
        hal, "read_analog", side_effect=mock_read_analog
    ):
        res = client.get("/api/tx-sampling-adjust")
        assert res.status_code == 200
        data = res.json()
        assert data["tx_sample_readout"] == 128.0
        assert data["tx_frequency_readout_mhz"] == 2800.0
        assert data["commanded_lo_freq_readout_mhz"] == 2770.0
        assert data["tx_start_sample_readout"] == 32.0
        assert data["tx_stop_sample_readout"] == 256.0
        assert data["bus_ok"] is True


def test_tx_sampling_adjust_set_and_save_success(client_app):
    client, app, hal = client_app
    params = {
        "tx_sample": 128.0,
        "tx_frequency_mhz": 2800.0,
        "commanded_lo_freq_mhz": 2770.0,
        "tx_start_sample": 32.0,
        "tx_stop_sample": 256.0,
    }

    # Set (Volátil)
    res_set = client.post("/api/tx-sampling-adjust", json=params)
    assert res_set.status_code == 200
    assert res_set.json() == params

    snap = client.get("/api/tx-sampling-adjust").json()
    assert snap["params"] == params

    # Save (Persistente)
    res_save = client.post("/api/tx-sampling-adjust/save")
    assert res_save.status_code == 200
    assert res_save.json() == params

    # Verificar que se registró en calibration-log
    log_res = client.get("/api/calibration-log")
    assert log_res.status_code == 200
    logs = log_res.json()
    assert len(logs) >= 1
    assert any(l["procedure"] == "TX Sampling Adjust" for l in logs)


def test_tx_sampling_adjust_save_errors(client_app):
    client, app, hal = client_app

    # Error 1: Guardar cuando no hay parámetros configurados (params is None)
    res_save_no_params = client.post("/api/tx-sampling-adjust/save")
    assert res_save_no_params.status_code == 409
    assert "no hay parametros" in res_save_no_params.json()["detail"]

    # Configurar parámetros vía Set
    params = {
        "tx_sample": 128.0,
        "tx_frequency_mhz": 2800.0,
        "commanded_lo_freq_mhz": 2770.0,
        "tx_start_sample": 32.0,
        "tx_stop_sample": 256.0,
    }
    client.post("/api/tx-sampling-adjust", json=params)

    # Error 2: Guardar cuando el radar está radiando
    radiating_reading = SignalReading(value=True, quality=SignalQuality.OK, at_us=MonotonicMicros(1000))
    with patch.object(hal, "read_digital", new_callable=AsyncMock, return_value=radiating_reading):
        res_save_radiating = client.post("/api/tx-sampling-adjust/save")
        assert res_save_radiating.status_code == 409
        assert "radiando" in res_save_radiating.json()["detail"]
