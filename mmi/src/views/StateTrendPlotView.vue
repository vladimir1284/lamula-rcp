<!--
  StateTrendPlotView.vue: Vista B4 — Graficación de Tendencias de Estado (XY).
  Gaps documentados:
  1. El buffer de tendencia vive en la memoria del gateway y no persiste entre reinicios (misma convención que el resto del estado de control).
  2. Sin wraparound automático a las 8h: se detiene al llegar al límite (8h a 1 muestra/s = 28,800 muestras), sin inventar reinicio automático no especificado.
  3. Cursor de inspección por desplazamiento (hover) en lugar de clic derecho (el clic derecho interfiere con el menú contextual nativo del navegador).
-->
<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import ChannelSelector from '@/components/domain/ChannelSelector.vue'
import PlotTransportControls from '@/components/domain/PlotTransportControls.vue'
import TrendChart from '@/components/domain/TrendChart.vue'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useGateway } from '@/composables/useGateway'
import type { TrendSeries, TrendStatus } from '@/types/mmi'

const {
  fetchTrendChannels,
  fetchTrendStatus,
  startTrend,
  stopTrend,
  continueTrend,
  clearTrend,
  fetchTrendData,
} = useGateway()

const availableChannels = ref<string[]>([])
const selectedChannels = ref<string[]>([])
const trendStatus = ref<TrendStatus>({ running: false, started_at_wall: null, signal_ids: [] })
const trendSeries = ref<TrendSeries[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

let pollTimer: ReturnType<typeof setInterval> | null = null

async function loadChannelsAndStatus() {
  loading.value = true
  error.value = null
  try {
    availableChannels.value = await fetchTrendChannels()
    trendStatus.value = await fetchTrendStatus()
    if (trendStatus.value.signal_ids.length > 0) {
      selectedChannels.value = [...trendStatus.value.signal_ids]
    } else if (availableChannels.value.length > 0) {
      // Selección por defecto de los primeros dos canales AI
      selectedChannels.value = availableChannels.value.slice(0, 2)
    }
    await refreshData()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

async function refreshData() {
  try {
    trendStatus.value = await fetchTrendStatus()
    trendSeries.value = await fetchTrendData()
  } catch (e) {
    // No pisar el error principal si la reconexión es temporal
  }
}

async function handleStart() {
  if (selectedChannels.value.length === 0) return
  error.value = null
  try {
    trendStatus.value = await startTrend(selectedChannels.value)
    await refreshData()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

async function handleStop() {
  error.value = null
  try {
    trendStatus.value = await stopTrend()
    await refreshData()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

async function handleContinue() {
  error.value = null
  try {
    trendStatus.value = await continueTrend()
    await refreshData()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

async function handleClear() {
  error.value = null
  try {
    trendStatus.value = await clearTrend()
    trendSeries.value = []
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

onMounted(() => {
  loadChannelsAndStatus()
  pollTimer = setInterval(refreshData, 1000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 overflow-auto p-3">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <div>
        <h2 class="text-lg font-semibold text-foreground">B4 State Trend Plot (XY)</h2>
        <p class="text-xs text-muted-foreground">
          Muestreo en tiempo real de canales analógicos a 1 muestra/segundo (máx. 8 horas de buffer).
        </p>
      </div>

      <PlotTransportControls
        :running="trendStatus.running"
        :has-data="trendSeries.some((s) => s.samples.length > 0)"
        :can-start="selectedChannels.length > 0"
        :disabled="loading"
        @start="handleStart"
        @stop="handleStop"
        @continue="handleContinue"
        @clear="handleClear"
      />
    </div>

    <p v-if="error" class="text-xs font-medium text-destructive">
      {{ error }}
    </p>

    <!-- Selector de canales (deshabilitado mientras esté en ejecución) -->
    <ChannelSelector
      v-model:selected="selectedChannels"
      :channels="availableChannels"
      :disabled="trendStatus.running"
    />

    <!-- Panel del Gráfico -->
    <Card>
      <CardHeader>
        <CardTitle class="flex items-center justify-between">
          <span>Gráfico de Tendencias</span>
          <span class="text-xs font-normal text-muted-foreground">
            Estado: {{ trendStatus.running ? 'Muestreando en vivo' : 'Detenido' }}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div v-if="trendSeries.length === 0 || trendSeries.every((s) => s.samples.length === 0)" class="p-8 text-center text-xs text-muted-foreground">
          No hay datos de tendencias. Seleccione canales y presione "Iniciar Captura".
        </div>
        <TrendChart v-else :series="trendSeries" />
      </CardContent>
    </Card>
  </div>
</template>
