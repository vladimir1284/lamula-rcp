"""Pruebas para E11 Config Profiles (/api/config/profile/*)."""

import pytest
from fastapi.testclient import TestClient

from adapters.dsp import MomentStreamReceiver
from adapters.gateway.app import create_app
from adapters.hal_sim import SimulatedHAL


@pytest.fixture
def client(tmp_path):
    hal = SimulatedHAL()
    dsp = MomentStreamReceiver()
    profile_path = tmp_path / "config_profile.json"
    app = create_app(
        hal,
        dsp,
        dsp_bind_host="127.0.0.1",
        dsp_port=0,
        config_profile_path=profile_path,
    )
    with TestClient(app) as test_client:
        yield test_client


def test_config_profile_current_and_saved(client: TestClient):
    res_cur = client.get("/api/config/profile/current")
    assert res_cur.status_code == 200
    cur_data = res_cur.json()
    assert "antenna_step_config" in cur_data
    assert "thresholds" in cur_data

    res_sav = client.get("/api/config/profile/saved")
    assert res_sav.status_code == 200
    assert res_sav.json() == cur_data


def test_config_profile_set_and_restore(client: TestClient):
    cur_data = client.get("/api/config/profile/current").json()
    modified = cur_data.copy()
    modified["antenna_step_config"] = {"azimuth_step_deg": 0.5, "elevation_step_deg": 0.5}
    modified["thresholds"]["log_threshold_db"] = 2.5

    res_set = client.post("/api/config/profile/set", json=modified)
    assert res_set.status_code == 200
    updated = res_set.json()
    assert updated["antenna_step_config"]["azimuth_step_deg"] == 0.5
    assert updated["thresholds"]["log_threshold_db"] == 2.5

    # Restore debe volver al saved original
    res_res = client.post("/api/config/profile/restore")
    assert res_res.status_code == 200
    restored = res_res.json()
    assert restored["antenna_step_config"]["azimuth_step_deg"] == 1.0
    assert restored["thresholds"]["log_threshold_db"] == 1.0


def test_config_profile_save_and_factory(client: TestClient):
    cur_data = client.get("/api/config/profile/current").json()
    modified = cur_data.copy()
    modified["antenna_step_config"] = {"azimuth_step_deg": 0.2, "elevation_step_deg": 0.2}

    client.post("/api/config/profile/set", json=modified)
    res_save = client.post("/api/config/profile/save")
    assert res_save.status_code == 200
    assert res_save.json()["antenna_step_config"]["azimuth_step_deg"] == 0.2

    # Factory debe resetear a defaults
    res_fac = client.post("/api/config/profile/factory")
    assert res_fac.status_code == 200
    factory_data = res_fac.json()
    assert factory_data["antenna_step_config"]["azimuth_step_deg"] == 1.0

    # Restore ahora vuelve al saved modificado (0.2)
    res_res = client.post("/api/config/profile/restore")
    assert res_res.status_code == 200
    assert res_res.json()["antenna_step_config"]["azimuth_step_deg"] == 0.2
