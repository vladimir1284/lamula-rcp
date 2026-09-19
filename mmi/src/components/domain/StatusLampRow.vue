<script setup lang="ts">
// B2 Subsystem Detail: una fila = una señal digital del catálogo BITE
// (@/lib/biteCatalog). Sólo hay clase "digital" con respaldo real -- ver
// comentario en biteCatalog.ts. `title` nativo para el tooltip, mismo
// criterio que IndicatorLamp.vue (A6): no hay Tooltip en components/ui/.
import { computed } from 'vue'

const props = defineProps<{
  label: string
  signalId: string
  fault: boolean
  stale: boolean
  detail?: string
}>()

const dotClass = computed(() => ({
  'bg-state-fault': props.fault,
  'bg-state-ok': !props.fault,
  'is-stale': props.stale,
}))

const tooltip = computed(() => {
  const parts = [props.signalId]
  if (props.detail) parts.push(props.detail)
  if (props.stale) parts.push('dato no actual (HAL sin conexión)')
  return parts.join(' -- ')
})
</script>

<template>
  <div class="flex items-center gap-2 py-0.5 text-sm" :title="tooltip">
    <span class="size-2.5 shrink-0 rounded-full" :class="dotClass" />
    <span class="truncate">{{ label }}</span>
  </div>
</template>
