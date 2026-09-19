<script setup lang="ts">
// A6 Alarm/Indicator Bar: "no es un punto gris de 6 px". El detalle
// (ej. tasa real de transferencia) va en el `title` nativo -- basta para el
// "al pasar el ratón aparece el detalle" del inventario sin sumar una
// dependencia de Tooltip que hoy no existe en ui/.
import { computed } from 'vue'
import type { LampState } from '@/types/shell'

const props = defineProps<{
  label: string
  state: LampState
  detail?: string
}>()

const dotClass = computed(() => ({
  'bg-state-ok': props.state === 'ok',
  'bg-state-disabled': props.state === 'neutral',
  'bg-state-fault': props.state === 'fault',
}))
</script>

<template>
  <span
    class="inline-flex items-center gap-1.5 rounded-md border border-border px-1.5 py-0.5 text-xs"
    :title="detail"
  >
    <span class="size-2 rounded-full" :class="dotClass" />
    <span class="font-medium tabular-nums">{{ label }}</span>
  </span>
</template>
