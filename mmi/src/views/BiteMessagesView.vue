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
// apaga el semáforo hasta la próxima falla nueva. Pulsar el propio semáforo
// hace lo mismo (legacy: "se resetea pulsándolo").
//
// NO construido, gap real documentado aquí en vez de fabricado:
// - Columna "radar de origen": sistema de un solo radar, siempre estaría
//   vacía -- sin valor.
// - "Auto-limpiar al conectar con otro radar": no hay concepto de radar
//   distinto en este sistema.
import { computed, onMounted, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import TrafficLight from '@/components/domain/TrafficLight.vue'
import { useGateway } from '@/composables/useGateway'
import { providePanelExportData } from '@/composables/usePanelExport'
import { exportToJson } from '@/lib/exportUtils'
import type { BiteEventMessage } from '@/types/mmi'

const { biteFaults, messages, alarmWorst, alarmCount, acknowledgeAlarm, fetchStatus } = useGateway()

const showResolved = ref(false)

// Historial de transiciones -- comparte el ring buffer de 200 mensajes de
// `messages` con eventos/antena/sesión, así que no es un archivo BiTE
// completo, es lo que quepa en esa ventana.
const history = computed<BiteEventMessage[]>(() =>
  messages.value.filter((m): m is BiteEventMessage => m.type === 'bite_event'),
)

providePanelExportData(() => history.value)

// "Limpiar tabla" es sólo de vista: el ring buffer real (`messages`) es
// compartido con A5/A6/Control Center, así que no se puede vaciar sin
// romper esas vistas. Se guarda un corte de tiempo local y se ocultan las
// filas anteriores -- reversible con "Mostrar resueltas" desde cero al
// recargar, no hay endpoint de borrado real que respaldar.
const clearedBefore = ref<string | null>(null)

// FindBar: "buscar patrón" con respaldo real es filtrar filas por
// signal_id/titular -- no se fabrica un "siguiente" tipo editor de texto
// (no hay cursor sobre una única fila, todas las coincidencias ya se ven a
// la vez en la tabla filtrada).
const query = ref('')

type SortKey = 'level' | 'signal_id' | 'at_wall' | 'detail'
const sortKey = ref<SortKey>('at_wall')
const sortDir = ref<'asc' | 'desc'>('desc')

function toggleSort(key: SortKey) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'asc'
  }
}

function sortValue(m: BiteEventMessage, key: SortKey): string {
  if (key === 'level') return m.transition
  return m[key]
}

const selected = ref<BiteEventMessage | null>(null)

// "activas" = signal_id sigue en biteFaults AHORA, no "esta fila es una
// transición de tipo fault" -- una falla que ya se resolvió deja una fila
// `fault` en el historial, y esa fila no debe contar como activa sólo
// porque su `transition` diga 'fault' (bug real, atrapado viendo esta
// vista en Storybook con datos de ejemplo: ant.servo_ok_status se resolvió
// pero su fila de fault seguía apareciendo con "Mostrar resueltas" apagado).
const rows = computed(() => {
  const q = query.value.trim().toLowerCase()
  const filtered = history.value.filter((m) => {
    if (!(showResolved.value || biteFaults.value.has(m.signal_id))) return false
    if (clearedBefore.value !== null && m.at_wall <= clearedBefore.value) return false
    if (q && !m.signal_id.toLowerCase().includes(q) && !m.detail.toLowerCase().includes(q)) return false
    return true
  })
  const dir = sortDir.value === 'asc' ? 1 : -1
  return filtered.sort((a, b) => sortValue(a, sortKey.value).localeCompare(sortValue(b, sortKey.value)) * dir)
})

function clearTable() {
  clearedBefore.value = new Date().toISOString()
  selected.value = null
}

function downloadHistory() {
  // El catálogo exige exportar todo el historial sin filtrar ("guarda todo, ignorando el filtro")
  const ts = new Date().toISOString().replace(/[:.]/g, '-')
  exportToJson(history.value, `bite_history_${ts}.json`)
}

onMounted(() => {
  fetchStatus().catch(() => {
    // WS ya en autoReconnect -- si el snapshot inicial falla, el estado
    // sigue llegando por bite_event en cuanto el WS conecte.
  })
})
</script>

<script lang="ts">
function sortArrow(active: boolean, dir: 'asc' | 'desc') {
  if (!active) return ''
  return dir === 'asc' ? '▲' : '▼'
}
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-2">
    <div class="flex flex-wrap items-center gap-2">
      <TrafficLight :worst="alarmWorst" clickable @click="acknowledgeAlarm" />
      <span class="text-xs text-muted-foreground">{{ alarmCount }} falla(s) activa(s)</span>
      <Button size="sm" variant="outline" @click="acknowledgeAlarm">Confirmar error</Button>
      <Input v-model="query" placeholder="Buscar signal_id / titular…" class="h-8 w-48 text-xs" />
      <Button size="sm" variant="outline" @click="clearTable">Limpiar tabla</Button>
      <Button size="sm" variant="outline" :disabled="history.length === 0" @click="downloadHistory">
        Guardar lista
      </Button>
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
            <th class="cursor-pointer select-none py-1 pr-2 font-medium" @click="toggleSort('level')">
              Nivel {{ sortArrow(sortKey === 'level', sortDir) }}
            </th>
            <th class="cursor-pointer select-none py-1 pr-2 font-medium" @click="toggleSort('signal_id')">
              Signal ID {{ sortArrow(sortKey === 'signal_id', sortDir) }}
            </th>
            <th class="cursor-pointer select-none py-1 pr-2 font-medium" @click="toggleSort('at_wall')">
              Fecha {{ sortArrow(sortKey === 'at_wall', sortDir) }}
            </th>
            <th class="cursor-pointer select-none py-1 font-medium" @click="toggleSort('detail')">
              Titular {{ sortArrow(sortKey === 'detail', sortDir) }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(m, i) in rows"
            :key="`${m.signal_id}-${m.at_wall}-${i}`"
            class="cursor-pointer border-t border-border hover:bg-accent"
            :class="{ 'bg-accent': selected === m }"
            @click="selected = m"
          >
            <td class="py-1 pr-2">
              <Badge :variant="m.transition === 'fault' ? 'destructive' : 'secondary'">
                {{ m.transition === 'fault' ? 'error' : 'resuelto' }}
              </Badge>
            </td>
            <td class="py-1 pr-2 font-medium">{{ m.signal_id }}</td>
            <td class="py-1 pr-2 text-muted-foreground">{{ new Date(m.at_wall).toLocaleString() }}</td>
            <td class="max-w-0 truncate py-1">{{ m.detail }}</td>
          </tr>
        </tbody>
      </table>
    </ScrollArea>

    <div v-if="selected" class="rounded-md border border-border bg-card p-2 text-xs">
      <p class="font-medium">{{ selected.signal_id }} — {{ new Date(selected.at_wall).toLocaleString() }}</p>
      <p class="text-muted-foreground">{{ selected.detail }}</p>
    </div>

    <p class="text-xs text-muted-foreground">
      Fallas activas ahora: {{ [...biteFaults.values()].map((f) => f.signal_id).join(', ') || 'ninguna' }}
    </p>
  </div>
</template>
