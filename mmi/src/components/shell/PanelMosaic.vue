<script setup lang="ts">
// Zona de trabajo de A1: 1 a 4 paneles. `layout` fija la geometría, cada
// panel se pasa por slot con nombre ('a'..'d') para no depender del orden
// de hijos por defecto. Sólo usa fr/minmax(0,1fr): nada aquí impone un
// min-width mayor que el ancho de referencia estrecho (~960px a cuatro
// paneles, docs/diseno/inventario-ui.md "Densidad alta"), así que el
// cuadrante más chico de un `quad` en ese ancho sigue siendo ~480x240 sin
// que el grid lo fuerce a desbordar.
import { computed } from 'vue'
import type { MosaicLayout } from '@/types/shell'

const props = defineProps<{
  layout: MosaicLayout
}>()

const AREAS: Record<MosaicLayout, string[]> = {
  single: ['"a"'],
  'split-h': ['"a b"'],
  'split-v': ['"a"', '"b"'],
  'triple-left': ['"a b"', '"a c"'],
  quad: ['"a b"', '"c d"'],
}

const COLUMNS: Record<MosaicLayout, string> = {
  single: 'minmax(0, 1fr)',
  'split-h': 'minmax(0, 1fr) minmax(0, 1fr)',
  'split-v': 'minmax(0, 1fr)',
  'triple-left': 'minmax(0, 1fr) minmax(0, 1fr)',
  quad: 'minmax(0, 1fr) minmax(0, 1fr)',
}

const ROWS: Record<MosaicLayout, string> = {
  single: 'minmax(0, 1fr)',
  'split-h': 'minmax(0, 1fr)',
  'split-v': 'minmax(0, 1fr) minmax(0, 1fr)',
  'triple-left': 'minmax(0, 1fr) minmax(0, 1fr)',
  quad: 'minmax(0, 1fr) minmax(0, 1fr)',
}

const gridStyle = computed(() => ({
  display: 'grid',
  gridTemplateAreas: AREAS[props.layout].join(' '),
  gridTemplateColumns: COLUMNS[props.layout],
  gridTemplateRows: ROWS[props.layout],
  gap: '0.5rem',
}))

const slotNames = computed(() => ['a', 'b', 'c', 'd'].slice(0, new Set(AREAS[props.layout].join('').match(/[a-d]/g)).size))
</script>

<template>
  <div class="min-h-0 flex-1 p-2" :style="gridStyle">
    <div v-for="name in slotNames" :key="name" :style="{ gridArea: name, minWidth: 0, minHeight: 0 }">
      <slot :name="name" />
    </div>
  </div>
</template>
