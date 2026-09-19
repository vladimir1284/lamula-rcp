<script setup lang="ts">
// B8 BiTE Messages (docs/diseno/inventario-ui.md). El backend actual sólo
// modela dos transiciones por signal_id -- fault/cleared (BiteEventMessage,
// core/bite/manager.py) -- no los tres niveles info/warn/error del legacy
// Ravis. No hay forma honesta de mostrar un filtro de tres niveles con datos
// de dos: el filtro real que sí tiene respaldo es "activas / todas
// (incluye resueltas)", que es la misma idea de fondo ("el filtro filtra la
// vista, no la captura" -- nada se pierde por tener el filtro puesto).
//
// El semáforo/"confirmar error" usa alarmAckedAt del gateway (compartido con
// el resumen de alarma de la barra global -- B8 exige estar sincronizado con
// el icono del Control Center). Confirmar no borra fallas activas, sólo
// apaga el semáforo hasta la próxima falla nueva.
import { computed, onMounted, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import TrafficLight from '@/components/domain/TrafficLight.vue'
import { useGateway } from '@/composables/useGateway'
import type { BiteEventMessage } from '@/types/mmi'

const { biteFaults, messages, alarmWorst, alarmCount, acknowledgeAlarm, fetchStatus } = useGateway()

const showResolved = ref(false)

// Historial de transiciones -- comparte el ring buffer de 200 mensajes de
// `messages` con eventos/antena/sesión, así que no es un archivo BiTE
// completo, es lo que quepa en esa ventana. Un archivo real (B9 BiTE
// Review) necesitaría su propio endpoint, fuera de alcance de este paso.
const history = computed<BiteEventMessage[]>(() =>
  messages.value.filter((m): m is BiteEventMessage => m.type === 'bite_event'),
)

// "activas" = signal_id sigue en biteFaults AHORA, no "esta fila es una
// transición de tipo fault" -- una falla que ya se resolvió deja una fila
// `fault` en el historial, y esa fila no debe contar como activa sólo
// porque su `transition` diga 'fault' (bug real, atrapado viendo esta
// vista en Storybook con datos de ejemplo: ant.servo_ok_status se resolvió
// pero su fila de fault seguía apareciendo con "Mostrar resueltas" apagado).
const rows = computed(() =>
  [...history.value]
    .filter((m) => showResolved.value || biteFaults.value.has(m.signal_id))
    .sort((a, b) => b.at_wall.localeCompare(a.at_wall)),
)

onMounted(() => {
  fetchStatus().catch(() => {
    // WS ya en autoReconnect -- si el snapshot inicial falla, el estado
    // sigue llegando por bite_event en cuanto el WS conecte.
  })
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-2">
    <div class="flex flex-wrap items-center gap-2">
      <TrafficLight :worst="alarmWorst" />
      <span class="text-xs text-muted-foreground">{{ alarmCount }} falla(s) activa(s)</span>
      <Button size="sm" variant="outline" @click="acknowledgeAlarm">Confirmar error</Button>
      <Button size="sm" :variant="showResolved ? 'default' : 'outline'" class="ml-auto" @click="showResolved = !showResolved">
        {{ showResolved ? 'Ocultar resueltas' : 'Mostrar resueltas' }}
      </Button>
    </div>

    <p v-if="rows.length === 0" class="text-sm text-muted-foreground">
      {{ showResolved ? 'Sin mensajes BiTE todavía.' : 'Sin fallas activas.' }}
    </p>
    <ScrollArea v-else class="min-h-0 flex-1">
      <table class="w-full text-left text-xs">
        <thead class="text-muted-foreground">
          <tr>
            <th class="py-1 pr-2 font-medium">Nivel</th>
            <th class="py-1 pr-2 font-medium">Signal ID</th>
            <th class="py-1 pr-2 font-medium">Fecha</th>
            <th class="py-1 font-medium">Titular</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(m, i) in rows" :key="`${m.signal_id}-${m.at_wall}-${i}`" class="border-t border-border">
            <td class="py-1 pr-2">
              <Badge :variant="m.transition === 'fault' ? 'destructive' : 'secondary'">
                {{ m.transition === 'fault' ? 'error' : 'resuelto' }}
              </Badge>
            </td>
            <td class="py-1 pr-2 font-medium">{{ m.signal_id }}</td>
            <td class="py-1 pr-2 text-muted-foreground">{{ new Date(m.at_wall).toLocaleString() }}</td>
            <td class="py-1">{{ m.detail }}</td>
          </tr>
        </tbody>
      </table>
    </ScrollArea>

    <p class="text-xs text-muted-foreground">
      Fallas activas ahora: {{ [...biteFaults.values()].map((f) => f.signal_id).join(', ') || 'ninguna' }}
    </p>
  </div>
</template>
