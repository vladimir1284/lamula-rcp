<script setup lang="ts">
// Componente HistoricalModeBanner (docs/diseno/inventario-ui.md, B9):
// Franja obligatoria que advierte al operador que está viendo un reporte
// guardado e histórico, no datos en vivo.
import { Badge } from '@/components/ui/badge'

defineProps<{
  fileName?: string
  totalRecords?: number
}>()
</script>

<template>
  <div class="flex flex-wrap items-center justify-between gap-2 rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-600 dark:text-amber-400">
    <div class="flex items-center gap-2">
      <Badge variant="outline" class="border-amber-500 text-amber-600 dark:text-amber-400 font-semibold">
        HISTÓRICO
      </Badge>
      <span class="font-medium">Viendo reporte guardado — No tiempo real</span>
    </div>
    <div v-if="fileName || totalRecords !== undefined" class="text-muted-foreground flex items-center gap-3 text-[11px]">
      <span v-if="fileName">Archivo: {{ fileName }}</span>
      <span v-if="totalRecords !== undefined">{{ totalRecords }} registro(s)</span>
    </div>
  </div>
</template>
