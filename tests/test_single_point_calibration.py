"""Pruebas unitarias e integración para G4 — Single Point Calibration."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from adapters.dsp import MomentStreamReceiver
from adapters.gateway.app import create_app
from core.contracts.common import SignalQuality
from core.contracts.control import RoutineName, RoutineOutcome
from core.contracts.hal import AntennaPosition, HardwareAbstractionLayer, SignalReading
from core.control_routines import run_single_point_calibration


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


@pytest.mark.anyio
async def test_single_point_calibration_routine_auto():
    hal = MockHAL(remote_ok=True)
    res = await run_single_point_calibration(hal, mode="auto")
    assert res.routine == RoutineName.SINGLE_POINT_CALIBRATION
    assert res.outcome == RoutineOutcome.SUCCESS
    assert len(res.steps) >= 3


@pytest.mark.anyio
async def test_single_point_calibration_routine_external():
    hal = MockHAL(remote_ok=True)

    async def mock_input():
        return {"injected_power_dbm": -25.0, "measured_radar_constant_db": 69.1}

    res = await run_single_point_calibration(
        hal,
        mode="external",
        step_input_func=mock_input,
    )
    assert res.routine == RoutineName.SINGLE_POINT_CALIBRATION
    assert res.outcome == RoutineOutcome.SUCCESS
    injected_step = next(s for s in res.steps if s.signal_id == "rx.single_point_injected_power")
    assert "-25.00 dBm" in injected_step.detail


def test_single_point_calibration_endpoint_permissions(client: TestClient):
    # Sin MANT debe fallar con 403
    res = client.post("/api/control/single-point-calibration", json={"mode": "auto"})
    assert res.status_code == 403

    # Desbloquear MANT pero sin tomar control
    client.post("/api/maintenance/unlock", json={"password": "mant1234", "actor": "tester", "duration_s": 300})
    client.post("/api/control", json={"mode": "passive", "actor": "tester"})
    res = client.post("/api/control/single-point-calibration", json={"mode": "auto"})
    assert res.status_code == 403

    # Tomar control activo
    client.post("/api/control", json={"mode": "active", "actor": "tester"})
    res = client.post("/api/control/single-point-calibration", json={"mode": "auto"})
    assert res.status_code == 202
    data = res.json()
    assert data["status"] == "running"


def test_single_point_calibration_endpoint_auto_workflow(client: TestClient):
    client.post("/api/maintenance/unlock", json={"password": "mant1234", "actor": "tester", "duration_s": 300})
    client.post("/api/control", json={"mode": "active", "actor": "tester"})

    res = client.post("/api/control/single-point-calibration", json={"mode": "auto"})
    assert res.status_code == 202
    job_id = res.json()["job_id"]

    for _ in range(20):
        job_res = client.get(f"/api/control/jobs/{job_id}")
        assert job_res.status_code == 200
        status_data = job_res.json()
        if status_data["status"] == "done":
            break
        time.sleep(0.05)

    assert status_data["status"] == "done"
    assert status_data["result"]["outcome"] == "success"

    # Verificar log de calibración G8
    log_res = client.get("/api/calibration-log")
    assert log_res.status_code == 200
    logs = log_res.json()
    assert any("Single Point Calibration" in l["procedure"] for l in logs)


def test_single_point_calibration_endpoint_external_workflow(client: TestClient):
    client.post("/api/maintenance/unlock", json={"password": "mant1234", "actor": "tester", "duration_s": 300})
    client.post("/api/control", json={"mode": "active", "actor": "tester"})

    res = client.post("/api/control/single-point-calibration", json={"mode": "external"})
    assert res.status_code == 202
    job_id = res.json()["job_id"]

    job_data = None
    for _ in range(20):
        job_res = client.get(f"/api/control/jobs/{job_id}")
        job_data = job_res.json()
        if job_data["status"] == "awaiting_operator_input":
            break
        time.sleep(0.05)

    assert job_data["status"] == "awaiting_operator_input"
    assert job_data["current_step"] == 2

    # Enviar paso 2 (potencia inyectada)
    step_res = client.post(f"/api/control/jobs/{job_id}/step", json={"data": {"injected_power_dbm": -28.5}})
    assert step_res.status_code == 200

    # Esperar a paso 3
    for _ in range(20):
        job_res = client.get(f"/api/control/jobs/{job_id}")
        job_data = job_res.json()
        if job_data["status"] == "awaiting_operator_input" and job_data["current_step"] == 3:
            break
        time.sleep(0.05)

    assert job_data["status"] == "awaiting_operator_input"
    assert job_data["current_step"] == 3

    # Enviar paso 3 (constante de radar)
    step_res = client.post(f"/api/control/jobs/{job_id}/step", json={"data": {"measured_radar_constant_db": 68.8}})
    assert step_res.status_code == 200

    # Esperar finalización
    for _ in range(20):
        job_res = client.get(f"/api/control/jobs/{job_id}")
        job_data = job_res.json()
        if job_data["status"] == "done":
            break
        time.sleep(0.05)

    assert job_data["status"] == "done"
    assert job_data["result"]["outcome"] == "success"
