<script setup lang="ts">
// Leyenda de escala de color para D3/D4 (PPI/RHI). Gradiente CSS continuo sobre
// la escala activa (resuelta mediante buildActiveScale / customScale) -- D6
import { computed } from 'vue'
import { buildActiveScale } from '@/lib/dataPalette'
import type { DataKind } from '@/lib/mockRadar'

const props = defineProps<{
  kind: DataKind
  customScale?: string[]
}>()

const activeScale = computed<string[]>(() => {
  if (props.customScale && props.customScale.length > 0) {
    return props.customScale
  }
  return buildActiveScale(props.kind, 64)
})

const gradient = computed(() => {
  const colors = activeScale.value
  if (colors.length === 0) return 'none'
  return `linear-gradient(to top, ${colors.join(', ')})`
})

const isSigned = computed(() => props.kind === 'velocity')
</script>

<template>
  <div class="flex h-full flex-col items-center gap-1 text-[10px] text-muted-foreground">
    <span>{{ isSigned ? '+' : 'max' }}</span>
    <div class="w-3 flex-1 rounded-sm" :style="{ background: gradient }" />
    <span>{{ isSigned ? '−' : 'min' }}</span>
  </div>
</template>
