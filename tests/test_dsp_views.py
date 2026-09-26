"""Pruebas para las vistas E4 (clutter-filters), E6 (trigger-setup-pw), E2 (processing-options) y E7 (burst-afc)."""

import pytest
from contract.vendor import dsp_rcp_v0_1 as wire
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


def test_trigger_setup_general_get(client):
    res = client.get("/api/dsp/trigger-setup-general")
    assert res.status_code == 200
    data = res.json()
    assert "triggers" in data
    assert len(data["triggers"]) == 4
    for idx, name in enumerate(["Trig 1 (Tx)", "Trig 2 (Rx)", "Trig 3 (Aux)", "Trig 4 (Spare)"], start=1):
        trig = data["triggers"][idx - 1]
        assert trig["trigger_index"] == idx
        assert trig["name"] == name
        assert "start_us" in trig
        assert "width_us" in trig


def test_clutter_filters_get_and_set(client):
    res = client.get("/api/dsp/clutter-filters")
    assert res.status_code == 200
    data = res.json()
    assert "clutter_filter" in data
    assert "clutter_width_ms" in data

    payload = {
        "clutter_filter": "notch",
        "clutter_width_ms": 2.5,
        "fixed_win": 1,
        "fixed_width_pts": 6,
        "fixed_edge_pts": 3,
        "variable_hunt_pts": 4,
        "secondary_sqi_slope": 0.1,
        "secondary_sqi_offset": 0.05,
    }
    post_res = client.post("/api/dsp/clutter-filters", json=payload)
    assert post_res.status_code == 200
    updated = post_res.json()
    assert updated["clutter_filter"] == "notch"
    assert updated["clutter_width_ms"] == 2.5


def test_trigger_setup_pw_get_and_set(client):
    res = client.get("/api/dsp/trigger-setup-pw")
    assert res.status_code == 200
    data = res.json()
    assert "selected_pulse_width" in data
    assert "gate_spacing_m" in data
    assert "triggers" in data
    assert len(data["triggers"]) == 4

    payload = {
        "selected_pulse_width": "short",
        "gate_spacing_m": 75.0,
        "prf_hz": 1200.0,
        "external_pretrigger_delay_us": 0.5,
        "current_noise_level_dbm": -108.0,
        "powerup_noise_level_dbm": -110.0,
        "triggers": data["triggers"],
    }
    post_res = client.post("/api/dsp/trigger-setup-pw", json=payload)
    assert post_res.status_code == 200
    updated = post_res.json()
    assert updated["selected_pulse_width"] == "short"
    assert updated["gate_spacing_m"] == 75.0


def test_processing_options_get_and_set(client):
    res = client.get("/api/dsp/processing-options")
    assert res.status_code == 200
    data = res.json()
    assert "r2_processing" in data
    assert "phidp_offset_deg" in data

    payload = {
        "spectral_window": "rect",
        "r2_processing": "always",
        "clutter_microsuppression": "user",
        "ppp_autocorrels": "never",
        "unfold_velocity": "user",
        "process_custom_trigs": "never",
        "interference_filter": "alg1",
        "phidp_offset_deg": 12.5,
    }
    post_res = client.post("/api/dsp/processing-options", json=payload)
    assert post_res.status_code == 200
    updated = post_res.json()
    assert updated["r2_processing"] == "always"
    assert updated["phidp_offset_deg"] == 12.5


def test_burst_afc_get_and_set(client):
    res = client.get("/api/dsp/burst-afc")
    assert res.status_code == 200
    data = res.json()
    assert data["tx_if_mhz"] == 30.0
    assert data["afc_enabled"] is True
    assert data["phase_lock_burst"] == "never"

    payload = dict(data)
    payload["tx_if_mhz"] = 60.0
    payload["phase_lock_burst"] = "always"
    payload["enable_burst_tracking"] = "user"
    payload["min_burst_power_dbm"] = -15.5

    post_res = client.post("/api/dsp/burst-afc", json=payload)
    assert post_res.status_code == 200
    updated = post_res.json()
    assert updated["tx_if_mhz"] == 60.0
    assert updated["phase_lock_burst"] == "always"
    assert updated["enable_burst_tracking"] == "user"
    assert updated["min_burst_power_dbm"] == -15.5

    get_again = client.get("/api/dsp/burst-afc")
    assert get_again.status_code == 200
    assert get_again.json() == updated


def test_spectrum_get_and_request(client):
    res_initial = client.get("/api/dsp/spectrum")
    assert res_initial.status_code == 200
    assert res_initial.json()["has_data"] is False

    dsp = client.app.state.dsp
    dsp._latest_spectrum = (64, 0, 101, 1700000000000000000, 0.0, 0.0, -10.0, [-30.0] * 64)

    res_data = client.get("/api/dsp/spectrum")
    assert res_data.status_code == 200
    body = res_data.json()
    assert body["has_data"] is True
    assert body["channel"] == 0
    assert body["seq"] == 101
    assert body["ref_level_dbm"] == -10.0
    assert len(body["bins"]) == 64

    # Request spectrum requires MANT mode
    res_req_forbidden = client.post("/api/dsp/request-spectrum")
    assert res_req_forbidden.status_code == 403

    unlock_res = client.post(
        "/api/maintenance/unlock",
        json={"password": "mant1234", "actor": "tester", "duration_s": 3600},
    )
    assert unlock_res.status_code == 200

    class DummyWriter:
        def __init__(self):
            self.data = b""

        def write(self, data: bytes):
            self.data += data

        async def drain(self):
            pass

    dummy_writer = DummyWriter()
    dsp._writer = dummy_writer

    res_req_ok = client.post("/api/dsp/request-spectrum")
    assert res_req_ok.status_code == 200
    assert res_req_ok.json()["status"] == "ok"
    assert len(dummy_writer.data) > 0


def test_set_endpoints_cannot_override_real_dsp_fields(client):
    """`clutter_width_ms`/`gate_spacing_m`/`prf_hz`/`phidp_offset_deg` llegan de
    `dsp.latest_config` (telemetria del DSP, sin path de escritura RCP->DSP hoy,
    ver docs/diseno/pendientes-p1.md). Un POST con un valor distinto no debe
    poder "guardar" un valor que despues un GET desmentiria."""
    dsp = client.app.state.dsp
    dsp._latest_config = wire.Config(clutter_filter=1, gate_spacing_m=150.0, prf_hz=1000.0, clutter_width_ms=1.0, phidp_offset_deg=0.0)

    clutter_payload = {
        "clutter_filter": "notch",
        "clutter_width_ms": 20.0,
        "fixed_win": 0,
        "fixed_width_pts": 5,
        "fixed_edge_pts": 2,
        "variable_hunt_pts": 3,
        "secondary_sqi_slope": 0.0,
        "secondary_sqi_offset": 0.0,
    }
    res = client.post("/api/dsp/clutter-filters", json=clutter_payload)
    assert res.status_code == 200
    body = res.json()
    assert body["clutter_filter"] == "gmap"
    assert body["clutter_width_ms"] == 1.0
    assert client.get("/api/dsp/clutter-filters").json() == body

    trigger_payload = {
        "selected_pulse_width": "short",
        "gate_spacing_m": 999.0,
        "prf_hz": 9999.0,
        "external_pretrigger_delay_us": 0.0,
        "current_noise_level_dbm": -110.0,
        "powerup_noise_level_dbm": -112.0,
        "triggers": [],
    }
    res = client.post("/api/dsp/trigger-setup-pw", json=trigger_payload)
    assert res.status_code == 200
    body = res.json()
    assert body["gate_spacing_m"] == 150.0
    assert body["prf_hz"] == 1000.0
    assert client.get("/api/dsp/trigger-setup-pw").json() == body

    processing_payload = {
        "spectral_window": "rect",
        "r2_processing": "always",
        "clutter_microsuppression": "user",
        "ppp_autocorrels": "never",
        "unfold_velocity": "user",
        "process_custom_trigs": "never",
        "interference_filter": "alg1",
        "phidp_offset_deg": 42.0,
    }
    res = client.post("/api/dsp/processing-options", json=processing_payload)
    assert res.status_code == 200
    body = res.json()
    assert body["phidp_offset_deg"] == 0.0
    assert client.get("/api/dsp/processing-options").json() == body
