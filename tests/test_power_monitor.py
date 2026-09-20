"""Pruebas para B7 Power Monitor (/api/power-monitor*).

Sin radar_emulator corriendo, SimulatedHAL no se conecta (lifespan lo absorbe,
ver adapters/gateway/app.py) -- forward/reverse quedan en None y bus_ok/
radiating en False. Es el mismo escenario "sin lecturas" que un bus caído en
campo, asi que estas pruebas cubren exactamente eso mas el ciclo Set/Save.
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
        scan_worksheet_path=tmp_path / "scan_worksheet.json",
        power_limits_path=tmp_path / "power_limits.json",
    )
    with TestClient(app) as test_client:
        yield test_client


def test_power_monitor_without_hal_connection(client: TestClient):
    res = client.get("/api/power-monitor")
    assert res.status_code == 200
    data = res.json()
    assert data["forward_power_kw"] is None
    assert data["reverse_power_kw"] is None
    assert data["vswr"] is None
    assert data["bus_ok"] is False
    assert data["radiating"] is False
    assert data["limits"] is None


def test_power_limits_set_is_volatile(client: TestClient):
    limits = {"forward_limit_kw": 220.0, "reverse_limit_kw": 10.0, "vswr_limit": 1.5}
    res = client.post("/api/power-monitor/limits", json=limits)
    assert res.status_code == 200
    assert res.json() == limits

    # Set queda reflejado en el snapshot, pero no se persistio a disco todavia.
    snap = client.get("/api/power-monitor").json()
    assert snap["limits"] == limits


def test_power_limits_save_requires_set_first(client: TestClient):
    res = client.post("/api/power-monitor/limits/save")
    assert res.status_code == 409


def test_power_limits_save_persists(client: TestClient):
    limits = {"forward_limit_kw": 220.0, "reverse_limit_kw": 10.0, "vswr_limit": 1.5}
    client.post("/api/power-monitor/limits", json=limits)
    res = client.post("/api/power-monitor/limits/save")
    assert res.status_code == 200
    assert res.json() == limits
