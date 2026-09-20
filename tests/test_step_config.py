"""Pruebas para C2 Antenna Step Control Setup (/api/antenna/step-config)."""

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


def test_step_config_get_default(client: TestClient):
    res = client.get("/api/antenna/step-config")
    assert res.status_code == 200
    data = res.json()
    assert data["azimuth_step_deg"] == 1.0
    assert data["elevation_step_deg"] == 1.0


def test_step_config_post_valid(client: TestClient):
    res = client.post("/api/antenna/step-config", json={"azimuth_step_deg": 0.5, "elevation_step_deg": 0.2})
    assert res.status_code == 200
    data = res.json()
    assert data["azimuth_step_deg"] == 0.5
    assert data["elevation_step_deg"] == 0.2

    # Verificar que persiste en GET
    res_get = client.get("/api/antenna/step-config")
    assert res_get.status_code == 200
    assert res_get.json() == {"azimuth_step_deg": 0.5, "elevation_step_deg": 0.2}


def test_step_config_post_invalid_bounds(client: TestClient):
    # Menor a 0.1
    res1 = client.post("/api/antenna/step-config", json={"azimuth_step_deg": 0.05, "elevation_step_deg": 0.5})
    assert res1.status_code == 422

    # Mayor a 1.0
    res2 = client.post("/api/antenna/step-config", json={"azimuth_step_deg": 0.5, "elevation_step_deg": 1.5})
    assert res2.status_code == 422
