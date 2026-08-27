<script setup lang="ts">
// Lectura en vivo de posición de antena -- antes duplicada en
// ControlCenterView.vue (abreviada, sin tasas) y AntennaControlView.vue
// (completa, con az_rate/el_rate). `showRates` distingue ambos usos.
import type { AntennaPosition } from '@/types/mmi'
import { Badge } from '@/components/ui/badge'

withDefaults(
  defineProps<{
    antenna: AntennaPosition | null
    showRates?: boolean
  }>(),
  { showRates: false },
)
</script>

<template>
  <div class="flex flex-wrap items-center gap-4 text-sm">
    <template v-if="antenna">
      <span>
        az: {{ antenna.az_deg.toFixed(2) }}°
        <template v-if="showRates">({{ antenna.az_rate_deg_s.toFixed(3) }}°/s)</template>
      </span>
      <span>
        el: {{ antenna.el_deg.toFixed(2) }}°
        <template v-if="showRates">({{ antenna.el_rate_deg_s.toFixed(3) }}°/s)</template>
      </span>
      <Badge v-if="!antenna.az_valid || !antenna.el_valid" variant="destructive">encoder inválido</Badge>
      <Badge v-if="antenna.degraded" variant="secondary">degradado</Badge>
    </template>
    <span v-else class="text-muted-foreground">sin posición todavía</span>
  </div>
</template>
