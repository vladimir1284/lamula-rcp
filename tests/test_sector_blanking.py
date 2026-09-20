"""Pruebas para C5 Sector Blanking Editor (/api/sector-blanking*).
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from adapters.dsp import MomentStreamReceiver
from adapters.gateway.app import create_app
from adapters.hal_sim import SimulatedHAL


@pytest.fixture
def temp_sector_path(tmp_path: Path) -> Path:
    return tmp_path / "sector_blanking.json"


@pytest.fixture
def client(temp_sector_path: Path):
    hal = SimulatedHAL()
    dsp = MomentStreamReceiver()
    app = create_app(
        hal,
        dsp,
        dsp_bind_host="127.0.0.1",
        dsp_port=0,
        sector_blanking_path=temp_sector_path,
    )
    with TestClient(app) as test_client:
        yield test_client


def test_get_sector_blanking_default(client: TestClient):
    res = client.get("/api/sector-blanking")
    assert res.status_code == 200
    data = res.json()
    assert data["enabled"] is False
    assert len(data["sectors"]) == 8
    for sec in data["sectors"]:
        assert sec["in_use"] is False
        assert sec["az_start_deg"] == 0.0
        assert sec["az_end_deg"] == 0.0


def test_set_and_save_sector_blanking(client: TestClient, temp_sector_path: Path):
    # Fetch default profile
    profile = client.get("/api/sector-blanking").json()
    profile["enabled"] = True
    profile["sectors"][0]["in_use"] = True
    profile["sectors"][0]["az_start_deg"] = 10.0
    profile["sectors"][0]["az_end_deg"] = 45.0
    profile["sectors"][0]["el_start_deg"] = -10.0
    profile["sectors"][0]["el_end_deg"] = 30.0

    # Set profile (volatile in memory)
    res_set = client.post("/api/sector-blanking/set", json=profile)
    assert res_set.status_code == 200
    assert res_set.json()["enabled"] is True
    assert res_set.json()["sectors"][0]["in_use"] is True

    # Check GET reflects set profile
    res_get = client.get("/api/sector-blanking").json()
    assert res_get["enabled"] is True
    assert res_get["sectors"][0]["az_start_deg"] == 10.0

    # File should not exist before save
    assert not temp_sector_path.exists()

    # Save profile
    res_save = client.post("/api/sector-blanking/save")
    assert res_save.status_code == 200
    assert temp_sector_path.exists()

    # Re-initialize app to verify persistence across restarts
    hal = SimulatedHAL()
    dsp = MomentStreamReceiver()
    app2 = create_app(
        hal,
        dsp,
        dsp_bind_host="127.0.0.1",
        dsp_port=0,
        sector_blanking_path=temp_sector_path,
    )
    with TestClient(app2) as client2:
        reloaded = client2.get("/api/sector-blanking").json()
        assert reloaded["enabled"] is True
        assert reloaded["sectors"][0]["az_start_deg"] == 10.0
