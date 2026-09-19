<script setup lang="ts">
// A6: SI/SR/SD/RD. SD y RD en 'neutral' durante >5s sin datos es el origen
// documentado del estado `stale` de todo el sistema -- por eso el color
// reutiliza --state-disabled (gris) en vez de inventar un cuarto tono.
import IndicatorLamp from './IndicatorLamp.vue'
import type { IndicatorState } from '@/types/shell'

defineProps<{
  indicators: IndicatorState[]
}>()
</script>

<template>
  <div class="flex items-center gap-1.5">
    <IndicatorLamp
      v-for="ind in indicators"
      :key="ind.id"
      :label="ind.id"
      :state="ind.state"
      :detail="ind.detail"
    />
  </div>
</template>
