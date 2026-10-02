from __future__ import annotations

from datetime import UTC, datetime

from core.bite.manager import BiteManager
from core.contracts.bite import BiteTransition
from core.contracts.dsp import DspBiteEvent, DspSeverity


def _dsp_event(*, subsystem: int, code: int, severity: DspSeverity, value: int = 0, text: str = "") -> DspBiteEvent:
    return DspBiteEvent(
        event_time_utc=datetime.now(UTC),
        code=code,
        value=value,
        severity=severity,
        subsystem=subsystem,
        text=text,
    )


def test_ingest_dsp_event_fault_severity_becomes_active_fault() -> None:
    manager = BiteManager()

    event = manager.ingest_dsp_event(_dsp_event(subsystem=3, code=42, severity=DspSeverity.FAULT))

    assert event.signal_id == "dsp.3.42"
    assert event.transition is BiteTransition.FAULT
    assert event in manager.active_faults()
    assert event in manager.history()


def test_ingest_dsp_event_config_error_is_also_a_fault() -> None:
    manager = BiteManager()

    event = manager.ingest_dsp_event(_dsp_event(subsystem=1, code=7, severity=DspSeverity.CONFIG_ERROR))

    assert event.transition is BiteTransition.FAULT
    assert event in manager.active_faults()


def test_ingest_dsp_event_info_or_warning_is_not_a_fault() -> None:
    manager = BiteManager()

    manager.ingest_dsp_event(_dsp_event(subsystem=2, code=5, severity=DspSeverity.FAULT))
    cleared = manager.ingest_dsp_event(_dsp_event(subsystem=2, code=5, severity=DspSeverity.INFO))

    assert cleared.transition is BiteTransition.CLEARED
    assert cleared not in manager.active_faults()
    assert all(e.signal_id != "dsp.2.5" for e in manager.active_faults())


def test_ingest_dsp_event_does_not_interfere_with_modbus_signal_ids() -> None:
    manager = BiteManager()

    manager.ingest_dsp_event(_dsp_event(subsystem=9, code=1, severity=DspSeverity.FAULT))

    assert manager.history(subsystem="dsp") != []
    assert manager.history(subsystem="tx") == []
