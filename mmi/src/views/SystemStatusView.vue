<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useGateway } from '@/composables/useGateway'

const { status, biteFaults, fetchStatus } = useGateway()

const faultsSorted = computed(() =>
  [...biteFaults.value.values()].sort((a, b) => a.signal_id.localeCompare(b.signal_id)),
)

const wsStatusVariant = computed(() => {
  if (status.value === 'OPEN') return 'default'
  if (status.value === 'CONNECTING') return 'secondary'
  return 'destructive'
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
    <h1 class="text-2xl font-semibold">System Status &amp; BITE</h1>

    <Card>
      <CardHeader>
        <CardTitle>Conexión al gateway</CardTitle>
      </CardHeader>
      <CardContent class="flex flex-wrap items-center gap-3">
        <Badge :variant="wsStatusVariant">WS {{ status }}</Badge>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Fallas activas ({{ faultsSorted.length }})</CardTitle>
      </CardHeader>
      <CardContent>
        <p v-if="faultsSorted.length === 0" class="text-sm text-muted-foreground">
          Ninguna falla activa.
        </p>
        <ScrollArea v-else class="h-96 w-full">
          <ul class="flex flex-col gap-2 text-sm">
            <li
              v-for="fault in faultsSorted"
              :key="fault.signal_id"
              class="flex flex-wrap items-center gap-2 border-b pb-2"
            >
              <Badge variant="destructive">{{ fault.signal_id }}</Badge>
              <span class="text-muted-foreground">{{ fault.detail }}</span>
              <span class="text-xs text-muted-foreground">
                desde {{ new Date(fault.since_wall).toLocaleTimeString() }}
              </span>
            </li>
          </ul>
        </ScrollArea>
      </CardContent>
    </Card>
  </div>
</template>
