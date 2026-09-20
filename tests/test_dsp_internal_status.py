"""Pruebas para E12 DSP Internal Status (/api/dsp/internal-status y /api/dsp/reset-counters)."""

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
        yield test_client, dsp


def test_get_dsp_internal_status(client):
    test_client, _ = client
    res = test_client.get("/api/dsp/internal-status")
    assert res.status_code == 200
    data = res.json()

    assert "connected" in data
    assert "uptime_s" in data
    assert "severity" in data
    assert "last_error" in data
    assert "n_rx_channels" in data
    assert "capability_flags" in data
    assert "bite_flags" in data
    assert "rays_in" in data
    assert "rays_out" in data
    assert "rays_dropped" in data
    assert "noise_floor_dbm" in data
    assert len(data["noise_floor_dbm"]) == 4
    assert "dc_offset_i" in data
    assert len(data["dc_offset_i"]) == 4
    assert "dc_offset_q" in data
    assert len(data["dc_offset_q"]) == 4
    assert "n_gates" in data
    assert "n_pulses" in data
    assert "prf_hz" in data
    assert "gate_spacing_m" in data


def test_post_dsp_reset_counters(client):
    test_client, dsp = client
    dsp.radials_received = 150
    assert dsp.radials_received == 150

    res = test_client.post("/api/dsp/reset-counters")
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "ok"
    assert "message" in data
    assert dsp.radials_received == 0
