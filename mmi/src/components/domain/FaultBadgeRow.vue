<script setup lang="ts">
// Fila de falla BITE -- antes dos layouts casi iguales sobre el mismo dato
// (BiteFaultSummary): agrupado por subsistema en SystemVisualizationView.vue
// (signal_id en texto plano) y lista plana ordenada en SystemStatusView.vue
// (signal_id como Badge + timestamp). `asBadge`/`showTimestamp` cubren las
// dos. El agrupado/orden sigue siendo de cada vista -- eso no es
// presentacional, es layout propio de cada pantalla.
import type { BiteFaultSummary } from '@/types/mmi'
import { Badge } from '@/components/ui/badge'

withDefaults(
  defineProps<{
    fault: BiteFaultSummary
    asBadge?: boolean
    showTimestamp?: boolean
  }>(),
  { asBadge: false, showTimestamp: false },
)
</script>

<template>
  <div class="flex flex-wrap items-center gap-2">
    <Badge v-if="asBadge" variant="destructive">{{ fault.signal_id }}</Badge>
    <span v-else class="font-medium">{{ fault.signal_id }}</span>
    <span class="text-muted-foreground">{{ fault.detail }}</span>
    <span v-if="showTimestamp" class="text-xs text-muted-foreground">
      desde {{ new Date(fault.since_wall).toLocaleTimeString() }}
    </span>
  </div>
</template>
