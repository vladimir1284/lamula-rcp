<script setup lang="ts">
// D4 RHI (docs/diseno/inventario-ui.md) -- igual patrón que D3 (PpiView.vue):
// radar en la esquina inferior izquierda, línea radial sigue la velocidad de
// elevación en vez de azimut, cursor añade altura. Misma limitación
// documentada en PpiView.vue sobre el inset (zoom centrado, sin recentrar
// por click) y mismo límite de fondo (sin stream de momentos real, "camino
// 1" -- solo UI + datos sintéticos).
//
// Azimut fijo sintético: en el legacy el RHI corre a un azimut del Scan
// Worksheet, que en este mock no existe conectado -- se fija a un valor
// constante en vez de inventar un selector de azimut sin scan worksheet real
// detrás.
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import ColorScaleLegend from '@/components/domain/ColorScaleLegend.vue'
import CursorReadout from '@/components/domain/CursorReadout.vue'
import DataViewToolbar from '@/components/domain/DataViewToolbar.vue'
import { resolvePalette, colorForValue } from '@/lib/dataPalette'
import { generateGates, GATE_COUNT, MAX_RANGE_KM, type DataKind } from '@/lib/mockRadar'

const props = withDefaults(defineProps<{ frozen?: boolean }>(), { frozen: false })

const FIXED_AZIMUTH_DEG = 45
const EL_MIN = 0
const EL_MAX = 90
const EL_STEP_DEG = 2

const dataType = ref<DataKind>('reflectivity')
const resolution = ref(64)
const zoom = ref(1)
const source = ref<'radar' | 'file'>('radar')

const wrapEl = ref<HTMLDivElement | null>(null)
const dataCanvasEl = ref<HTMLCanvasElement | null>(null)
const overlayCanvasEl = ref<HTMLCanvasElement | null>(null)
let ro: ResizeObserver | null = null
let timer: ReturnType<typeof setInterval> | null = null

const elevation = ref(0)
let direction = 1 // RHI barre elevación de ida y vuelta, no da vueltas completas como PPI
const BUCKET_COUNT = (EL_MAX - EL_MIN) / EL_STEP_DEG
// Mismo bug que PpiView.vue: el bucket del historial tiene que medir lo
// mismo que el paso de elevación por tick, si no, sólo se pinta una
// fracción de los grados y quedan rendijas "de rueda" en el abanico.
let history: (number[] | null)[] = Array.from({ length: BUCKET_COUNT }, () => null)
let palette = resolvePalette(dataType.value)

const cursor = ref<{ rangeKm: number; azimuthDeg: number; elevationDeg: number; heightKm: number; value: number; kind: DataKind } | null>(null)

function quantize(v: number, levels: number): number {
  return Math.round(v * (levels - 1)) / (levels - 1)
}

function sizePx() {
  const canvas = dataCanvasEl.value
  const w = canvas?.width ?? 0
  const h = canvas?.height ?? 0
  const radius = Math.min(w, h) * 0.92
  return { w, h, originX: w * 0.06, originY: h * 0.94, radius }
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

// Misma cuña polar real que PpiView.vue -- ver comentario ahí sobre el bug
// de rendijas que deja un rect de ancho fijo.
function drawSector(bucketDeg: number, gates: number[]) {
  const ctx = dataCanvasEl.value?.getContext('2d')
  if (!ctx) return
  const { originX, originY, radius } = sizePx()
  const a0 = -((bucketDeg + EL_STEP_DEG * 1.02) * Math.PI) / 180
  const a1 = -(bucketDeg * Math.PI) / 180
  const rScale = (radius * zoom.value) / gates.length
  for (let i = 0; i < gates.length; i++) {
    const v = quantize(gates[i] ?? 0, resolution.value)
    const r0 = i * rScale
    const r1 = (i + 1) * rScale + 0.5
    ctx.fillStyle = colorForValue(palette, dataType.value, v)
    ctx.beginPath()
    ctx.arc(originX, originY, r1, a0, a1)
    ctx.arc(originX, originY, r0, a1, a0, true)
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
    if (g) drawSector(EL_MIN + b * EL_STEP_DEG, g)
  }
  drawOverlay()
}

function drawOverlay() {
  const ctx = overlayCanvasEl.value?.getContext('2d')
  if (!ctx) return
  const { w, h, originX, originY, radius } = sizePx()
  ctx.clearRect(0, 0, w, h)

  // Anillos de rango (isométricos con PPI: arcos de altura/rango constante).
  ctx.strokeStyle = 'rgba(255,255,255,0.18)'
  ctx.lineWidth = 1
  for (let f = 0.25; f <= 1; f += 0.25) {
    ctx.beginPath()
    ctx.arc(originX, originY, radius * zoom.value * f, -Math.PI / 2, 0)
    ctx.stroke()
  }

  // Línea de barrido: sigue la velocidad de elevación, no de azimut.
  const elRad = (elevation.value * Math.PI) / 180
  ctx.strokeStyle = 'white'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(originX, originY)
  ctx.lineTo(originX + radius * zoom.value * Math.cos(elRad), originY - radius * zoom.value * Math.sin(elRad))
  ctx.stroke()

  if (zoom.value > 1) {
    const insetR = Math.min(w, h) * 0.14
    const insetOx = w - insetR * 2 - 10
    const insetOy = h - 10
    ctx.fillStyle = 'rgba(13,13,13,0.9)'
    ctx.beginPath()
    ctx.moveTo(insetOx, insetOy)
    ctx.arc(insetOx, insetOy, insetR, -Math.PI / 2, 0)
    ctx.closePath()
    ctx.fill()
    ctx.strokeStyle = 'rgba(255,255,255,0.4)'
    ctx.stroke()
    const boxSide = insetR / zoom.value
    ctx.strokeStyle = 'white'
    ctx.strokeRect(insetOx, insetOy - boxSide, boxSide, boxSide)
  }
}

function step() {
  if (props.frozen) return
  elevation.value += EL_STEP_DEG * direction
  if (elevation.value >= EL_MAX) {
    elevation.value = EL_MAX
    direction = -1
  } else if (elevation.value <= EL_MIN) {
    elevation.value = EL_MIN
    direction = 1
  }
  const bucket = Math.min(BUCKET_COUNT - 1, Math.floor((elevation.value - EL_MIN) / EL_STEP_DEG))
  const bucketDeg = EL_MIN + bucket * EL_STEP_DEG
  const gates = generateGates(dataType.value, FIXED_AZIMUTH_DEG + bucketDeg)
  history[bucket] = gates
  drawSector(bucketDeg, gates)
  drawOverlay()
}

watch(dataType, () => {
  palette = resolvePalette(dataType.value)
  history = Array.from({ length: BUCKET_COUNT }, () => null)
  redrawAll()
})
watch([resolution, zoom], redrawAll)

function onCanvasClick(ev: MouseEvent) {
  const canvas = overlayCanvasEl.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  const { originX, originY, radius } = sizePx()
  const dpr = canvas.width / rect.width
  const px = (ev.clientX - rect.left) * dpr - originX
  const py = originY - (ev.clientY - rect.top) * dpr
  if (px < 0 || py < 0) return
  const rFrac = Math.hypot(px, py) / (radius * zoom.value)
  if (rFrac > 1) return
  const elDeg = (Math.atan2(py, px) * 180) / Math.PI
  const clampedEl = Math.min(EL_MAX, Math.max(EL_MIN, elDeg))
  const bucket = Math.min(BUCKET_COUNT - 1, Math.floor((clampedEl - EL_MIN) / EL_STEP_DEG))
  const gates = history[bucket]
  const gateIdx = Math.min(GATE_COUNT - 1, Math.round(rFrac * GATE_COUNT))
  cursor.value = {
    rangeKm: rFrac * MAX_RANGE_KM,
    azimuthDeg: FIXED_AZIMUTH_DEG,
    elevationDeg: elDeg,
    heightKm: rFrac * MAX_RANGE_KM * Math.sin((elDeg * Math.PI) / 180),
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
    />
    <div class="flex min-h-0 flex-1 gap-1.5">
      <div ref="wrapEl" class="relative min-h-0 flex-1">
        <canvas ref="dataCanvasEl" class="absolute inset-0 h-full w-full" />
        <canvas ref="overlayCanvasEl" class="absolute inset-0 h-full w-full cursor-crosshair" @click="onCanvasClick" />
        <span v-if="frozen" class="absolute right-1 top-1 rounded-sm bg-state-simulated/80 px-1 text-[10px] text-white">FROZEN</span>
      </div>
      <ColorScaleLegend :kind="dataType" />
    </div>
    <div class="flex items-center justify-between gap-2">
      <span class="text-[10px] text-muted-foreground">
        AZ fijo {{ FIXED_AZIMUTH_DEG }}° (Scan Worksheet mock) · alcance {{ MAX_RANGE_KM }} km ·
        fuente {{ source === 'radar' ? 'radar' : 'fichero (mock, sin implementar)' }}
      </span>
      <CursorReadout :cursor="cursor" />
    </div>
  </div>
</template>
