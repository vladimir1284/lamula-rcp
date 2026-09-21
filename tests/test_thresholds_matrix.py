"""Pruebas para E3 Thresholds Matrix (/api/thresholds-matrix).

Verifica que el endpoint GET /api/thresholds-matrix devuelva la estructura
con los umbrales globales y la matriz de 19 parámetros donde las celdas
no disponibles per-parámetro en el contrato actual se marcan explícitamente como None.
"""

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


def test_get_thresholds_matrix(client: TestClient):
    res = client.get("/api/thresholds-matrix")
    assert res.status_code == 200
    data = res.json()

    assert "globals" in data
    assert "rows" in data

    globals_data = data["globals"]
    assert globals_data["sqi_threshold"] == 0.35
    assert globals_data["log_threshold"] == 2.0
    assert globals_data["ccor_threshold"] == 15.0
    assert globals_data["sig_threshold"] == 5.0

    rows = data["rows"]
    assert len(rows) == 19

    expected_params = [
        "DBZ", "DBT", "VEL", "WID", "ZDR", "KDP", "PHIDP", "RHOHV",
        "SQI", "LDRH", "RHOH", "PHIH", "LDRV", "RHOV", "PHIV",
        "HCLASS", "SNR", "DBZA", "DBTA",
    ]
    actual_params = [r["parameter"] for r in rows]
    assert actual_params == expected_params

    # Celdas que no existen en el contrato se deben marcar explícitamente como None (N/A)
    for row in rows:
        assert row["log_db"] is None
        assert row["ccor_db"] is None
        assert row["sig_db"] is None
        assert row["sqi"] is None
        assert row["pmi"] is None
