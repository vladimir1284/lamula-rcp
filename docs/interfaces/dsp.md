# Interfaz RCP↔DSP

El stream de momentos dejó de ser una dependencia externa sin forma. El proyecto
LAMULA DSP congeló el formato de cable `DSP↔RCP v0.1` y aquí está vendorizado y
anclado por hash, con adaptador y tests contra el formato real en vez de contra
un stub propio.

## Quién manda

**El contrato lo posee el proyecto DSP**, igual que el `DRx↔DSP` lo posee el DRx.
Aquí sólo se consume. La consecuencia práctica: nada de
`contract/vendor/dsp_rcp_v0_1.py` ni de `mmi/src/contracts/dsp_rcp_v0_1.ts` se
edita a mano, y un cambio de formato se pide allí, no se parchea aquí.

`contract/vendor/UPSTREAM.toml` fija el SHA-256 de cada fichero vendorizado.
`tools/check_vendored_contract.py` falla si alguno se aparta —una edición local,
o Prettier pasando por `mmi/src/`— y avisa si el origen se movió sin que aquí
nadie re-vendorizara. Es el mismo patrón que el proyecto DSP usa para consumir
el contrato del DRx: tres repositorios, un solo idioma de vendorizado.

## Las tres capas

| Capa | Dónde | Qué sabe |
| --- | --- | --- |
| Cable | `contract/vendor/dsp_rcp_v0_1.py` | Bytes, `struct`, desplazamientos |
| Adaptador | `src/adapters/dsp/wire.py` | Traduce cable ↔ dominio |
| Dominio | `src/core/contracts/dsp.py` | `RadialMoments` en unidades de ingeniería |

`src/core/` no ve un buffer jamás, que es la misma regla que ya rige para
Modbus. Si algún día el cable pasa a entregar enteros con escala y offset —el
descriptor de momento ya reserva los campos— la conversión es del adaptador y el
dominio no se entera.

## Forma del cable

Cabecera común de 12 B y detrás `payload_len` bytes con el mensaje entero. Un
lector de tramas hace: leer 12 B, leer `payload_len` B, y ya tiene el mensaje sin
necesitar saber de qué tipo es.

El `magic` es `LMDS`, distinto del `LMDR` del contrato `DRx↔DSP`, que usa una
cabecera **del mismo tamaño y la misma forma**. Eso es deliberado: un solo lector
de tramas sirve para los dos enlaces, y el magic distinto es lo que impide que un
cable cruzado pase por bueno. Hay un test que manda una cabecera con el magic del
DRx y comprueba que se rechaza.

Un `moment_ray` son 88 B de cabecera más `n_moments` bloques de 16 B, cada uno
seguido de `n_gates` valores `f32`. Los momentos llegan en unidades de ingeniería
a precisión plena: el enlace de 1 GbE (D-03) da de sobra, y la diezmación a 8 o
16 bits es cosa del codificador Level-II de este repo, no del cable.

## Dos relojes, resuelto

`AGENTS.md` marcaba la separación de relojes como asunción de diseño pendiente de
confirmar. En el lado DSP ya está cerrada: **el cable trae los dos instantes**.

- `acq_time_utc` — hora de pared del instante de adquisición, **medida en el
  DSP**. Es la que se archiva en Level-II y la que va a ORPG.
- `acq_monotonic_us` — el mismo instante en el reloj monótono del DSP. Sirve para
  ordenar radiales y medir intervalos sin que un ajuste de UTC los corrompa.

Lo que esto evita: sellar la hora de pared al recibir metía la latencia del
enlace dentro de la marca de tiempo de una observación meteorológica. Ahora no
hace falta.

Cuidado con el monótono: **no es comparable con el de este proceso**. Vale para
diferencias entre radiales del mismo flujo y para nada más.

Sigue abierto lo mismo de antes para el contrato `RCP↔ORPG`, que es donde la
regla nació.

## Detalles del adaptador que no son obvios

**El azimut cruza por cero.** El cable manda `az_start` y `az_end`; el dominio
quiere centro y anchura. Restar sin más da −359,5° de anchura para un radial que
abre en 359,75° y cierra en 0,25°, y coloca el centro en la antípoda. El
adaptador usa módulo 360 y hay test.

**`ray_flags` es máscara de bits; `RadialStatus` es un estado único.** Un radial
puede ser a la vez principio de volumen y principio de elevación. El adaptador
colapsa por prioridad —lo más externo gana— y pierde información a propósito. El
adaptador `RCP↔ORPG`, que sí necesita el detalle para el Msg 31, lee el cable y
no este modelo.

**Por el mismo enlace llegan más cosas que radiales.** Un `status`, un
`bite_event` o un `config_ack` no son errores de trama: se cuentan aparte y se
ignoran mientras no haya consumidor. Una trama mal formada sí corta la conexión,
porque tras un largo erróneo el flujo está desincronizado y seguir leyendo
produce radiales que parecen válidos y no lo son.

## Lo que este contrato aporta y antes faltaba

Además del stream de momentos, el cable trae el plano de control entero, que
antes no existía por ningún lado:

- **Configurar y arrancar son pasos distintos.** Un `config` que llega en marcha
  se rechaza con `not_in_setup_phase`.
- **Autotest de enlace obligatorio al reconectar**, con nonce.
- **La configuración se lee, no sólo se escribe**: `request_config` la devuelve y
  `status.config_seq` dice cuál está vigente.
- **Capacidades declaradas**: qué momentos, qué dealiasing y qué estimadores
  soporta esa compilación del DSP, para no ofrecer al operador un modo que el
  procesador no implementa.
- **Telemetría de completitud y deriva**, no un bit de vivo/muerto: `bins_ok`
  frente a `bins_total`, periodo de disparo medido frente a mandado, y suelo de
  ruido y offset de continua por canal.

De momento el receptor sólo consume `moment_ray`. Cablear el resto al Scan
Controller y al System Status & BITE Manager es trabajo de Fase 2.

## Qué sigue sin validarse

Todo lo de aquí se ha probado contra tramas construidas con el módulo generado
del proyecto DSP, no contra un DSP corriendo. Eso cubre el formato; no cubre
cadencia, contrapresión con radiales de 3680 celdas a PRF alta, ni comportamiento
en reconexión real. Sigue haciendo falta un emisor de referencia del lado DSP —
su simulador de señal, cuando exista— para cerrar eso.
