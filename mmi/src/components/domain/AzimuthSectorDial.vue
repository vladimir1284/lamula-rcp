<script setup lang="ts">
import type { BlankingSector } from '@/types/mmi'

const props = withDefaults(
  defineProps<{
    sectors: BlankingSector[]
    selectedIndex?: number | null
    enabled?: boolean
  }>(),
  {
    selectedIndex: null,
    enabled: true,
  },
)

const emit = defineEmits<{
  (e: 'select-sector', index: number): void
}>()

const SECTOR_COLORS = [
  '#f87171', // red-400
  '#fb923c', // orange-400
  '#facc15', // yellow-400
  '#4ade80', // green-400
  '#38bdf8', // sky-400
  '#818cf8', // indigo-400
  '#c084fc', // purple-400
  '#f472b6', // pink-400
]

function polarToCartesian(cx: number, cy: number, radius: number, angleDeg: number) {
  const rad = (angleDeg * Math.PI) / 180.0
  return {
    x: cx + radius * Math.sin(rad),
    y: cy - radius * Math.cos(rad),
  }
}

function describeAnnularSector(
  cx: number,
  cy: number,
  rIn: number,
  rOut: number,
  startDeg: number,
  endDeg: number,
): string {
  let sweep = endDeg - startDeg
  if (sweep < 0) sweep += 360
  if (sweep === 0 && startDeg !== endDeg) sweep = 360
  if (sweep >= 360) sweep = 359.999
  if (sweep <= 0.001) return ''

  const effectiveEndDeg = startDeg + sweep

  const pOutStart = polarToCartesian(cx, cy, rOut, startDeg)
  const pOutEnd = polarToCartesian(cx, cy, rOut, effectiveEndDeg)
  const pInEnd = polarToCartesian(cx, cy, rIn, effectiveEndDeg)
  const pInStart = polarToCartesian(cx, cy, rIn, startDeg)

  const largeArcFlag = sweep > 180 ? 1 : 0

  return [
    `M ${pOutStart.x.toFixed(2)} ${pOutStart.y.toFixed(2)}`,
    `A ${rOut} ${rOut} 0 ${largeArcFlag} 1 ${pOutEnd.x.toFixed(2)} ${pOutEnd.y.toFixed(2)}`,
    `L ${pInEnd.x.toFixed(2)} ${pInEnd.y.toFixed(2)}`,
    `A ${rIn} ${rIn} 0 ${largeArcFlag} 0 ${pInStart.x.toFixed(2)} ${pInStart.y.toFixed(2)}`,
    'Z',
  ].join(' ')
}

const ticks = [
  { label: 'N', x: 150, y: 16 },
  { label: 'E', x: 284, y: 150 },
  { label: 'S', x: 150, y: 284 },
  { label: 'W', x: 16, y: 150 },
]
</script>

<template>
  <div class="relative flex flex-col items-center justify-center p-2">
    <svg
      viewBox="0 0 300 300"
      class="h-64 w-64 select-none"
      :class="{ 'opacity-50': !enabled }"
    >
      <!-- Background Circles -->
      <circle cx="150" cy="150" r="125" class="fill-muted/10 stroke-border" stroke-width="1.5" />
      <circle cx="150" cy="150" r="60" class="fill-background stroke-border" stroke-width="1.5" />

      <!-- Sector Arc Segments -->
      <g v-for="(sec, i) in sectors" :key="i">
        <path
          v-if="sec.az_start_deg !== sec.az_end_deg || sec.in_use"
          :d="describeAnnularSector(150, 150, 62, 123, sec.az_start_deg, sec.az_end_deg)"
          :fill="sec.in_use ? SECTOR_COLORS[i % SECTOR_COLORS.length] : 'currentColor'"
          :fill-opacity="sec.in_use ? (selectedIndex === i ? '0.75' : '0.45') : '0.05'"
          :stroke="sec.in_use ? SECTOR_COLORS[i % SECTOR_COLORS.length] : 'currentColor'"
          :stroke-opacity="sec.in_use ? '0.9' : '0.2'"
          :stroke-width="selectedIndex === i ? '2.5' : '1.5'"
          class="cursor-pointer transition-all hover:fill-opacity-70"
          @click="emit('select-sector', i)"
        />
      </g>

      <!-- Center Circle -->
      <circle cx="150" cy="150" r="60" class="fill-card/80 stroke-border" stroke-width="1" />

      <!-- Compass Ticks and Labels -->
      <g v-for="t in ticks" :key="t.label">
        <text
          :x="t.x"
          :y="t.y"
          text-anchor="middle"
          dominant-baseline="central"
          class="fill-muted-foreground text-[10px] font-bold"
        >
          {{ t.label }}
        </text>
      </g>

      <!-- Center Text -->
      <text
        x="150"
        y="142"
        text-anchor="middle"
        class="fill-foreground text-xs font-semibold"
      >
        AZ Sector Dial
      </text>
      <text
        x="150"
        y="160"
        text-anchor="middle"
        class="fill-muted-foreground text-[10px]"
      >
        {{ enabled ? 'Sector Blanking Active' : 'Blanking Off' }}
      </text>
    </svg>
  </div>
</template>
