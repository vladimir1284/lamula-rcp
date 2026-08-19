# Spike fase 0 — handshake RDA↔ORPG (Msg 11/12)

Cubre el punto 3 de "Lo primero dentro de esta fase" en
[fases.md](../docs/implementacion/fases.md), antes bloqueado por
[PEND-RCP-04](../docs/alcance/pendientes.md#pend-rcp-04-disponibilidad-de-orpg-real-o-stub-cm_tcp-para-fase-0).
No es código de producción; no reemplaza congelar el contrato RCP↔ORPG como esquema (eso sigue
pospuesto, punto 4 de la misma fase).

`rda_orpg_handshake_spike.py` implementa el CTM_Header/MSG_Header/Loopback Test del ICD 2620002F
(RDA/RPG) tomando el formato de bytes del proyecto legacy `RDA_Backend_Py` (2013, ingesta de los
radares cubanos al ORPG), que cita esa misma ICD como fuente. El script trae los dos roles:

```
python3 spike-fase0/rda_orpg_handshake_spike.py --role rda --port 10010 &
python3 spike-fase0/rda_orpg_handshake_spike.py --role orpg --port 10010
```

`--role orpg` **es** el stub CM_TCP que pedía el pendiente — solo hace falta mientras no haya un
ORPG real. Contra un ORPG real, se corre nada más `--role rda` y se apunta el ORPG real al mismo
puerto.

Ver `RESULTADO-rda-orpg.md` para el resultado documentado y un hallazgo a confirmar con el equipo
LAMULA ORPG antes de dar el formato por definitivo.
