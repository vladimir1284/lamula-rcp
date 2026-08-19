"""System Status & BITE Manager (plan §4.4). Sondea un conjunto fijo de
senales de estado del HAL activo (real o simulador) y produce un
`BiteEvent` cada vez que alguna cruza entre "sana" y "en falla" -- no en
cada lectura, solo en el cambio (evita inundar el historial con la misma
falla repetida en cada poll).

**Como se eligio `MONITORED_SIGNALS`:** todas las senales `*_ok_status` del
catalogo vendorizado (sanas cuando valen `True`, siguiendo la convencion de
nombres que ya usa `radar_emulator` de punta a punta -- `sys.*`, `tx.*`,
`rx.*`, `ant.*`), mas `*_fault_status` y `*_over_current_status` (sanas
cuando valen `False`). Dos excepciones que no siguen el patron de sufijo:
`ant.i2t_drive_az_status`/`i2t_drive_el_status` (proteccion termica,
enclavada, sana en `False`) -- ver `core/safety_guard/antenna_limits.py`
para el mismo hallazgo.

**Deliberadamente fuera de esta lista:** senales de estado positivo como
`tx.tx_on_status`, `ant.au_on_status`, `rx.rfe_on_status` o
`ant.el_upper_limit_status` -- su valor "malo" depende del contexto
operativo (un transmisor apagado no es una falla si nadie lo encendio
todavia), no del nombre de la senal. Tratarlas como BITE dispararia una
falla permanente en reposo, no algo util para el operador.

**Salud del enlace ORPG (plan §4.4) queda fuera:** esa interfaz no existe
todavia (PEND-RCP-04), no hay nada que agregar.

**Filtrado por subsistema, no por severidad:** el catalogo de senales no
tiene ningun metadato de severidad -- inventar una escala (p.ej.
"critico"/"advertencia") sin respaldo del product expert seria el mismo
error que ya se evito en `antenna_positioning.py`. El filtrado disponible
es por subsistema (`tx`, `rx`, `ant`, `sys`, derivado de `signal_id`).
"""

from __future__ import annotations

import time
from collections import deque

from core.contracts.bite import BiteEvent, BiteTransition
from core.contracts.common import MonotonicMicros
from core.contracts.hal import HardwareAbstractionLayer, SignalId

# True: la senal esta sana cuando su lectura vale True (patron "*_ok_status").
# False: la senal esta sana cuando su lectura vale False (patron "*_fault_status",
# "*_over_current_status", y las dos excepciones i2t_drive_*_status).
MONITORED_SIGNALS: dict[SignalId, bool] = {
    "sys.line_parameters_ok_status": True,
    "sys.environment_ok_status": True,
    "sys.standby_system_ok_status": True,
    "tx.interlock_ok_status": True,
    "tx.wg_pressure_ok_status": True,
    "tx.cb_blower_ok_status": True,
    "tx.magnetron_blower_ok_status": True,
    "tx.pha_seq_ok_status": True,
    "tx.duty_cycle_ok_status": True,
    "tx.fps_ok_status": True,
    "tx.mps_fault_status": False,
    "tx.magnetron_peak_over_current_status": False,
    "rx.p_15_v_ps_ok_status": True,
    "rx.n_15_v_ps_ok_status": True,
    "rx.p_12_v_ps_ok_status": True,
    "rx.rfe_fault_status": False,
    "ant.drive_az_ok_status": True,
    "ant.drive_el_ok_status": True,
    "ant.i2t_drive_az_status": False,
    "ant.i2t_drive_el_status": False,
}

DEFAULT_HISTORY_LIMIT = 500


def _now_us() -> MonotonicMicros:
    return time.monotonic_ns() // 1000


class BiteManager:
    def __init__(self, history_limit: int = DEFAULT_HISTORY_LIMIT) -> None:
        self._healthy_when: dict[SignalId, bool] = dict(MONITORED_SIGNALS)
        self._was_healthy: dict[SignalId, bool] = {}
        self._active_faults: dict[SignalId, BiteEvent] = {}
        self._history: deque[BiteEvent] = deque(maxlen=history_limit)

    async def poll(self, hal: HardwareAbstractionLayer) -> list[BiteEvent]:
        """Lee todas las senales monitoreadas una vez y devuelve solo los
        eventos nuevos (transiciones desde el poll anterior). La primera
        lectura de una senal cuenta como transicion si ya esta en falla --
        se asume sana antes del primer poll, para que una falla presente
        desde el arranque igual se reporte."""

        new_events: list[BiteEvent] = []
        for signal_id, healthy_value in self._healthy_when.items():
            reading = await hal.read_digital(signal_id)
            healthy_now = reading.value == healthy_value
            healthy_before = self._was_healthy.get(signal_id, True)
            if healthy_now != healthy_before:
                transition = BiteTransition.CLEARED if healthy_now else BiteTransition.FAULT
                event = BiteEvent(signal_id=signal_id, transition=transition, detail=f"value={reading.value}", at_us=_now_us())
                new_events.append(event)
                self._history.append(event)
                if transition is BiteTransition.FAULT:
                    self._active_faults[signal_id] = event
                else:
                    self._active_faults.pop(signal_id, None)
            self._was_healthy[signal_id] = healthy_now
        return new_events

    def active_faults(self) -> list[BiteEvent]:
        return list(self._active_faults.values())

    def history(self, *, subsystem: str | None = None, limit: int | None = None) -> list[BiteEvent]:
        events = list(self._history)
        if subsystem is not None:
            events = [e for e in events if e.signal_id.split(".", 1)[0] == subsystem]
        if limit is not None:
            events = events[-limit:]
        return events
