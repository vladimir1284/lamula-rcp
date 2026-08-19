# Spike — stub de stream de momentos RCP↔DSP

Cubre [PEND-RCP-05](../docs/alcance/pendientes.md#pend-rcp-05-el-dsp-externo-no-tiene-aun-una-interfaz-de-referencia-ejecutable):
el contrato RCP↔DSP ya está congelado como esquema Pydantic
(`src/core/contracts/dsp.py`), pero no existe implementación de referencia ni simulador del lado
DSP equivalente a `radar_emulator` para el HAL. Este spike es un **stub propio** — no una
implementación del formato real del proyecto DSP, que sigue sin acordarse — construido solo para
no bloquear la ingestión DSP/DRX de Fase 1 mientras tanto.

`dsp_moment_stream_spike.py` trae los dos roles:

```
python3 spike-fase0/dsp_moment_stream_spike.py --role rcp --port 15551 &
python3 spike-fase0/dsp_moment_stream_spike.py --role dsp --port 15551
```

`--role dsp` genera un volumen sintético (dos elevaciones, cuatro radiales cada una, momentos UZ
y V) y lo manda por TCP como JSON de `RadialMoments`, con framing propio de largo de 4 bytes —
no un protocolo acordado con DSP, solo lo mínimo para ejercitar el esquema ya congelado.
`--role rcp` lo recibe y valida cada radial contra ese esquema, más el framing de volumen/elevación
(`RadialStatus`).

En cuanto exista una implementación de referencia real del lado DSP, este script se descarta o se
adapta al formato real. Ver `RESULTADO-dsp.md` para el resultado documentado.
