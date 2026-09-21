<script setup lang="ts">
// D3 PPI (docs/diseno/inventario-ui.md) -- D6: usa escala continua interpolada `buildActiveScale`.
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import ColorScaleLegend from '@/components/domain/ColorScaleLegend.vue'
import CursorReadout from '@/components/domain/CursorReadout.vue'
import DataViewToolbar from '@/components/domain/DataViewToolbar.vue'
import { buildActiveScale, colorForValueContinuous } from '@/lib/dataPalette'
import { generateGates, GATE_COUNT, MAX_RANGE_KM, type DataKind } from '@/lib/mockRadar'

const props = withDefaults(defineProps<{ frozen?: boolean }>(), { frozen: false })

const dataType = ref<DataKind>('reflectivity')
const resolution = ref(64)
const zoom = ref(1)
const source = ref<'radar' | 'file'>('radar')

const wrapEl = ref<HTMLDivElement | null>(null)
const dataCanvasEl = ref<HTMLCanvasElement | null>(null)
const overlayCanvasEl = ref<HTMLCanvasElement | null>(null)
let ro: ResizeObserver | null = null
let timer: ReturnType<typeof setInterval> | null = null

const angle = ref(0)
const ANGLE_STEP_DEG = 3
const BUCKET_COUNT = 360 / ANGLE_STEP_DEG
let history: (number[] | null)[] = Array.from({ length: BUCKET_COUNT }, () => null)

const activeScale = ref<string[]>(buildActiveScale(dataType.value, 256))

const cursor = ref<{ rangeKm: number; azimuthDeg: number; elevationDeg: number; value: number; kind: DataKind } | null>(null)

function quantize(v: number, levels: number): number {
  return Math.round(v * (levels - 1)) / (levels - 1)
}

function sizePx() {
  const canvas = dataCanvasEl.value
  const w = canvas?.width ?? 0
  const h = canvas?.height ?? 0
  const radius = Math.min(w, h) * 0.47
  return { w, h, cx: w / 2, cy: h / 2, radius }
}

function resizeCanvases() {
  const wrap = wrapEl.value
  const data = dataCanvasEl.value
  const overlay = overlayCanvasEl.value
  if (!wrap || !data || !overlay) return
  const ratio = window.devicePixelRatio || 1
  for (const c of [data, overlay]) {
    c.width = Math.max(1, wrap.clientWidth * ratio)
    c.height = Math.max(1, wrap.clientHeight * ratio)
  }
  redrawAll()
}

function drawSector(bucketDeg: number, gates: number[]) {
  const ctx = dataCanvasEl.value?.getContext('2d')
  if (!ctx) return
  const { cx, cy, radius } = sizePx()
  const a0 = ((bucketDeg * Math.PI) / 180) - Math.PI / 2
  const a1 = (((bucketDeg + ANGLE_STEP_DEG * 1.02) * Math.PI) / 180) - Math.PI / 2
  const rScale = (radius * zoom.value) / gates.length
  for (let i = 0; i < gates.length; i++) {
    const v = quantize(gates[i] ?? 0, resolution.value)
    const r0 = i * rScale
    const r1 = (i + 1) * rScale + 0.5
    ctx.fillStyle = colorForValueContinuous(activeScale.value, dataType.value, v)
    ctx.beginPath()
    ctx.arc(cx, cy, r1, a0, a1)
    ctx.arc(cx, cy, r0, a1, a0, true)
    ctx.closePath()
    ctx.fill()
  }
}

function redrawAll() {
  const ctx = dataCanvasEl.value?.getContext('2d')
  if (!ctx) return
  ctx.fillStyle = '#0d0d0d'
  ctx.fillRect(0, 0, dataCanvasEl.value!.width, dataCanvasEl.value!.height)
  for (let b = 0; b < BUCKET_COUNT; b++) {
    const g = history[b]
    if (g) drawSector(b * ANGLE_STEP_DEG, g)
  }
  drawOverlay()
}

function drawOverlay() {
  const ctx = overlayCanvasEl.value?.getContext('2d')
  if (!ctx) return
  const { w, h, cx, cy, radius } = sizePx()
  ctx.clearRect(0, 0, w, h)

  ctx.strokeStyle = 'rgba(255,255,255,0.18)'
  ctx.lineWidth = 1
  for (let f = 0.25; f <= 1; f += 0.25) {
    ctx.beginPath()
    ctx.arc(cx, cy, radius * zoom.value * f, 0, Math.PI * 2)
    ctx.stroke()
  }

  const thetaRad = (angle.value * Math.PI) / 180
  ctx.strokeStyle = 'white'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(cx, cy)
  ctx.lineTo(cx + radius * zoom.value * Math.sin(thetaRad), cy - radius * zoom.value * Math.cos(thetaRad))
  ctx.stroke()

  if (zoom.value > 1) {
    const insetR = Math.min(w, h) * 0.14
    const insetCx = w - insetR - 8
    const insetCy = insetR + 8
    ctx.fillStyle = 'rgba(13,13,13,0.9)'
    ctx.beginPath()
    ctx.arc(insetCx, insetCy, insetR, 0, Math.PI * 2)
    ctx.fill()
    ctx.strokeStyle = 'rgba(255,255,255,0.4)'
    ctx.stroke()
    const boxHalf = insetR / zoom.value
    ctx.strokeStyle = 'white'
    ctx.strokeRect(insetCx - boxHalf, insetCy - boxHalf, boxHalf * 2, boxHalf * 2)
  }
}

function step() {
  if (props.frozen) return
  angle.value = (angle.value + ANGLE_STEP_DEG) % 360
  const bucket = Math.floor(angle.value / ANGLE_STEP_DEG)
  const gates = generateGates(dataType.value, angle.value)
  history[bucket] = gates
  drawSector(bucket * ANGLE_STEP_DEG, gates)
  drawOverlay()
}

function reloadScale() {
  activeScale.value = buildActiveScale(dataType.value, 256)
  redrawAll()
}

watch(dataType, () => {
  activeScale.value = buildActiveScale(dataType.value, 256)
  history = Array.from({ length: BUCKET_COUNT }, () => null)
  redrawAll()
})
watch([resolution, zoom], redrawAll)

function onCanvasClick(ev: MouseEvent) {
  const canvas = overlayCanvasEl.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  const { cx, cy, radius } = sizePx()
  const dpr = canvas.width / rect.width
  const px = (ev.clientX - rect.left) * dpr - cx
  const py = (ev.clientY - rect.top) * dpr - cy
  const rFrac = Math.hypot(px, py) / (radius * zoom.value)
  if (rFrac > 1) return
  const thetaDeg = ((Math.atan2(px, -py) * 180) / Math.PI + 360) % 360
  const bucket = Math.floor(thetaDeg / ANGLE_STEP_DEG)
  const gates = history[bucket]
  const gateIdx = Math.min(GATE_COUNT - 1, Math.round(rFrac * GATE_COUNT))
  cursor.value = {
    rangeKm: rFrac * MAX_RANGE_KM,
    azimuthDeg: thetaDeg,
    elevationDeg: 0.5,
    value: gates ? (gates[gateIdx] ?? 0) : 0,
    kind: dataType.value,
  }
}

onMounted(() => {
  ro = new ResizeObserver(resizeCanvases)
  if (wrapEl.value) ro.observe(wrapEl.value)
  resizeCanvases()
  timer = setInterval(step, 100)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
  ro?.disconnect()
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-1.5">
    <DataViewToolbar
      v-model:data-type="dataType"
      v-model:resolution="resolution"
      v-model:zoom="zoom"
      v-model:source="source"
      @color-composer-updated="reloadScale"
    />
    <div class="flex min-h-0 flex-1 gap-1.5">
      <div ref="wrapEl" class="relative min-h-0 flex-1">
        <canvas ref="dataCanvasEl" class="absolute inset-0 h-full w-full" />
        <canvas ref="overlayCanvasEl" class="absolute inset-0 h-full w-full cursor-crosshair" @click="onCanvasClick" />
        <span v-if="frozen" class="absolute right-1 top-1 rounded-sm bg-state-simulated/80 px-1 text-[10px] text-white">FROZEN</span>
      </div>
      <ColorScaleLegend :kind="dataType" :custom-scale="activeScale" />
    </div>
    <div class="flex items-center justify-between gap-2">
      <span class="text-[10px] text-muted-foreground">
        Alcance {{ MAX_RANGE_KM }} km · fuente {{ source === 'radar' ? 'radar' : 'fichero (mock, sin implementar)' }}
      </span>
      <CursorReadout :cursor="cursor" />
    </div>
  </div>
</template>
