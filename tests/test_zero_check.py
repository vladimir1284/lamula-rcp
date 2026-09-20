"""Pruebas para G5 Zero Check (rutina de control y /api/zero-check / /api/control/zero-check).
"""

import pytest
from fastapi.testclient import TestClient

from adapters.dsp import MomentStreamReceiver
from adapters.gateway.app import create_app
from core.contracts.common import SignalQuality
from core.contracts.control import RoutineOutcome
from core.contracts.hal import AntennaPosition, HardwareAbstractionLayer, SignalReading
from core.control_routines.zero_check import run_zero_check


class MockHAL(HardwareAbstractionLayer):
    def __init__(self, remote_ok: bool = True):
        self.remote_ok = remote_ok

    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    def is_connected(self) -> bool:
        return True

    async def read_digital(self, signal_id: str) -> SignalReading[bool]:
        return SignalReading(value=self.remote_ok, quality=SignalQuality.OK, at_us=0)

    async def read_analog(self, signal_id: str) -> SignalReading[float]:
        return SignalReading(value=0.0, quality=SignalQuality.OK, at_us=0)

    async def write_digital(self, signal_id: str, value: bool) -> None:
        pass

    async def write_analog(self, signal_id: str, value: float) -> None:
        pass

    async def read_antenna_position(self) -> AntennaPosition:
        return AntennaPosition(
            az_deg=0.0,
            el_deg=0.0,
            az_rate_deg_s=0.0,
            el_rate_deg_s=0.0,
            az_valid=True,
            el_valid=True,
            az_ref_ok=True,
            el_ref_ok=True,
            az_fault=False,
            el_fault=False,
            degraded=False,
            seq=1,
            at_us=0,
        )


@pytest.mark.anyio
async def test_run_zero_check_success():
    hal = MockHAL(remote_ok=True)
    res = await run_zero_check(hal)
    assert res.outcome == RoutineOutcome.SUCCESS
    assert res.routine == "zero_check"
    assert any("Noise High Channel" in step.detail for step in res.steps)
    assert any("Noise Low Channel" in step.detail for step in res.steps)


@pytest.mark.anyio
async def test_run_zero_check_failed_preconditions():
    hal = MockHAL(remote_ok=False)
    res = await run_zero_check(hal)
    assert res.outcome == RoutineOutcome.FAILED
    assert res.routine == "zero_check"


@pytest.fixture
def client(tmp_path):
    hal = MockHAL(remote_ok=True)
    dsp = MomentStreamReceiver()
    app = create_app(
        hal,
        dsp,
        dsp_bind_host="127.0.0.1",
        dsp_port=0,
        power_limits_path=tmp_path / "power_limits.json",
    )
    with TestClient(app) as test_client:
        yield test_client


def test_zero_check_snapshot_initial(client: TestClient):
    res = client.get("/api/zero-check")
    assert res.status_code == 200
    data = res.json()
    assert data["interval_s"] == 3600.0
    assert data["enabled"] is True
    assert data["last_run_at_wall"] is None
    assert data["noise_high_dbm"] is None
    assert data["noise_low_dbm"] is None


def test_zero_check_execution_requires_active_control(client: TestClient):
    # En modo passive por defecto -> 403
    res = client.post("/api/control/zero-check")
    assert res.status_code == 403


def test_zero_check_execution_flow(client: TestClient):
    # Activar control
    client.post("/api/control", json={"mode": "active", "actor": "test-op"})

    # Lanzar Zero Check
    res = client.post("/api/control/zero-check")
    assert res.status_code == 202
    job_accepted = res.json()
    assert job_accepted["routine"] == "zero_check"

    # Sondear job
    job_id = job_accepted["job_id"]
    job_res = client.get(f"/api/control/jobs/{job_id}")
    assert job_res.status_code == 200
    job_data = job_res.json()
    assert job_data["status"] == "done"
    assert job_data["result"]["outcome"] == "success"

    # Verificar que el snapshot se actualizo
    snap_res = client.get("/api/zero-check")
    assert snap_res.status_code == 200
    snap = snap_res.json()
    assert snap["last_run_at_wall"] is not None
    assert snap["noise_high_dbm"] == -105.2
    assert snap["noise_low_dbm"] == -102.8
