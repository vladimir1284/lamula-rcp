<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import FaultBadgeRow from '@/components/domain/FaultBadgeRow.vue'
import { useGateway } from '@/composables/useGateway'

const { biteFaults, fetchStatus } = useGateway()

// Mismo criterio de subsistema que core/bite/manager.py (prefijo de signal_id
// antes del primer punto) -- no hay metadato de severidad en el catalogo, asi
// que la unica agrupacion con respaldo real es por subsistema.
const SUBSYSTEMS = [
  { key: 'sys', label: 'Sistema' },
  { key: 'tx', label: 'Transmisor' },
  { key: 'rx', label: 'Receptor' },
  { key: 'ant', label: 'Antena' },
] as const

const subsystemFaults = computed(() => {
  const faults = [...biteFaults.value.values()]
  return SUBSYSTEMS.map((s) => ({
    ...s,
    faults: faults.filter((f) => f.signal_id.split('.', 1)[0] === s.key),
  }))
})

onMounted(() => {
  fetchStatus().catch(() => {
    // WS ya en autoReconnect -- si el snapshot inicial falla, el estado
    // sigue llegando por bite_event en cuanto el WS conecte.
  })
})
</script>

<template>
  <div class="mx-auto flex max-w-3xl flex-col gap-4 p-6">
    <h1 class="text-2xl font-semibold">System Visualization</h1>

    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <Card v-for="s in subsystemFaults" :key="s.key">
        <CardHeader class="flex flex-row items-center justify-between space-y-0">
          <CardTitle>{{ s.label }}</CardTitle>
          <Badge :variant="s.faults.length === 0 ? 'default' : 'destructive'">
            {{ s.faults.length === 0 ? 'sano' : `${s.faults.length} falla(s)` }}
          </Badge>
        </CardHeader>
        <CardContent>
          <p v-if="s.faults.length === 0" class="text-sm text-muted-foreground">
            Sin fallas activas.
          </p>
          <ul v-else class="flex flex-col gap-1 text-sm">
            <li v-for="f in s.faults" :key="f.signal_id">
              <FaultBadgeRow :fault="f" />
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
