"""Pruebas para A4 Maintenance Unlock (/api/maintenance/*) y la evaluacion perezosa."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from adapters.dsp import MomentStreamReceiver
from adapters.gateway.app import create_app
from adapters.hal_sim import SimulatedHAL
from core.contracts.mmi import AccessLevel


@pytest.fixture
def client():
    hal = SimulatedHAL()
    dsp = MomentStreamReceiver()
    app = create_app(hal, dsp, dsp_bind_host="127.0.0.1", dsp_port=0)
    with TestClient(app) as test_client:
        yield test_client


def test_status_initial_maintenance(client: TestClient):
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert "maintenance" in data
    assert data["maintenance"]["level"] == AccessLevel.OP


def test_unlock_maintenance_wrong_password(client: TestClient):
    res = client.post(
        "/api/maintenance/unlock",
        json={"password": "wrongpassword", "actor": "tech", "duration_s": 60},
    )
    assert res.status_code == 403
    assert "incorrecta" in res.json()["detail"]


def test_unlock_maintenance_success(client: TestClient):
    res = client.post(
        "/api/maintenance/unlock",
        json={"password": "mant1234", "actor": "tecnico1", "duration_s": 300},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["level"] == AccessLevel.MANT
    assert data["actor"] == "tecnico1"
    assert data["expires_wall"] is not None

    status_res = client.get("/api/status")
    assert status_res.status_code == 200
    assert status_res.json()["maintenance"]["level"] == AccessLevel.MANT


def test_lock_maintenance(client: TestClient):
    client.post(
        "/api/maintenance/unlock",
        json={"password": "mant1234", "actor": "tecnico1", "duration_s": 300},
    )
    res = client.post("/api/maintenance/lock")
    assert res.status_code == 200
    assert res.json()["level"] == AccessLevel.OP

    status_res = client.get("/api/status")
    assert status_res.json()["maintenance"]["level"] == AccessLevel.OP


def test_maintenance_expiration_lazy_check(client: TestClient):
    # Forzar un estado MANT con expires_wall en el pasado
    client.post(
        "/api/maintenance/unlock",
        json={"password": "mant1234", "actor": "tecnico1", "duration_s": 10},
    )
    app = client.app
    past = datetime.now(timezone.utc) - timedelta(seconds=5)
    app.state.maintenance.expires_wall = past

    # Al pedir status, _effective_maintenance resetea a OP
    res = client.get("/api/status")
    assert res.status_code == 200
    assert res.json()["maintenance"]["level"] == AccessLevel.OP
