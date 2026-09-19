<script setup lang="ts">
// A2 Connection / Login (docs/diseno/inventario-ui.md) -- "camino 1"
// (decisión del usuario, mismo patrón que paso 4 D2-D4): esta vista sólo
// expone lo que el gateway soporta hoy, no lo que RAVIS §6.1 describe.
//
// Lo que el inventario pide y NO existe todavía, documentado en vez de
// inventado:
// - Destino real/simulador: se decide hoy por qué HAL arranca el proceso
//   RCP (backend), no algo que el operador conmute desde la MMI.
// - Host/puerto: `GATEWAY_HTTP`/`GATEWAY_WS` en useGateway.ts son fijos a
//   localhost:8000 -- no hay empaquetado/despliegue decidido aún.
// - "Rechazado" / "versión incompatible": el mensaje `session` del
//   contrato (core/contracts/mmi.py) sólo manda `rcp_version` como texto,
//   sin negociación ni chequeo de compatibilidad del lado del gateway.
//
// Lo que sí es real: los 3 estados de `useWebSocket`
// (CONNECTING/OPEN/CLOSED), reconexión manual (open/close, ya expuestos por
// useGateway) sobre el autoReconnect automático existente, y el motivo del
// último cierre cuando el navegador lo entrega (`lastCloseReason` --
// best-effort, `CloseEvent.reason` suele venir vacío en cortes de red).
import { computed } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import ConnectionStatusBadge from '@/components/domain/ConnectionStatusBadge.vue'
import { useGateway } from '@/composables/useGateway'

const { status, lastCloseReason, sessionInfo, open, close } = useGateway()

const isOpen = computed(() => status.value === 'OPEN')
const isConnecting = computed(() => status.value === 'CONNECTING')
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-3">
    <Card>
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          Conexión con el RCP
          <ConnectionStatusBadge :status="status" label="gateway" />
        </CardTitle>
      </CardHeader>
      <CardContent class="flex flex-col gap-3">
        <div v-if="isOpen && sessionInfo" class="text-sm text-muted-foreground">
          RCP {{ sessionInfo.rcp_version }} -- en línea desde
          {{ new Date(sessionInfo.started_at_wall).toLocaleTimeString() }}
        </div>
        <p v-else-if="isConnecting" class="text-sm text-muted-foreground">Conectando...</p>
        <p v-else class="text-sm text-destructive">
          Sin conexión<template v-if="lastCloseReason">: {{ lastCloseReason }}</template>
        </p>

        <div class="flex gap-2">
          <Button v-if="!isOpen" :disabled="isConnecting" @click="open">Conectar</Button>
          <Button v-else variant="outline" @click="close">Desconectar</Button>
        </div>

        <p class="text-xs text-muted-foreground">
          Reintento automático activo en segundo plano
          (<Badge variant="secondary" class="align-middle">autoReconnect</Badge>);
          estos botones fuerzan un ciclo manual.
        </p>
      </CardContent>
    </Card>
  </div>
</template>
