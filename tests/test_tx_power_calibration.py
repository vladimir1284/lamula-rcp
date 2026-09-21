"""Pruebas para G3 TX Power Calibration (rutina de control, endpoints y wizard).
"""

import asyncio
import time
import pytest
from fastapi.testclient import TestClient

from adapters.dsp import MomentStreamReceiver
from adapters.gateway.app import create_app
from core.contracts.common import SignalQuality
from core.contracts.control import RoutineOutcome
from core.contracts.hal import AntennaPosition, HardwareAbstractionLayer, SignalReading
from core.contracts.mmi import CalibrationLogEntry
from core.control_routines.tx_power_calibration import run_tx_power_calibration


class MockHAL(HardwareAbstractionLayer):
    def __init__(self, remote_ok: bool = True, radiating: bool = True):
        self.remote_ok = remote_ok
        self.radiating = radiating

    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    def is_connected(self) -> bool:
        return True

    async def read_digital(self, signal_id: str) -> SignalReading[bool]:
        if signal_id == "tx.radiating_status":
            return SignalReading(value=self.radiating, quality=SignalQuality.OK, at_us=0)
        return SignalReading(value=self.remote_ok, quality=SignalQuality.OK, at_us=0)

    async def read_analog(self, signal_id: str) -> SignalReading[float]:
        if signal_id == "tx.tx_peak_power_sample":
            return SignalReading(value=248.5, quality=SignalQuality.OK, at_us=0)
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
async def test_run_tx_power_calibration_routine_success():
    hal = MockHAL(remote_ok=True, radiating=True)
    logs: list[CalibrationLogEntry] = []
    inputs = [{"measured_power_kw": 250.0}, {"coupler_offset_db": 0.5}]
    input_idx = 0

    async def _step_input():
        nonlocal input_idx
        val = inputs[input_idx]
        input_idx += 1
        return val

    res = await run_tx_power_calibration(
        hal,
        actor="tester",
        step_input_func=_step_input,
        record_log_func=lambda entry: logs.append(entry),
        warmup_duration_s=1200.0,
        required_warmup_s=1200.0,
    )

    assert res.outcome == RoutineOutcome.SUCCESS
    assert res.routine == "tx_power_calibration"
    assert len(logs) == 3
    assert "Paso 1/3" in logs[0].message
    assert "Paso 2/3" in logs[1].message
    assert "Paso 3/3" in logs[2].message


@pytest.mark.anyio
async def test_run_tx_power_calibration_failed_preconditions():
    hal = MockHAL(remote_ok=False, radiating=True)
    logs: list[CalibrationLogEntry] = []

    res = await run_tx_power_calibration(
        hal,
        actor="tester",
        record_log_func=lambda entry: logs.append(entry),
        warmup_duration_s=1200.0,
        required_warmup_s=1200.0,
    )

    assert res.outcome == RoutineOutcome.FAILED
    assert len(logs) == 1
    assert logs[0].severity == "error"


@pytest.mark.anyio
async def test_run_tx_power_calibration_failed_warmup():
    hal = MockHAL(remote_ok=True, radiating=True)
    logs: list[CalibrationLogEntry] = []

    res = await run_tx_power_calibration(
        hal,
        actor="tester",
        record_log_func=lambda entry: logs.append(entry),
        warmup_duration_s=500.0,
        required_warmup_s=1200.0,
    )

    assert res.outcome == RoutineOutcome.FAILED
    assert any("caldeo insuficiente" in s.detail for s in res.steps)


@pytest.fixture
def client(tmp_path):
    hal = MockHAL(remote_ok=True, radiating=True)
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


def test_tx_power_calibration_requires_active_control_and_mant(client: TestClient):
    # En modo passive por defecto -> 403
    res = client.post("/api/control/tx-power-calibration")
    assert res.status_code == 403

    # Activar control activo, pero con mantenimiento OP (no MANT) -> 403
    client.post("/api/control", json={"mode": "active", "actor": "tester"})
    res2 = client.post("/api/control/tx-power-calibration")
    assert res2.status_code == 403
    assert "mantenimiento MANT" in res2.json()["detail"]


def test_tx_power_calibration_wizard_full_flow(client: TestClient):
    # 1. Activar mantenimiento MANT
    m_res = client.post(
        "/api/maintenance/unlock",
        json={"password": "mant1234", "actor": "tester", "duration_s": 3600},
    )
    assert m_res.status_code == 200

    # 2. Activar control activo
    c_res = client.post("/api/control", json={"mode": "active", "actor": "tester"})
    assert c_res.status_code == 200

    # 3. Iniciar wizard de calibración TX
    start_res = client.post("/api/control/tx-power-calibration?warmup_duration_s=1200")
    assert start_res.status_code == 202
    job_accepted = start_res.json()
    job_id = job_accepted["job_id"]
    assert job_accepted["routine"] == "tx_power_calibration"

    # 4. Sondear job hasta estar esperando input en Paso 2
    for _ in range(10):
        j_res = client.get(f"/api/control/jobs/{job_id}")
        assert j_res.status_code == 200
        j_data = j_res.json()
        if j_data["status"] == "awaiting_operator_input":
            break
        time.sleep(0.05)

    assert j_data["status"] == "awaiting_operator_input"
    assert j_data["current_step"] == 2

    # 5. Enviar input del Paso 2 (potencia pico medida)
    step2_res = client.post(
        f"/api/control/jobs/{job_id}/step",
        json={"data": {"measured_power_kw": 252.0}},
    )
    assert step2_res.status_code == 200

    # 6. Sondear job hasta estar esperando input en Paso 3
    for _ in range(10):
        j_res = client.get(f"/api/control/jobs/{job_id}")
        assert j_res.status_code == 200
        j_data = j_res.json()
        if j_data["status"] == "awaiting_operator_input" and j_data["current_step"] == 3:
            break
        time.sleep(0.05)

    assert j_data["status"] == "awaiting_operator_input"
    assert j_data["current_step"] == 3

    # 7. Enviar input del Paso 3 (offset de acoplador)
    step3_res = client.post(
        f"/api/control/jobs/{job_id}/step",
        json={"data": {"coupler_offset_db": 0.35}},
    )
    assert step3_res.status_code == 200

    # 8. Sondear job hasta estado final DONE
    for _ in range(10):
        j_res = client.get(f"/api/control/jobs/{job_id}")
        assert j_res.status_code == 200
        j_data = j_res.json()
        if j_data["status"] == "done":
            break
        time.sleep(0.05)

    assert j_data["status"] == "done"
    assert j_data["result"]["outcome"] == "success"

    # 9. Verificar que el Calibration Log contiene las 3 entradas
    log_res = client.get("/api/calibration-log")
    assert log_res.status_code == 200
    logs = log_res.json()
    assert len(logs) == 3
    assert any("252.00 kW" in l["message"] for l in logs)
    assert any("0.35 dB" in l["message"] for l in logs)
