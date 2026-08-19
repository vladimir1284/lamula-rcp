"""Autoridad de control (D-07): un solo operador, arbitraje passive/active.

En memoria, sin persistencia -- esqueleto de Fase 1
(docs/implementacion/fases.md). Ni autenticacion ni auditoria durable de
quien pidio el cambio: `actor` es el string que mande el llamador, sin
verificar identidad. Marcar como PEND si Fase 2 (seguridad de parametros)
necesita mas que esto.
"""

from __future__ import annotations

from datetime import datetime, timezone

from core.contracts.mmi import ControlAuthorityState, OperatorMode


class ControlAuthority:
    def __init__(self) -> None:
        self._state = ControlAuthorityState(
            mode=OperatorMode.PASSIVE, actor="system", since_wall=datetime.now(timezone.utc)
        )

    @property
    def state(self) -> ControlAuthorityState:
        return self._state

    def set_mode(self, mode: OperatorMode, actor: str) -> ControlAuthorityState:
        self._state = ControlAuthorityState(mode=mode, actor=actor, since_wall=datetime.now(timezone.utc))
        return self._state
