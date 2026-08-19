# Resultado — spike RDA↔ORPG (Msg 11/12), Fase 0

Ejecutado 2026-08-19, `rda_orpg_handshake_spike.py --role rda` y `--role orpg` en dos procesos
locales (puerto no privilegiado para la prueba; el ICD fija 10010 para producción). No contra
ORPG real — no hay acceso a un build real en esta etapa; `--role orpg` es el stub CM_TCP que el
pendiente pedía construir.

## Spike RDA↔ORPG — PASA (contra el stub local, no contra ORPG real)

- Login (CTM.Typ=0 con password) → ack (CTM.Typ=1) con el formato `"<id> <canal> connected"` del
  legacy.
- RDA envía Msg 11 (Loopback Test, 104 bytes: halfword de tamaño + 51 valores) sin que ORPG lo
  pida — es unsolicited tras el login ack, tal como hace el legacy en `process_Login`.
- ORPG (stub) recibe Msg 11, lo reconoce por `MSG_Header.message_Type`, y lo devuelve intacto
  como Msg 12.
- RDA valida que el Msg 12 recibido tiene el mismo payload que el Msg 11 que mandó → loopback
  test pasado.

Verificado en ambos sentidos, log de las dos corridas guardado en
`/tmp/claude-1000/.../tasks/*.output` de la sesión que hizo el spike (no versionado).

## Hallazgo — confirmado por el usuario (producción real), no por el equipo LAMULA ORPG

El legacy `RDA_Backend_Py/RDA_TCPServer.py` (`process_Data`), al recibir un mensaje entrante de
**tipo 12**, responde reenviando su **propio** tipo 12 (`self.sendMessage(12)`), y valida el
loopback recién cuando lo que llega es tipo **11** (`self.fLBT.process_LoopBack_Test(s)`). Es
decir: en el código de 2013, quien valida el eco es quien recibe un **11** entrante, no un 12 —
al revés de lo que la lectura directa del ICD (RDA emite 11, RPG hace eco con 12, RDA valida)
sugiere, y al revés de lo que este spike implementó.

**Confirmado 2026-08-19 por el usuario (vladimir):** no es un bug de 2013 — ese mismo
`RDA_Backend_Py` corrió en producción real haciendo ingesta de productos al ORPG. La dirección
del legacy es la que hay que seguir, no la lectura literal de las tablas del ICD. Esta
confirmación viene de experiencia operativa directa del usuario, no de una consulta formal al
equipo LAMULA ORPG — sigue siendo la fuente más fuerte disponible hoy, pero conviene que quede
explícito en cualquier revisión externa del contrato que el origen es "funcionó en producción",
no un sign-off documentado del equipo ORPG.

El spike (`rda_orpg_handshake_spike.py`) todavía implementa la lectura literal del ICD, **no**
la dirección confirmada del legacy — queda pendiente alinearlo antes de congelar el contrato
RCP↔ORPG.

Sin resolver todavía: el rol del `RDA_Redundant_Channel` en `MSG_Header` (canal principal vs.
redundante) no se ejercitó, y podría cambiar quién inicia el loopback en cada caso.

## Pendiente relacionado, no resuelto por este spike

`RDA_TCPServer.py` también contesta `process_Request_Data`/`process_VCP`/RDA Status/Perf-Maint/
VCP/Clutter Maps/Adaptation Data completos — mucho más que el loopback. Ese alcance corresponde a
Fase 3 ("emulación RDA completa"), no a este spike de Fase 0, y no se portó aquí.
