"""Pruebas para G7 Radar Constant Parameters (/api/radar-constant*).
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from adapters.dsp import MomentStreamReceiver
from adapters.gateway.app import create_app
from adapters.hal_sim import SimulatedHAL


@pytest.fixture
def client(tmp_path: Path):
    hal = SimulatedHAL()
    dsp = MomentStreamReceiver()
    save_path = tmp_path / "radar_constant.json"
    app = create_app(
        hal,
        dsp,
        dsp_bind_host="127.0.0.1",
        dsp_port=0,
        radar_constant_path=save_path,
    )
    with TestClient(app) as test_client:
        yield test_client


def test_get_radar_constant_defaults(client: TestClient):
    res = client.get("/api/radar-constant")
    assert res.status_code == 200
    data = res.json()
    assert "params" in data
    assert "radar_constant_db" in data
    assert data["params"]["antenna_gain_db"] == 45.0
    assert isinstance(data["radar_constant_db"], float)


def test_set_radar_constant_volatile(client: TestClient):
    get_res = client.get("/api/radar-constant").json()
    params = get_res["params"]
    initial_db = get_res["radar_constant_db"]

    params["antenna_gain_db"] = 48.0
    res = client.post("/api/radar-constant", json=params)
    assert res.status_code == 200
    updated = res.json()
    assert updated["params"]["antenna_gain_db"] == 48.0
    assert updated["radar_constant_db"] > initial_db

    # GET refleja la modificación volátil
    snap = client.get("/api/radar-constant").json()
    assert snap["params"]["antenna_gain_db"] == 48.0


def test_save_radar_constant_persists(client: TestClient):
    get_res = client.get("/api/radar-constant").json()
    params = get_res["params"]
    params["tx_losses_db"] = 2.0

    client.post("/api/radar-constant", json=params)
    res = client.post("/api/radar-constant/save")
    assert res.status_code == 200
    saved = res.json()
    assert saved["params"]["tx_losses_db"] == 2.0

    # Verificar que se registró en calibration-log
    log_res = client.get("/api/calibration-log")
    assert log_res.status_code == 200
    logs = log_res.json()
    assert len(logs) >= 1
    assert any(l["procedure"] == "Radar Constant Parameters" for l in logs)
