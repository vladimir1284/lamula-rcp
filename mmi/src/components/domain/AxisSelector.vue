<script setup lang="ts">
// Selector de eje az/el -- antes duplicado dos veces dentro de
// AntennaControlView.vue (panel Jog y panel Posicionar).
import type { AntennaAxis } from '@/types/mmi'

defineProps<{
  modelValue: AntennaAxis
}>()

defineEmits<{
  'update:modelValue': [value: AntennaAxis]
}>()
</script>

<template>
  <div class="flex flex-wrap items-center gap-3 text-sm">
    <label class="flex items-center gap-1">
      <input
        type="radio"
        value="azimuth"
        :checked="modelValue === 'azimuth'"
        @change="$emit('update:modelValue', 'azimuth')"
      >
      azimut
    </label>
    <label class="flex items-center gap-1">
      <input
        type="radio"
        value="elevation"
        :checked="modelValue === 'elevation'"
        @change="$emit('update:modelValue', 'elevation')"
      >
      elevación
    </label>
  </div>
</template>
