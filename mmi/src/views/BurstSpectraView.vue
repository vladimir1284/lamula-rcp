<script setup lang="ts">
// BurstSpectraView.vue: Vista F2 — Burst Spectra & Matched Filter (Ps).
//
// Recorte de alcance obligatorio:
// - Muestra traza cruda de espectro (n_bins f32, canal, seq, capture_time, ref_level_dbm).
// - NO hay diseño de filtro (FIR taps, BW, # coef, DCGain, Loss), NI control MFC, NI promediado,
//   NI selección de canal, NI estados AFC (Disabled/Wait/Track/Locked...).
// - Banner fijo visible informando de limitaciones.
// - Eje X en unidades de bin (sin escala de frecuencia real).
// - Plot log con rango dinámico de 70 dB (líneas cada 10 dB) per RVP §5.4.
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useGateway } from '@/composables/useGateway'
import type { SpectrumSnapshot } from '@/types/mmi'

const { fetchSpectrum, requestSpectrum, maintenance } = useGateway()

const spectrum = ref<SpectrumSnapshot | null>(null)
const loading = ref(false)
const requesting = ref(false)
const message = ref<string | null>(null)
const isError = ref(false)

const isMaintenanceUnlocked = computed(() => maintenance.value?.level === 'MANT')

const wrapEl = ref<HTMLDivElement | null>(null)
const canvasEl = ref<HTMLCanvasElement | null>(null)
let ro: ResizeObserver | null = null

async function loadData() {
  loading.value = true
  message.value = null
  isError.value = false
  try {
    spectrum.value = await fetchSpectrum()
  } catch (err) {
    isError.value = true
    message.value = err instanceof Error ? err.message : 'Error al cargar traza de espectro'
  } finally {
    loading.value = false
  }
}

async function handleRequestSpectrum() {
  requesting.value = true
  message.value = null
  isError.value = false
  try {
    await requestSpectrum()
    message.value = 'Solicitud de espectro enviada al DSP. Cargando captura...'
    await loadData()
  } catch (err) {
    isError.value = true
    message.value = err instanceof Error ? err.message : 'Error al solicitar espectro'
  } finally {
    requesting.value = false
  }
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

  // Background
  ctx.fillStyle = '#0d0d0d'
  ctx.fillRect(0, 0, w, h)

  const snap = spectrum.value
  if (!snap || !snap.has_data || !snap.bins || snap.bins.length === 0) {
    ctx.fillStyle = '#666666'
    ctx.font = '12px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('Sin datos de espectro. Haga clic en "Pedir espectro" para solicitar una traza.', w / 2, h / 2)
    return
  }

  const paddingLeft = 45
  const paddingRight = 15
  const paddingTop = 20
  const paddingBottom = 30

  const plotW = w - paddingLeft - paddingRight
  const plotH = h - paddingTop - paddingBottom

  const refLevel = snap.ref_level_dbm || 0.0
  // Dynamic range of 70 dB per RVP §5.4
  const minDb = refLevel - 70.0
  const maxDb = refLevel

  // Draw Grid Lines Y (every 10 dB)
  ctx.strokeStyle = '#262626'
  ctx.lineWidth = 1
  ctx.fillStyle = '#888888'
  ctx.font = '10px monospace'
  ctx.textAlign = 'right'
  ctx.textBaseline = 'middle'

  for (let db = minDb; db <= maxDb; db += 10) {
    const yFrac = (maxDb - db) / 70.0
    const y = paddingTop + yFrac * plotH
    ctx.beginPath()
    ctx.moveTo(paddingLeft, y)
    ctx.lineTo(w - paddingRight, y)
    ctx.stroke()

    ctx.fillText(`${db.toFixed(0)} dB`, paddingLeft - 5, y)
  }

  // Draw Grid Lines X (5 divisions)
  const binsCount = snap.bins.length
  ctx.textAlign = 'center'
  ctx.textBaseline = 'top'

  const numXDivs = 5
  for (let i = 0; i <= numXDivs; i++) {
    const binIdx = Math.round((i / numXDivs) * (binsCount - 1))
    const xFrac = i / numXDivs
    const x = paddingLeft + xFrac * plotW

    ctx.beginPath()
    ctx.moveTo(x, paddingTop)
    ctx.lineTo(x, h - paddingBottom)
    ctx.stroke()

    ctx.fillText(`bin ${binIdx}`, x, h - paddingBottom + 5)
  }

  // Draw Spectrum Plot Trace
  ctx.strokeStyle = '#38bdf8' // Cyan-400
  ctx.lineWidth = 2
  ctx.beginPath()

  for (let i = 0; i < binsCount; i++) {
    const binVal = snap.bins[i] ?? minDb
    const clampedVal = Math.max(minDb, Math.min(maxDb, binVal))
    const xFrac = i / Math.max(1, binsCount - 1)
    const yFrac = (maxDb - clampedVal) / 70.0

    const x = paddingLeft + xFrac * plotW
    const y = paddingTop + yFrac * plotH

    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  }
  ctx.stroke()
}

function formatTimeUtc(ns: number): string {
  if (!ns) return '—'
  const ms = ns / 1_000_000
  const date = new Date(ms)
  return date.toISOString().replace('T', ' ').substring(0, 19) + ' UTC'
}

watch(spectrum, () => {
  draw()
})

onMounted(() => {
  ro = new ResizeObserver(resizeCanvas)
  if (wrapEl.value) ro.observe(wrapEl.value)
  resizeCanvas()
  loadData()
})

onBeforeUnmount(() => {
  ro?.disconnect()
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-3 overflow-auto p-3 text-xs bg-background text-foreground">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-2 border-b pb-2">
      <div>
        <div class="flex items-center gap-2">
          <h2 class="text-base font-bold tracking-tight">F2 — Burst Spectra & Matched Filter (Ps)</h2>
          <Badge variant="outline" class="text-xs">Ps</Badge>
          <Badge variant="outline" class="border-amber-500/50 bg-amber-500/10 text-amber-500 text-xs">
            Alcance Recortado
          </Badge>
        </div>
        <p class="text-xs text-muted-foreground mt-0.5">
          Visualizador de traza de espectro de FI capturada por el analizador DSP.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <Button variant="outline" size="sm" :disabled="loading" @click="loadData">
          Refrescar
        </Button>
        <Button
          size="sm"
          :disabled="requesting || !isMaintenanceUnlocked"
          @click="handleRequestSpectrum"
        >
          {{ requesting ? 'Solicitando...' : 'Pedir espectro' }}
        </Button>
      </div>
    </div>

    <!-- Status / Error Messages -->
    <div
      v-if="message"
      class="rounded p-2 text-xs"
      :class="isError ? 'border border-destructive/50 bg-destructive/10 text-destructive' : 'border border-emerald-500/50 bg-emerald-500/10 text-emerald-500'"
    >
      {{ message }}
    </div>

    <div v-if="!isMaintenanceUnlocked" class="rounded border border-amber-500/30 bg-amber-500/10 p-2 text-amber-700 dark:text-amber-300">
      Aviso: Solicitar una nueva traza de espectro (`request_spectrum`) requiere nivel de mantenimiento MANT activo.
    </div>

    <!-- Fixed Limitation Banner -->
    <div class="rounded border border-amber-500/40 bg-amber-500/10 p-2.5 text-amber-600 dark:text-amber-400 font-medium text-xs leading-relaxed">
      <strong>Limitaciones de Integración:</strong> Solo canal RX_0. Sin promediado. Diseño de filtro adaptado no disponible — pendiente lamula-dsp#1.
    </div>

    <!-- Plot Area -->
    <div class="flex flex-1 min-h-[220px] flex-col rounded border border-border bg-card p-2">
      <!-- Plot X-axis Banner -->
      <div class="flex items-center justify-between pb-1.5 px-1 border-b border-border/50 text-[11px]">
        <span class="font-semibold text-muted-foreground">Traza de Espectro Logarítmica (dB vs Index)</span>
        <span class="text-amber-500 font-mono text-[10px]">
          sin escala de frecuencia real — center_freq_hz/span_hz no disponibles
        </span>
      </div>

      <!-- Canvas Plot -->
      <div ref="wrapEl" class="relative min-h-0 flex-1 w-full mt-1">
        <canvas ref="canvasEl" class="h-full w-full block rounded bg-black" />
      </div>
    </div>

    <!-- Live Telemetry Status Bar -->
    <div class="rounded border border-border bg-muted/40 p-2 text-xs">
      <div class="font-semibold text-foreground mb-1">Telemetría de la Traza Viva:</div>
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-[11px]">
        <div>
          <span class="text-muted-foreground block text-[10px] font-sans">Nivel Referencia</span>
          <span class="font-bold text-foreground">
            {{ spectrum?.has_data ? `${spectrum.ref_level_dbm.toFixed(1)} dBm` : '—' }}
          </span>
        </div>
        <div>
          <span class="text-muted-foreground block text-[10px] font-sans">Secuencia (`seq`)</span>
          <span class="font-bold text-foreground">
            {{ spectrum?.has_data ? `#${spectrum.seq}` : '—' }}
          </span>
        </div>
        <div>
          <span class="text-muted-foreground block text-[10px] font-sans">Tiempo Captura</span>
          <span class="font-bold text-foreground">
            {{ spectrum?.has_data ? formatTimeUtc(spectrum.capture_time_utc_ns) : '—' }}
          </span>
        </div>
        <div>
          <span class="text-muted-foreground block text-[10px] font-sans">Canal RX</span>
          <span class="font-bold text-foreground">
            {{ spectrum?.has_data ? `RX_${spectrum.channel}` : '—' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
