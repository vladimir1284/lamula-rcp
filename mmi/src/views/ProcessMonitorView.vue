<!--
  ProcessMonitorView.vue: Vista B5 — Monitor de Procesos y Tareas del RCP.
  Gaps documentados:
  1. El RCP corre como un solo proceso asyncio; la vista muestra el proceso real
     (PID/prioridad) y sus tareas internas, sin fabricar procesos falsos del SO (diferencia con RVP900 V).
  2. Las tareas asyncio son cooperativas y no poseen prioridad ni política de planificación (no hay RealTimeRR por tarea); esa columna se omite.
  3. El control de acceso de mantenimiento (MANT) no se aplica aún porque A4 no existe todavía; la vista permanece visible sin gate.
-->
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useGateway } from '@/composables/useGateway'
import type { ProcessMonitorSnapshot } from '@/types/mmi'

const { fetchProcessMonitor } = useGateway()

const snapshot = ref<ProcessMonitorSnapshot | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

async function refresh() {
  loading.value = true
  error.value = null
  try {
    snapshot.value = await fetchProcessMonitor()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  refresh()
})

function getTaskBadgeVariant(state: string): 'default' | 'destructive' | 'secondary' | 'outline' {
  if (state === 'pending') return 'default'
  if (state === 'cancelled') return 'destructive'
  return 'secondary'
}
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 overflow-auto p-3">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold text-foreground">B5 RCP Process Monitor</h2>
      <Button size="sm" :disabled="loading" @click="refresh">
        {{ loading ? 'Actualizando...' : 'Actualizar' }}
      </Button>
    </div>

    <p v-if="error" class="text-xs font-medium text-destructive">
      {{ error }}
    </p>

    <!-- Sección 1: Proceso principal RCP -->
    <Card>
      <CardHeader>
        <CardTitle>Proceso Principal RCP</CardTitle>
      </CardHeader>
      <CardContent>
        <div v-if="!snapshot" class="text-xs text-muted-foreground">
          Sin datos de proceso.
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="border-b bg-muted/50 text-muted-foreground">
              <tr>
                <th class="p-2 font-medium">PID</th>
                <th class="p-2 font-medium">Nombre</th>
                <th class="p-2 font-medium">Prioridad (nice)</th>
                <th class="p-2 font-medium">Estado</th>
                <th class="p-2 font-medium">CPU (%)</th>
                <th class="p-2 font-medium">Memoria (MB)</th>
              </tr>
            </thead>
            <tbody class="divide-y">
              <tr>
                <td class="p-2 font-mono">{{ snapshot.process.pid }}</td>
                <td class="p-2 font-medium">{{ snapshot.process.name }}</td>
                <td class="p-2 font-mono">{{ snapshot.process.priority }}</td>
                <td class="p-2">
                  <Badge variant="default">
                    {{ snapshot.process.status }}
                  </Badge>
                </td>
                <td class="p-2 font-mono">{{ snapshot.process.cpu_percent.toFixed(1) }}%</td>
                <td class="p-2 font-mono">{{ snapshot.process.memory_mb.toFixed(1) }} MB</td>
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>

    <!-- Sección 2: Tareas internas (asyncio) -->
    <Card>
      <CardHeader>
        <CardTitle class="flex items-center justify-between">
          <span>Tareas Internas (asyncio)</span>
          <span v-if="snapshot" class="text-xs font-normal text-muted-foreground">
            {{ snapshot.tasks.length }} tarea(s)
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div v-if="!snapshot" class="text-xs text-muted-foreground">
          Sin datos de tareas.
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="border-b bg-muted/50 text-muted-foreground">
              <tr>
                <th class="p-2 font-medium">Nombre de Tarea</th>
                <th class="p-2 font-medium">Estado</th>
              </tr>
            </thead>
            <tbody class="divide-y">
              <tr v-for="t in snapshot.tasks" :key="t.name">
                <td class="p-2 font-mono">{{ t.name }}</td>
                <td class="p-2">
                  <Badge :variant="getTaskBadgeVariant(t.state)">
                    {{ t.state === 'pending' ? 'corriendo' : t.state }}
                  </Badge>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
