<!--
  TrendChart.vue: Gráfico de tendencias SVG (sin dependencias externas).
  Renderiza polilíneas por canal, marcadores de tiempo en saltos >1.5s (TimeMarker)
  y lectura con hover de cursor (PlotCursor).
  Valores redondeados al entero más cercano con Math.round() solo al mostrarlos en pantalla.
-->
<script setup lang="ts">
import { computed, ref } from 'vue'
import PlotCursor, { type CursorChannelValue } from '@/components/domain/PlotCursor.vue'
import TimeMarker, { type MarkerInfo } from '@/components/domain/TimeMarker.vue'
import type { TrendSeries } from '@/types/mmi'

const props = defineProps<{
  series: TrendSeries[]
}>()

const CHANNEL_COLORS = [
  '#3b82f6', // blue
  '#ef4444', // red
  '#10b981', // green
  '#f59e0b', // amber
  '#8b5cf6', // purple
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#84cc16', // lime
]

const svgWidth = 800
const svgHeight = 280
const padding = { top: 20, right: 20, bottom: 35, left: 55 }

const plotW = computed(() => svgWidth - padding.left - padding.right)
const plotH = computed(() => svgHeight - padding.top - padding.bottom)

// Muestras aplanadas para cálculo de límites
const allSamples = computed(() =>
  props.series.flatMap((s) => s.samples.map((samp) => ({ ...samp, signal_id: s.signal_id }))),
)

const timeBounds = computed(() => {
  if (allSamples.value.length === 0) {
    const now = Date.now()
    return { min: now - 10000, max: now }
  }
  const times = allSamples.value.map((s) => new Date(s.at_wall).getTime())
  let min = Math.min(...times)
  let max = Math.max(...times)
  if (max === min) max = min + 1000
  return { min, max }
})

const valueBounds = computed(() => {
  const vals = allSamples.value.map((s) => s.value).filter((v): v is number => v !== null)
  if (vals.length === 0) return { min: 0, max: 100 }
  let min = Math.min(...vals)
  let max = Math.max(...vals)
  if (min === max) {
    min -= 1
    max += 1
  }
  const pad = (max - min) * 0.1
  return { min: min - pad, max: max + pad }
})

function getX(timeIso: string): number {
  const t = new Date(timeIso).getTime()
  const span = timeBounds.value.max - timeBounds.value.min
  const ratio = (t - timeBounds.value.min) / span
  return padding.left + ratio * plotW.value
}

function getY(val: number): number {
  const span = valueBounds.value.max - valueBounds.value.min
  const ratio = (val - valueBounds.value.min) / span
  return padding.top + (1 - ratio) * plotH.value
}

// Genera polilíneas por canal. Si hay un sample con value === null, divide la serie en segmentos.
const channelLines = computed(() => {
  return props.series.map((s, idx) => {
    const color = CHANNEL_COLORS[idx % CHANNEL_COLORS.length]
    const segments: string[] = []
    let currentPoints: string[] = []

    s.samples.forEach((samp) => {
      if (samp.value === null) {
        if (currentPoints.length > 0) {
          segments.push(currentPoints.join(' '))
          currentPoints = []
        }
      } else {
        const x = getX(samp.at_wall)
        const y = getY(samp.value)
        currentPoints.push(`${x.toFixed(1)},${y.toFixed(1)}`)
      }
    })
    if (currentPoints.length > 0) {
      segments.push(currentPoints.join(' '))
    }

    return {
      signal_id: s.signal_id,
      color,
      segments,
    }
  })
})

// Detecta saltos de tiempo (gaps > 1.5 s)
const timeMarkers = computed<MarkerInfo[]>(() => {
  const markers: MarkerInfo[] = []
  if (props.series.length === 0) return markers

  const samples = props.series[0]?.samples
  if (!samples) return markers

  for (let i = 0; i < samples.length - 1; i++) {
    const s1 = samples[i]
    const s2 = samples[i + 1]
    if (!s1 || !s2) continue
    const t1 = new Date(s1.at_wall).getTime()
    const t2 = new Date(s2.at_wall).getTime()
    const gapS = (t2 - t1) / 1000
    if (gapS > 1.5) {
      const x1 = getX(s1.at_wall)
      const x2 = getX(s2.at_wall)
      const xMid = (x1 + x2) / 2
      const timeStr = new Date(t2).toLocaleTimeString()
      markers.push({ x: xMid, timeStr, gapDurationS: gapS })
    }
  }
  return markers
})

// Interacción de Hover / Cursor
const cursorX = ref<number | null>(null)
const cursorTimeStr = ref<string | null>(null)
const cursorValues = ref<CursorChannelValue[]>([])

function onMouseMove(event: MouseEvent) {
  const svgEl = event.currentTarget as SVGSVGElement
  const rect = svgEl.getBoundingClientRect()
  const mouseX = event.clientX - rect.left
  const svgX = (mouseX / rect.width) * svgWidth

  if (svgX < padding.left || svgX > svgWidth - padding.right) {
    cursorX.value = null
    cursorTimeStr.value = null
    cursorValues.value = []
    return
  }

  cursorX.value = svgX
  const ratio = (svgX - padding.left) / plotW.value
  const targetMs = timeBounds.value.min + ratio * (timeBounds.value.max - timeBounds.value.min)
  cursorTimeStr.value = new Date(targetMs).toLocaleTimeString()

  // Buscar muestra más cercana en cada canal
  cursorValues.value = props.series.map((s, idx) => {
    const color = CHANNEL_COLORS[idx % CHANNEL_COLORS.length] ?? '#3b82f6'
    let closestVal: number | null = null
    let minDiff = Infinity

    s.samples.forEach((samp) => {
      const diff = Math.abs(new Date(samp.at_wall).getTime() - targetMs)
      if (diff < minDiff) {
        minDiff = diff
        closestVal = samp.value
      }
    })

    return {
      signal_id: s.signal_id,
      color,
      rawValue: closestVal,
    }
  })
}

function onMouseLeave() {
  cursorX.value = null
  cursorTimeStr.value = null
  cursorValues.value = []
}

// Marcas de eje Y
const yTicks = computed(() => {
  const { min, max } = valueBounds.value
  const steps = 4
  const ticks = []
  for (let i = 0; i <= steps; i++) {
    const val = min + (i / steps) * (max - min)
    const y = getY(val)
    ticks.push({ val, y })
  }
  return ticks
})

// Marcas de eje X (tiempo)
const xTicks = computed(() => {
  const { min, max } = timeBounds.value
  const steps = 4
  const ticks = []
  for (let i = 0; i <= steps; i++) {
    const t = min + (i / steps) * (max - min)
    const ratio = i / steps
    const x = padding.left + ratio * plotW.value
    const label = new Date(t).toLocaleTimeString()
    ticks.push({ label, x })
  }
  return ticks
})
</script>

<template>
  <div class="flex flex-col gap-3">
    <!-- Leyenda e Inspector -->
    <div class="flex flex-wrap items-center justify-between gap-2 text-xs border-b pb-2">
      <div class="flex flex-wrap items-center gap-4">
        <div v-for="ch in channelLines" :key="ch.signal_id" class="flex items-center gap-1.5 font-mono">
          <span class="h-3 w-3 rounded-xs" :style="{ backgroundColor: ch.color }"></span>
          <span>{{ ch.signal_id }}:</span>
          <span class="font-bold">
            <template v-if="cursorX !== null">
              {{
                cursorValues.find((v) => v.signal_id === ch.signal_id)?.rawValue !== null
                  ? Math.round(cursorValues.find((v) => v.signal_id === ch.signal_id)?.rawValue as number)
                  : 'N/A'
              }}
            </template>
            <template v-else>
              {{
                series.find((s) => s.signal_id === ch.signal_id)?.samples.slice(-1)[0]?.value !== undefined &&
                series.find((s) => s.signal_id === ch.signal_id)?.samples.slice(-1)[0]?.value !== null
                  ? Math.round(series.find((s) => s.signal_id === ch.signal_id)?.samples.slice(-1)[0]?.value as number)
                  : 'N/A'
              }}
            </template>
          </span>
        </div>
      </div>
      <div v-if="cursorTimeStr" class="font-mono text-muted-foreground">
        Hora cursor: <span class="text-foreground font-semibold">{{ cursorTimeStr }}</span>
      </div>
    </div>

    <!-- Gráfico SVG -->
    <div class="relative w-full overflow-hidden rounded-md border bg-black/90 p-1">
      <svg
        :viewBox="`0 0 ${svgWidth} ${svgHeight}`"
        class="w-full h-auto cursor-crosshair select-none"
        @mousemove="onMouseMove"
        @mouseleave="onMouseLeave"
      >
        <!-- Rejilla de Fondo -->
        <g stroke="rgba(255,255,255,0.08)" stroke-width="1">
          <line v-for="t in yTicks" :key="t.y" :x1="padding.left" :y1="t.y" :x2="svgWidth - padding.right" :y2="t.y" />
          <line v-for="t in xTicks" :key="t.x" :x1="t.x" :y1="padding.top" :x2="t.x" :y2="svgHeight - padding.bottom" />
        </g>

        <!-- Ejes -->
        <g stroke="rgba(255,255,255,0.3)" stroke-width="1">
          <!-- Eje Y -->
          <line :x1="padding.left" :y1="padding.top" :x2="padding.left" :y2="svgHeight - padding.bottom" />
          <!-- Eje X -->
          <line :x1="padding.left" :y1="svgHeight - padding.bottom" :x2="svgWidth - padding.right" :y2="svgHeight - padding.bottom" />
        </g>

        <!-- Etiquetas Eje Y (Valores redondeados a 1 decimal) -->
        <g font-size="9" fill="rgba(255,255,255,0.6)" font-family="monospace" text-anchor="end">
          <text v-for="t in yTicks" :key="t.y" :x="padding.left - 6" :y="t.y + 3">
            {{ Math.round(t.val) }}
          </text>
        </g>

        <!-- Etiquetas Eje X (Hora) -->
        <g font-size="9" fill="rgba(255,255,255,0.6)" font-family="monospace" text-anchor="middle">
          <text v-for="t in xTicks" :key="t.x" :x="t.x" :y="svgHeight - padding.bottom + 16">
            {{ t.label }}
          </text>
        </g>

        <!-- Marcadores de Tiempo (TimeMarker para saltos de captura) -->
        <TimeMarker :markers="timeMarkers" :height="svgHeight - padding.bottom" />

        <!-- Polilíneas por Canal -->
        <g v-for="ch in channelLines" :key="ch.signal_id">
          <polyline
            v-for="(seg, segIdx) in ch.segments"
            :key="segIdx"
            fill="none"
            :stroke="ch.color"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
            :points="seg"
          />
        </g>

        <!-- Cursor de Inspección (PlotCursor) -->
        <PlotCursor
          :x="cursorX"
          :time-str="cursorTimeStr"
          :values="cursorValues"
          :height="svgHeight - padding.bottom"
        />
      </svg>
    </div>
  </div>
</template>
