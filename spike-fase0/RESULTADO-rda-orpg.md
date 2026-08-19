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

## Hallazgo — a confirmar con LAMULA ORPG antes de congelar el contrato

El legacy `RDA_Backend_Py/RDA_TCPServer.py` (`process_Data`), al recibir un mensaje entrante de
**tipo 12**, responde reenviando su **propio** tipo 12 (`self.sendMessage(12)`), y valida el
loopback recién cuando lo que llega es tipo **11** (`self.fLBT.process_LoopBack_Test(s)`). Es
decir: en el código de 2013, quien valida el eco es quien recibe un **11** entrante, no un 12 —
al revés de lo que la lectura directa del ICD (RDA emite 11, RPG hace eco con 12, RDA valida)
sugiere, y al revés de lo que este spike implementó.

No se resolvió esa discrepancia localmente — el spike sigue la lectura directa del ICD, no la
lógica del legacy. Antes de congelar el contrato RCP↔ORPG (fases.md, Fase 0 punto 4) hay que
confirmar con el equipo LAMULA ORPG cuál de las dos direcciones es la real, porque:

- puede ser un bug del legacy de 2013 nunca corregido porque el ORPG real con el que hablaba
  toleraba ambas direcciones, o
- puede ser que el legacy esté codificando un detalle real del ICD que la lectura de las tablas
  no deja ver (p. ej. quién inicia el loopback puede depender de si el canal es principal o
  redundante — `RDA_Redundant_Channel` en `MSG_Header`, no ejercitado por este spike).

## Pendiente relacionado, no resuelto por este spike

`RDA_TCPServer.py` también contesta `process_Request_Data`/`process_VCP`/RDA Status/Perf-Maint/
VCP/Clutter Maps/Adaptation Data completos — mucho más que el loopback. Ese alcance corresponde a
Fase 3 ("emulación RDA completa"), no a este spike de Fase 0, y no se portó aquí.
