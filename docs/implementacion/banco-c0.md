# Banco de integración C0 — RCP real contra DSP real

`tools/hil/run-c0.sh` levanta los binarios de verdad de este repositorio y del
proyecto LAMULA DSP y los hace hablar entre sí por sockets de verdad. Es la
primera fase ejecutable del plan de integración de los tres proyectos
([PEND-RCP-13](../alcance/pendientes.md#pend-rcp-13), y P-13 en el repositorio
del DRx).

## Qué monta

```
drx_faker  ──TCP──▶  lamula-dsp  ──TCP──▶  gateway del RCP
(DRx falso)          (binario real)        (binario real)
     rayos I/Q            momentos            config + START
   contrato DRx↔DSP     contrato DSP↔RCP    ◀── camino descendente
```

Los dos enlaces siguen la regla **el productor conecta**: el `drx_faker`
conecta al DSP, y el DSP conecta al RCP, que escucha en `--dsp-port`.

Lo único que no es real es el origen de las muestras. `drx_faker` es un ejemplo
del repositorio del DSP (`cargo run --example drx_faker`) que genera rayos
sintéticos y los escribe por el cable `DRx↔DSP` a cadencia de PRF. Sustituirlo
por una ZedBoard con `vector_source` es la fase B del plan, y no exige cambiar
nada de lo demás.

## Qué prueba, y qué no

Prueba: framing y transporte de los dos enlaces, el camino descendente
`config` + `START` desde este repositorio, el ensamblado de radiales del DSP,
la decodificación de momentos de `adapters/dsp/wire.py`, y la reconexión de
cada lado.

No prueba **nada de hardware**: ni cadencia, ni jitter, ni contrapresión
reales. Los radiales llegan marcados con `header_flag::SIMULATED_SOURCE`, que
es justo para esto.

## Uso

```sh
tools/hil/run-c0.sh 20     # segundos de captura; por defecto 15
```

Requiere el repositorio del DSP en `../lamula-dsp` (el mismo supuesto que el
pin de contrato) y `cargo` en el `PATH`. El script deja los tres logs en un
directorio temporal que imprime al arrancar, y falla si al terminar el RCP no
ha recibido ni un radial.

## La configuración que baja, y lo que todavía no decide el operador

El DSP no emite un solo radial hasta que recibe un `config` válido y un
`START`: su máquina de estados arranca en `setup`. Hasta ahora este repositorio
sólo sabía mandar `control` (`REQUEST_SPECTRUM`, `RESET_COUNTERS`), así que no
había forma de llevarlo a `running`.

El banco lo resuelve con un perfil fijo (`tools/hil/profile-c0.json`) que el
gateway aplica al conectar el DSP, si se arranca con `--dsp-bench-profile`.
**Es andamio de banco, no comportamiento de operador.** Quién decide la
configuración en operación es el Scan Controller, a partir del Scan Worksheet,
y ese mapeo sigue abierto (PEND-RCP-10). Sin ese flag el gateway no configura
al DSP, igual que antes.

## Hallazgos que salieron de montarlo

Los dos primeros se encontraron al ejecutar el banco por primera vez, y ninguno
era visible desde los tests de cada repositorio por separado — cada lado se
probaba contra un doble que, por construcción, hacía lo que ese lado esperaba.

1. **Los dos extremos del enlace `DSP↔RCP` escuchaban.** Este repositorio hace
   `asyncio.start_server`; el DSP hacía `TcpListener::bind` + `accept`. Nadie
   conectaba. Resuelto en el DSP, que ahora conecta.
2. **Todos los radiales salían con ancho de azimut cero.** El DSP publicaba
   `az_end_deg` igual a `az_start_deg` porque su `AssembledRadial` sólo
   guardaba el azimut del primer pulso del radial. Un radial de ancho cero no
   es archivable como Level-II ni aceptable para ORPG. Resuelto en el DSP,
   conservando el azimut de los dos extremos.
3. **Este repositorio cerraba la conexión** al recibir uno de esos radiales,
   tratándolo como trama mal formada. Ahora distingue: `WireFormatError` (el
   flujo queda desincronizado) corta el enlace; `DegenerateRadialError` (la
   trama está intacta, el contenido no sirve) descarta ese radial y lo cuenta.

## Lo que falta para la fase C1

- Que el `drx_faker` lo sustituya la ZedBoard real (fase B; necesita el
  firmware del DRx, su fase Z4.2 en adelante).
- Consumir `status`/`bite_event` ([PEND-RCP-14](../alcance/pendientes.md#pend-rcp-14)):
  hoy llegan por este mismo enlace y no los mira nadie.
- El contador `degenerate_radials` del receptor no llega a la MMI; haría falta
  un campo nuevo en `DspStreamStatus`.
