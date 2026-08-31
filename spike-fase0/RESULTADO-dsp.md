# Resultado — spike stub stream de momentos RCP↔DSP

> **Histórico (2026-08-30).** Esta corrida se hizo contra el framing propio del stub, que ya no
> existe: el script se portó al contrato de cable real `DSP↔RCP v0.1`. El resultado vigente está
> más abajo, en «Corrida sobre el contrato real». Lo de esta sección se conserva como registro de
> lo que se validó mientras no había contrato.
> Ver [`docs/interfaces/dsp.md`](../docs/interfaces/dsp.md).

Ejecutado 2026-08-19, `dsp_moment_stream_spike.py --role dsp` y `--role rcp` en dos procesos
locales, vía `uv run` (PEND-RCP-03: `uv` con lockfile, `uv.lock` generado en esta corrida). No
contra un emisor DSP real — no existe todavía ninguna implementación de referencia del lado DSP.

## Spike DSP↔RCP — PASA (contra el stub local, no contra DSP real)

- Volumen sintético de 2 elevaciones × 4 radiales, momentos UZ y V, 8 gates cada uno.
- Cada radial serializado como JSON de `RadialMoments` (esquema ya congelado en
  `src/core/contracts/dsp.py`), framing propio de largo de 4 bytes big-endian.
- RCP (consumidor) recibió los 8 radiales, validó cada uno contra el esquema Pydantic sin error,
  confirmó framing de volumen (primer radial `start_of_volume`, último `end_of_volume`) y que
  todos traen los momentos esperados con la cantidad de gates esperada.

## Qué NO valida este spike

- El formato de bytes/framing real que use el proyecto DSP — es inventado por este stub, no
  acordado. Si el DSP entrega crudo con escala/offset (probable para no saturar el enlace de
  1 GbE, D-03), esa conversión tampoco se ejercita aquí; queda a cargo del adaptador
  `src/adapters/dsp/` cuando exista.
- `capture_t_us` no se compara entre procesos — `common.py` ya advierte que un monotónico de un
  proceso no es comparable con el de otro; el stub genera un valor creciente propio, no reproduce
  reloj real de DSP.
- El rol de `RDA_Redundant_Channel` no aplica a este contrato (es propio de RDA↔ORPG); no
  confundir con [PEND-RCP-04](../docs/alcance/pendientes.md#pend-rcp-04-disponibilidad-de-orpg-real-o-stub-cm_tcp-para-fase-0).

## Sigue pendiente

Acceso a una implementación de referencia real del proyecto DSP para validar el esquema y el
framing contra algo no inventado localmente. Hasta entonces, Fase 1 puede avanzar la ingestión
DSP/DRX contra este stub, dejando explícito en cualquier revisión externa que el formato de
transporte es propio de este repo, no del proyecto DSP.


## Corrida sobre el contrato real — PASA

Ejecutado 2026-08-30, los dos roles del mismo script ya portado al formato de cable
`DSP↔RCP v0.1` (vendorizado en `contract/vendor/`, anclado por hash).

- Volumen sintético de 2 elevaciones × 4 radiales, momentos UZ y V, 8 celdas cada uno, enmarcado
  con la cabecera común de 12 B del contrato.
- El consumidor decodificó los 8 radiales con `src/adapters/dsp/wire.py` — el mismo adaptador que
  usa `src/`, no una decodificación aparte del spike.
- Se comprobó además: que un `status` por el mismo enlace no rompe al consumidor, que el framing
  de volumen sale de las banderas de bit del cable, que la hora de pared llega con zona horaria y
  medida en el emisor, y que el reloj monótono crece radial a radial.

### Qué sigue sin validar

El emisor sigue siendo de este repo, no del proyecto DSP. Lo verificado es **formato y framing**.
No se ha ejercitado cadencia real, contrapresión con radiales de 3680 celdas a PRF alta, ni
reconexión. Eso necesita el simulador de señal del proyecto DSP, que aún no existe.
