<script setup lang="ts">
export interface MarkerInfo {
  x: number
  timeStr: string
  gapDurationS: number
}

defineProps<{
  markers: MarkerInfo[]
  height: number
}>()
</script>

<template>
  <g class="time-markers">
    <g v-for="(m, idx) in markers" :key="idx">
      <!-- Línea vertical discontinua -->
      <line
        :x1="m.x"
        :y1="0"
        :x2="m.x"
        :y2="height"
        stroke="hsl(var(--destructive))"
        stroke-width="1.5"
        stroke-dasharray="4 3"
        opacity="0.85"
      />
      <!-- Etiqueta del gap -->
      <rect
        :x="m.x - 32"
        :y="8"
        width="64"
        height="18"
        rx="3"
        fill="hsl(var(--background))"
        stroke="hsl(var(--destructive))"
        stroke-width="1"
      />
      <text
        :x="m.x"
        :y="20"
        text-anchor="middle"
        font-size="9"
        fill="hsl(var(--destructive))"
        font-family="monospace"
        font-weight="bold"
      >
        GAP {{ m.gapDurationS.toFixed(1) }}s
      </text>
    </g>
  </g>
</template>
