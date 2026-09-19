<script setup lang="ts">
// B8: "icono de tres luces que refleja la peor condición recibida" --
// reutiliza los mismos tokens --state-* que IndicatorLamp (shell/), no
// inventa un cuarto set de colores para lo que es la misma semántica ok/
// advertencia/fallo ya resuelta en el paso 1 (sistema de color).
import type { LampState } from '@/types/shell'

withDefaults(
  defineProps<{
    worst: LampState
    clickable?: boolean
  }>(),
  { clickable: false },
)

defineEmits<{ click: [] }>()

const COLOR: Record<LampState, string> = {
  ok: 'bg-state-ok',
  neutral: 'bg-state-disabled',
  fault: 'bg-state-fault',
}
</script>

<template>
  <component
    :is="clickable ? 'button' : 'div'"
    class="inline-flex items-center gap-1 rounded-md border border-border bg-card px-1.5 py-1"
    :type="clickable ? 'button' : undefined"
    @click="clickable && $emit('click')"
  >
    <span
      v-for="s in (['fault', 'neutral', 'ok'] as const)"
      :key="s"
      class="h-2.5 w-2.5 rounded-full"
      :class="s === worst ? COLOR[s] : 'bg-border'"
    />
  </component>
</template>
