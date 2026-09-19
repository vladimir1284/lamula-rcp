<script setup lang="ts">
// D2 ASCOPE (docs/diseno/inventario-ui.md) -- "camino 1" acordado: solo UI +
// datos sintéticos en Storybook, sin backend real (no hay stream de
// momentos RCP<->MMI todavía, ver src/core/contracts/mmi.py, DspStreamStatus).
//
// `frozen` llega del panel que aloja esta vista (App.vue reenvía
// `panel.frozen` del slot con nombre) -- es el mismo ❄ de PanelFrame, no un
// segundo control duplicado (ver nota en DataViewToolbar.vue). Congela el
// barrido sintético sin tocar otras instancias de esta vista en otros
// paneles, que es exactamente el requisito de D2.
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import CursorReadout from '@/components/domain/CursorReadout.vue'
import DataViewToolbar from '@/components/domain/DataViewToolbar.vue'
import { generateGates, GATE_COUNT, MAX_RANGE_KM, type DataKind } from '@/lib/mockRadar'

const props = withDefaults(defineProps<{ frozen?: boolean }>(), { frozen: false })

const dataType = ref<DataKind>('reflectivity')
const resolution = ref(64)
const zoom = ref(1)
const source = ref<'radar' | 'file'>('radar')
const axisUnit = ref<'km' | 'us'>('km')
const pan = ref(0) // 0..1, borde izquierdo de la ventana visible cuando zoom > 1

const SCOPE_BG = '#0d0d0d' // fijo, no sigue el tema -- ver main.css, "Data palettes..."

const wrapEl = ref<HTMLDivElement | null>(null)
const canvasEl = ref<HTMLCanvasElement | null>(null)
let ro: ResizeObserver | null = null
let timer: ReturnType<typeof setInterval> | null = null

const angle = ref(0) // azimut sintético en grados
const tick = ref(0)
let lastGates: number[] = generateGates(dataType.value, 0)

const cursor = ref<{ rangeKm: number; azimuthDeg: number; elevationDeg: number; value: number; kind: DataKind } | null>(null)

function quantize(v: number, levels: number): number {
  return Math.round(v * (levels - 1)) / (levels - 1)
}

function resizeCanvas() {
  const wrap = wrapEl.value
  const canvas = canvasEl.value
  if (!wrap || !canvas) return
  const ratio = window.devicePixelRatio || 1
  canvas.width = Math.max(1, wrap.clientWidth * ratio)
  canvas.height = Math.max(1, wrap.clientHeight * ratio)
  draw()
}

function draw() {
  const canvas = canvasEl.value
  const ctx = canvas?.getContext('2d')
  if (!canvas || !ctx) return
  const w = canvas.width
  const h = canvas.height
  ctx.fillStyle = SCOPE_BG
  ctx.fillRect(0, 0, w, h)

  const visibleFrac = 1 / zoom.value
  const startGate = Math.floor(pan.value * GATE_COUNT)
  const endGate = Math.min(GATE_COUNT, startGate + Math.ceil(visibleFrac * GATE_COUNT))
  const signed = dataType.value === 'velocity'
  const baselineY = signed ? h / 2 : h - 4

  ctx.strokeStyle = 'oklch(0.7 0.15 195)'
  ctx.lineWidth = Math.max(1, dpr())
  ctx.beginPath()
  for (let i = startGate; i < endGate; i++) {
    const v = quantize(lastGates[i] ?? 0, resolution.value)
    const x = ((i - startGate) / Math.max(1, endGate - startGate - 1)) * w
    const amp = signed ? v : v
    const y = signed ? baselineY - amp * (h / 2 - 4) : h - 4 - amp * (h - 8)
    if (i === startGate) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  }
  ctx.stroke()

  if (signed) {
    ctx.strokeStyle = 'rgba(255,255,255,0.25)'
    ctx.beginPath()
    ctx.moveTo(0, baselineY)
    ctx.lineTo(w, baselineY)
    ctx.stroke()
  }
}

function dpr() {
  return window.devicePixelRatio || 1
}

function step() {
  tick.value += 1
  if (props.frozen) return
  angle.value = (angle.value + 9) % 360
  if (tick.value % Math.max(1, toolbarRefreshRate.value) !== 0) return
  lastGates = generateGates(dataType.value, angle.value)
  draw()
}

const toolbarRefreshRate = ref(1)

watch([dataType, resolution, zoom, pan], draw)

function onCanvasClick(ev: MouseEvent) {
  const canvas = canvasEl.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  const xFrac = (ev.clientX - rect.left) / rect.width
  const visibleFrac = 1 / zoom.value
  const startGate = Math.floor(pan.value * GATE_COUNT)
  const endGate = Math.min(GATE_COUNT, startGate + Math.ceil(visibleFrac * GATE_COUNT))
  const gateIdx = Math.round(startGate + xFrac * (endGate - startGate - 1))
  const value = lastGates[Math.max(0, Math.min(GATE_COUNT - 1, gateIdx))] ?? 0
  cursor.value = {
    rangeKm: (gateIdx / GATE_COUNT) * MAX_RANGE_KM,
    azimuthDeg: angle.value,
    elevationDeg: 0.5,
    value,
    kind: dataType.value,
  }
}

onMounted(() => {
  ro = new ResizeObserver(resizeCanvas)
  if (wrapEl.value) ro.observe(wrapEl.value)
  resizeCanvas()
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
      v-model:refresh-rate="toolbarRefreshRate"
      v-model:axis-unit="axisUnit"
      show-refresh-rate
      show-axis-unit
    />
    <div class="flex min-h-0 flex-1 gap-1.5">
      <div ref="wrapEl" class="relative min-h-0 flex-1">
        <canvas ref="canvasEl" class="h-full w-full cursor-crosshair" @click="onCanvasClick" />
        <span v-if="frozen" class="absolute right-1 top-1 rounded-sm bg-state-simulated/80 px-1 text-[10px] text-white">FROZEN</span>
      </div>
    </div>
    <input
      v-if="zoom > 1"
      v-model.number="pan"
      type="range"
      min="0"
      :max="1 - 1 / zoom"
      step="0.01"
      class="w-full"
      aria-label="Recorrer rango"
    />
    <div class="flex items-center justify-between gap-2">
      <span class="text-[10px] text-muted-foreground">
        Eje X: {{ axisUnit === 'km' ? `0–${MAX_RANGE_KM} km` : `0–${(MAX_RANGE_KM * 6.667).toFixed(0)} µsec` }} ·
        fuente {{ source === 'radar' ? 'radar' : 'fichero (mock, sin implementar)' }}
      </span>
      <CursorReadout :cursor="cursor" />
    </div>
  </div>
</template>
