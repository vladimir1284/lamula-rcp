# Resultado — spikes Modbus y UDP, Fase 0

Ejecutado 2026-08-19 contra una instancia local de `radar_emulator` (config derivada de
`config/rd100s.seed.json`, solo puerto Modbus y `dest_port`/`dest_host` de UDP remapeados a
puertos no privilegiados para no requerir root — ningún otro campo).

## 1. Spike Modbus — PASA

`modbus_client_spike.py`: cliente pymodbus 3.15, una sola conexión TCP, interroga los diez unit
IDs de la semilla. Verificado:

- FC01 (Read Coils) sobre los quince grupos DI/DO de los diez unit IDs.
- FC03 (Read Holding Registers) sobre los grupos AI/AO.
- FC05/FC15 (write single/multiple coil) sobre las tres unidades con DO, con read-back.
- FC06/FC16 (write single/multiple register) sobre las dos unidades con AO, con read-back.
- Escritura sobre una DI de solo lectura (unit 1, addr 0) responde excepción Modbus, no se
  acepta en silencio — confirma la regla de `docs/interfaces/modbus.md` desde el lado cliente.
- Enrutamiento por `unit_id` sobre una sola conexión TCP es correcto en los diez casos — esto es
  lo que pedía PEND-21 verificar desde el lado consumidor.

**Hallazgo no documentado hasta ahora, relevante para PEND-RCP-01/PEND-20 (ciclo de
interrogación del RCP):** las escrituras no se aplican al instante. `signal-store.ts` las deja
pendientes y las consume recién en el siguiente tick (`tick_ms=50` en la semilla) — es la misma
semántica de "flanco, no nivel" que `docs/interfaces/modbus.md` describe para los pares
Tx/RFE/Radar, pero generalizada: **aplica a todo `from_controller`, no solo a los comandos por
flanco**. Un read-back inmediato tras un write puede devolver el valor viejo. El cliente Modbus
del RCP no debe asumir consistencia read-your-write dentro del mismo ciclo de interrogación; debe
esperar al menos un tick (o diseñar su loop de interrogación asumiendo esta latencia). Esto
alimenta directamente el dato que PEND-20 pide que el RCP produzca (ciclo de interrogación y
timeout).

## 2. Spike UDP — PASA

`udp_encoder_spike.py`: receptor `RD100S-ENC-UDP v1`, verificado:

- Parseo de los 36 octetos con el formato exacto de la sección 2 del contrato (little-endian,
  sin relleno).
- Descarte silencioso de datagramas con `magic`, `version` o longitud inválidos (probado con
  paquetes sintéticos, no solo contra el emisor real).
- Manejo de envolvente de `seq` en `2^32` (`2^32-1 → 0` se interpreta como delta `+1`, no como
  retroceso).
- Detección de reinicio del emisor: `seq` y `t_us` retrocediendo juntos.
- Declaración de pérdida de stream por timeout (100 ms, diez periodos nominales, tal como
  recomienda §7 del contrato).
- `seq` inicial recibido del emulador real no fue cero (confirma que el receptor no debe
  asumirlo).

### 2b. Degradaciones en vivo (desde el emulador) — PASA

`udp_degradation_spike.py`: cliente WebSocket (canal `degrade` de `docs/interfaces/websocket.md`)
que dispara cada degradación real del emulador mientras un receptor UDP corre en paralelo, en
vez de simular solo el parser con paquetes sintéticos. Verificado en vivo, contra el emisor real:

- **Pérdida** (`loss`, 30%): huecos de `seq` detectados, tasa observada ~28% en la muestra.
- **Ráfaga de corte** (`burst`, 300 ms): hueco medible de ~304 ms en las llegadas.
- **Duplicación** (`duplicate`, 100%): `seq` repetida consecutiva en la mitad de los paquetes.
- **Congelación** (`freeze`): `az`/`el` constantes mientras `seq` sigue avanzando y bit
  `DEGRADED` en 1 — confirma que es distinguible de "silencio" (§6 del contrato, nota
  "Congelación contra silencio").
- **Encoder inválido** (`encoder_invalid`): `AZ_VALID`/`EL_VALID` caen a 0 en el 100% de los
  paquetes de la ventana.
- **Salto de secuencia** (`seq_jump`, +500): delta observado 521 (500 + avance normal del
  intervalo de medición) — confirma que es un delta de una sola vez, no un offset permanente.
- **Silencio total** (`silence`): 0 paquetes durante 500 ms — el receptor debe declarar stream
  perdido por el timeout ya validado en el spike de parser (§2), no por payload.

No se ejercitó **reordenamiento** (`reorder`) de forma aislada — comparte mecanismo con jitter en
la implementación del emulador (`encoder.ts`: mismo `extraDelayMs`, toma el mayor de los dos si
ambos están activos) y el efecto ya se observa indirectamente en el jitter de llegada de todas las
fases. No se considera necesario un caso aparte para subir la confianza antes de congelar el
contrato RCP↔HAL.

## 3. Spike RDA↔ORPG — bloqueado

No ejecutado. Bloqueado por
[PEND-RCP-04](../docs/alcance/pendientes.md#pend-rcp-04-disponibilidad-de-orpg-real-o-stub-cm_tcp-para-fase-0):
no hay build de ORPG real ni stub CM_TCP disponible todavía. Sin resolver esto no hay con qué
hablar para el handshake mínimo (Msg 11/12).

## 4. Congelar los cuatro contratos como esquemas Pydantic — no hecho todavía

Ver punto 3 arriba (bloqueante parcial: ORPG sí puede congelarse como esquema ICD 2620002 sin
necesitar el spike de handshake, pero RCP↔HAL debería esperar a que alguien confirme si vale la
pena ejercitar las degradaciones en vivo primero). Siguiente paso de esta fase.
