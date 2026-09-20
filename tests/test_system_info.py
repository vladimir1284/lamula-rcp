"""Pruebas para A7 System Information (/api/system-info)."""

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


def test_system_info_endpoint(client: TestClient):
    res = client.get("/api/system-info")
    assert res.status_code == 200
    data = res.json()
    assert "rcp_version" in data
    assert "dsp_contract_version" in data
    assert "dsp_contract_commit" in data
    assert "dsp_contract_commit_date" in data
    assert "connected_clients" in data
    assert data["dsp_contract_version"] == "v1.3"
    assert data["dsp_contract_commit"] == "6a09656"
