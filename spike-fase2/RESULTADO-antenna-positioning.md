# Resultado — spike rutina "posicionamiento de antena"

Ejecutado 2026-08-19, `antenna_positioning_spike.py` vía `uv run` contra una instancia real de
`radar_emulator` (mismo override de puertos que el resto de Fase 1/2: Modbus `15020`, UDP
`15100`, WS `18080` — proceso persistente durante toda la sesión, no se reinició).

## PASA

- Encoder inválido (`degrade encoder_invalid`) → `FAILED` sin intentar mover, con paso que reporta
  la lectura inválida.
- `ant.au_on_status` en falso → `FAILED` (propagado desde la Rutina 5 subyacente, que rechaza en
  su propia precondición).
- Azimut: objetivo a +15,9° del punto de partida (posición no reiniciada entre spikes) →
  `SUCCESS`, posición final dentro de un margen de 3° (ver limitación de frenado abajo).
- Elevación: objetivo a +10,9° del punto de partida → `SUCCESS`, mismo margen.
- `ant.el_upper_limit_status` forzado a verdadero de antemano, con objetivo que exige subir →
  `FAILED`, propagado desde el rechazo de la guarda en la Rutina 5.

8/8 verificaciones en `OK`.

## Qué NO prueba este spike

- Que `gain_v_per_deg`/`max_voltage`/`tolerance_deg`/`timeout_s` de prueba (0,3 V/°, 2 V, 1°, 25 s)
  sean valores razonables para el radar real — son arbitrarios, elegidos solo para que este spike
  converja sin sobrepasar demasiado. Nadie debería copiarlos como default.
- Sobrepaso durante el frenado con voltajes/velocidades más altas — la rutina no calcula distancia
  de frenado contra la aceleración limitada del eje; con los valores bajos de este spike el
  sobrepaso fue pequeño (dentro del margen de 3°), pero la limitación sigue sin resolver.
- Interrupción a mitad de camino por límite/térmica disparados **durante** el posicionamiento
  (solo se probó de antemano, antes de empezar) — el mecanismo ya está probado a fondo en
  `spike-fase2/RESULTADO-antenna-movement.md`, que es de donde esta rutina lo hereda sin
  modificarlo.

## Sigue pendiente

Con esto, las seis rutinas del plan (§4.3) tienen primer borrador implementado. Ninguna
confirmada con el product expert (PEND-RCP-06 para la Rutina 1, PEND-RCP-07 para las Rutinas 2–6).
PEND-RCP-07 gana, con esta rutina, tres preguntas nuevas y genuinamente sin ningún punto de
partida (a diferencia del resto, que al menos tienen un marcador de posición del simulador):
tolerancia final de posicionamiento, si el acercamiento debe frenar de forma distinta a un simple
proporcional, y tiempo máximo antes de reportar fallo.
