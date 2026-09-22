"""Pruebas para G2 TX Sampling Adjust (/api/tx-sampling-adjust*).

Verifica lecturas HAL (normal y degradado a None si no hay conexion sin error 500)
y el ciclo Set/Save de parametros.
"""

import pytest
from fastapi.testclient import TestClient

from adapters.dsp import MomentStreamReceiver
from adapters.gateway.app import create_app
from adapters.hal_sim import SimulatedHAL


@pytest.fixture
def client(tmp_path):
    hal = SimulatedHAL()
    dsp = MomentStreamReceiver()
    app = create_app(
        hal,
        dsp,
        dsp_bind_host="127.0.0.1",
        dsp_port=0,
        tx_sampling_path=tmp_path / "tx_sampling_adjust.json",
    )
    with TestClient(app) as test_client:
        yield test_client


def test_tx_sampling_adjust_without_hal_connection(client: TestClient):
    res = client.get("/api/tx-sampling-adjust")
    assert res.status_code == 200
    data = res.json()
    assert "params" in data
    assert data["tx_start_sample_read"] is None
    assert data["tx_stop_sample_read"] is None
    assert data["tx_sample_read"] is None
    assert data["tx_frequency_read"] is None
    assert data["commanded_lo_freq_read"] is None
    assert data["bus_ok"] is False


from unittest.mock import AsyncMock
from core.contracts.common import SignalQuality
from core.contracts.hal import SignalReading


def test_tx_sampling_adjust_with_mocked_hal(tmp_path):
    hal = SimulatedHAL()
    hal.is_connected = lambda: True
    hal.read_analog = AsyncMock(return_value=SignalReading(value=10.0, quality=SignalQuality.OK, at_us=0))
    dsp = MomentStreamReceiver()
    app = create_app(
        hal,
        dsp,
        dsp_bind_host="127.0.0.1",
        dsp_port=0,
        tx_sampling_path=tmp_path / "tx_sampling_adjust.json",
    )
    with TestClient(app) as test_client:
        res = test_client.get("/api/tx-sampling-adjust")
        assert res.status_code == 200
        data = res.json()
        assert data["tx_start_sample_read"] == 10.0
        assert data["tx_stop_sample_read"] == 10.0
        assert data["tx_sample_read"] == 10.0
        assert data["tx_frequency_read"] == 10.0
        assert data["commanded_lo_freq_read"] == 10.0
        assert data["bus_ok"] is True


def test_tx_sampling_adjust_set_and_save(client: TestClient):
    new_params = {
        "tx_start_sample": 12.0,
        "tx_stop_sample": 55.0,
        "tx_sample": 32.0,
        "tx_frequency": 30.5,
        "commanded_lo_freq": 5605.0,
    }
    res_set = client.post("/api/tx-sampling-adjust", json=new_params)
    assert res_set.status_code == 200
    assert res_set.json() == new_params

    # Verify set parameters in GET
    snap = client.get("/api/tx-sampling-adjust").json()
    assert snap["params"] == new_params

    # Save parameters
    res_save = client.post("/api/tx-sampling-adjust/save")
    assert res_save.status_code == 200
    assert res_save.json() == new_params
