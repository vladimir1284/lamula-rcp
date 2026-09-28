"""Pruebas para A7 System Information (/api/system-info)."""

import tomllib
from pathlib import Path

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
    # Contra el pin, no contra literales: re-vendorizar el contrato del DSP es
    # un evento esperado y frecuente, y hasta v1.3 cada uno rompía este test
    # por un motivo que no era un fallo. Lo que sí tiene que seguir cierto es
    # que el endpoint publique exactamente lo que dice `UPSTREAM.toml`.
    pin = tomllib.loads(
        (Path(__file__).resolve().parents[1] / "contract" / "vendor" / "UPSTREAM.toml").read_text(
            encoding="utf-8"
        )
    )
    version = pin["contract"]
    assert (
        data["dsp_contract_version"]
        == f"v{version['version_major']}.{version['version_minor']}"
    )
    assert data["dsp_contract_commit"] == pin["upstream"]["commit"]
    assert data["dsp_contract_commit_date"] == pin["upstream"]["commit_date"]
