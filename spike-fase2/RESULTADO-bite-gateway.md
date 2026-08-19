# Resultado — spike BITE cableado al gateway

Ejecutado 2026-08-19, gateway levantado con `PYTHONPATH=src uv run python -m adapters.gateway
--modbus-port 15020 --udp-port 15100 --dsp-port 15551 --http-port 18000` contra la misma
instancia real de `radar_emulator` del resto de la sesión, y `bite_gateway_spike.py` como cliente
independiente (REST + WS a la vez, imitando un MMI real).

## PASA

- `GET /api/status` al arrancar el gateway ya trae 15 fallas activas en `active_bite_faults`
  (las mismas `*_ok_status` no cableadas en la semilla, detectadas en el primer poll de fondo —
  confirma que el poller de fondo corre solo, sin necesitar ningún cliente WS conectado).
- Forzar `tx.mps_fault_status` directo contra `radar_emulator` (no contra el gateway) → llega un
  `BiteEventMessage` con `transition: "fault"` por el WS del gateway a un cliente ya conectado.
- `GET /api/status.active_bite_faults` incluye `tx.mps_fault_status` después.
- Liberar la señal → `BiteEventMessage` con `transition: "cleared"` por WS, y
  `active_bite_faults` ya no la incluye.

4/4 verificaciones en `OK`.

## Qué NO prueba este spike

- Múltiples clientes WS a la vez recibiendo el mismo evento (mismo límite ya señalado en
  `spike-fase1/RESULTADO-gateway.md` para `OperatorEventMessage`).
- Reconexión a mitad de sesión — un evento emitido mientras un cliente estaba desconectado se
  pierde para ese cliente, igual que el resto de los mensajes WS del gateway.
- Ningún cambio en la MMI (`mmi/`) — esto llega hasta el gateway, la vista "BITE Message Window"
  de la MMI sigue sin construir.

## Sigue pendiente

Vista de BITE en la MMI (`mmi/`) que consuma `active_bite_faults` del snapshot inicial y
`BiteEventMessage` en vivo. Sin PEND nuevo — no depende de ninguna confirmación del product
expert.
