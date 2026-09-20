"""Pruebas para B4 State Trend Plot (/api/trend/*)."""

import pytest
from fastapi.testclient import TestClient

from adapters.dsp import MomentStreamReceiver
from adapters.gateway.app import create_app
from adapters.hal_sim import SimulatedHAL


@pytest.fixture
def client():
    hal = SimulatedHAL()
    dsp = MomentStreamReceiver()
    app = create_app(hal, dsp, dsp_bind_host="127.0.0.1", dsp_port=0)
    with TestClient(app) as test_client:
        yield test_client


def test_trend_channels(client: TestClient):
    res = client.get("/api/trend/channels")
    assert res.status_code == 200
    channels = res.json()
    assert isinstance(channels, list)
    assert "tx.mps_output_voltage_sample" in channels
    assert "ant.az_motor_current_sample" in channels


def test_trend_lifecycle(client: TestClient):
    # Initial status
    st_res = client.get("/api/trend/status")
    assert st_res.status_code == 200
    st = st_res.json()
    assert st["running"] is False
    assert st["signal_ids"] == []

    # Start trend
    start_res = client.post(
        "/api/trend/start", json={"signal_ids": ["tx.mps_output_voltage_sample", "tx.fps_output_voltage_sample"]}
    )
    assert start_res.status_code == 200
    start_st = start_res.json()
    assert start_st["running"] is True
    assert start_st["signal_ids"] == ["tx.mps_output_voltage_sample", "tx.fps_output_voltage_sample"]

    # Starting again while running returns 409 Conflict
    conflict_res = client.post("/api/trend/start", json={"signal_ids": ["tx.mps_output_voltage_sample"]})
    assert conflict_res.status_code == 409

    # Check trend data
    data_res = client.get("/api/trend/data")
    assert data_res.status_code == 200
    data = data_res.json()
    assert len(data) == 2
    assert data[0]["signal_id"] in ["tx.mps_output_voltage_sample", "tx.fps_output_voltage_sample"]

    # Stop trend
    stop_res = client.post("/api/trend/stop")
    assert stop_res.status_code == 200
    assert stop_res.json()["running"] is False

    # Continue trend
    cont_res = client.post("/api/trend/continue")
    assert cont_res.status_code == 200
    assert cont_res.json()["running"] is True

    # Clear trend
    clear_res = client.post("/api/trend/clear")
    assert clear_res.status_code == 200
    clear_st = clear_res.json()
    assert clear_st["running"] is False
    assert clear_st["signal_ids"] == []

    # Data empty after clear
    data_after_clear = client.get("/api/trend/data").json()
    assert data_after_clear == []
