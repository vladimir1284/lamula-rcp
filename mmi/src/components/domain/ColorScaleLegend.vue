<script setup lang="ts">
// Leyenda de escala de color para D3/D4 (PPI/RHI). Gradiente CSS puro sobre
// los mismos custom properties de main.css (D6) -- a diferencia del canvas
// del plot, un `linear-gradient(var(--x), ...)` en CSS sí resuelve el token
// sin pasar por JS.
import { computed } from 'vue'
import { paletteVars } from '@/lib/dataPalette'
import type { DataKind } from '@/lib/mockRadar'

const props = defineProps<{ kind: DataKind }>()

const gradient = computed(() => `linear-gradient(to top, ${paletteVars(props.kind).map((v) => `var(${v})`).join(', ')})`)
const isSigned = computed(() => props.kind === 'velocity')
</script>

<template>
  <div class="flex h-full flex-col items-center gap-1 text-[10px] text-muted-foreground">
    <span>{{ isSigned ? '+' : 'max' }}</span>
    <div class="w-3 flex-1 rounded-sm" :style="{ background: gradient }" />
    <span>{{ isSigned ? '−' : 'min' }}</span>
  </div>
</template>
