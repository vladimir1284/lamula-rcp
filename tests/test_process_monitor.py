"""Pruebas para B5 RCP Process Monitor (/api/process-monitor)."""

import os
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


def test_process_monitor_endpoint(client: TestClient):
    res = client.get("/api/process-monitor")
    assert res.status_code == 200
    data = res.json()

    assert "process" in data
    assert "tasks" in data

    proc = data["process"]
    assert proc["pid"] == os.getpid()
    assert isinstance(proc["name"], str)
    assert isinstance(proc["priority"], int)
    assert isinstance(proc["status"], str)
    assert isinstance(proc["cpu_percent"], (int, float))
    assert isinstance(proc["memory_mb"], (int, float))

    tasks = data["tasks"]
    assert isinstance(tasks, list)
    assert len(tasks) > 0
    for t in tasks:
        assert "name" in t
        assert t["state"] in ("pending", "done", "cancelled")
