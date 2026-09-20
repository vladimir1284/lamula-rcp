<!--
  PlotCursor.vue: Cursor de inspección por desplazamiento de cursor (hover).
  Nota de diseño / cambio respecto a legacy:
  Usamos hover en lugar de clic derecho para inspeccionar el punto.
  El clic derecho es una convención de aplicaciones de escritorio Windows y en la web
  interfiere con el menú contextual nativo del navegador.
  Valores redondeados al entero más próximo solo al mostrarlos (Math.round).
-->
<script setup lang="ts">
export interface CursorChannelValue {
  signal_id: string
  color: string
  rawValue: number | null
}

defineProps<{
  x: number | null
  timeStr: string | null
  values: CursorChannelValue[]
  height: number
}>()
</script>

<template>
  <g v-if="x !== null" class="plot-cursor">
    <!-- Línea vertical del cursor -->
    <line
      :x1="x"
      :y1="0"
      :x2="x"
      :y2="height"
      stroke="hsl(var(--foreground))"
      stroke-width="1"
      stroke-dasharray="2 2"
      opacity="0.75"
    />
  </g>
</template>
