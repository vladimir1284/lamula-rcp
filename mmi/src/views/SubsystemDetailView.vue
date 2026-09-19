<script setup lang="ts">
// B2 Subsystem Detail (docs/diseno/inventario-ui.md) -- "camino 1a"
// (decisión del usuario, mismo patrón camino1/camino2 de pasos previos):
// grilla de lámparas por señal digital del catálogo BITE espejado en
// @/lib/biteCatalog.ts (ver ese fichero para el porqué del espejo y su
// riesgo de desincronización).
//
// Documentado en vez de construido, por falta de respaldo real:
// - Clases "analógico-digital" / "analógico": ninguna señal analógica está
//   monitoreada hoy (core/bite/manager.py sólo lee `read_digital`).
// - "Botón derecho -> excluir del agregado" y "checkbox + botón -> abre B3":
//   el propio inventario las marca como "decidir si conservamos" -- no se
//   inventan sin esa decisión de producto.
// - Abrir esta vista al pulsar un subsistema en B1: AppShell/PanelMosaic no
//   tiene hoy un mecanismo de "un panel navega a otro" (types/shell.ts sólo
//   modela selección manual de vista por panel) -- se navega por selector de
//   subsistema dentro de esta misma vista en su lugar.
// - Distinción ACU/LCU "no operativos" del legacy: el backend sólo expone un
//   `hal_connected` global (sin ACU/LCU por separado), así que ese único
//   flag decide `stale` para las 4 subsistemas por igual.
import { computed, onMounted, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import StatusLampGrid from '@/components/domain/StatusLampGrid.vue'
import { BITE_CATALOG, SUBSYSTEM_LABELS, subsystemOf } from '@/lib/biteCatalog'
import { useGateway } from '@/composables/useGateway'

const { biteFaults, halConnected, fetchStatus } = useGateway()

const subsystemKeys = Object.keys(SUBSYSTEM_LABELS)
const selected = ref(subsystemKeys[0] ?? 'sys')

const stale = computed(() => halConnected.value !== true)

const rows = computed(() => {
  const faults = biteFaults.value
  return BITE_CATALOG.filter((e) => subsystemOf(e.signalId) === selected.value).map((e) => {
    const fault = faults.get(e.signalId)
    return {
      signalId: e.signalId,
      label: e.label,
      fault: fault !== undefined,
      stale: stale.value,
      detail: fault?.detail,
    }
  })
})

const faultCount = computed(() => rows.value.filter((r) => r.fault).length)

onMounted(() => {
  fetchStatus().catch(() => {
    // WS ya en autoReconnect -- si el snapshot inicial falla, el estado
    // sigue llegando por bite_event en cuanto el WS conecte.
  })
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-3 overflow-auto p-3">
    <div class="flex flex-wrap gap-1.5">
      <Button
        v-for="key in subsystemKeys"
        :key="key"
        size="sm"
        :variant="selected === key ? 'default' : 'outline'"
        @click="selected = key"
      >
        {{ SUBSYSTEM_LABELS[key] }}
      </Button>
    </div>

    <Card>
      <CardHeader class="flex flex-row items-center justify-between space-y-0">
        <CardTitle>{{ SUBSYSTEM_LABELS[selected] }}</CardTitle>
        <div class="flex items-center gap-2">
          <Badge v-if="stale" variant="secondary">dato no actual</Badge>
          <Badge :variant="faultCount === 0 ? 'default' : 'destructive'">
            {{ faultCount === 0 ? 'sano' : `${faultCount} falla(s)` }}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <StatusLampGrid :items="rows" />
      </CardContent>
    </Card>
  </div>
</template>
