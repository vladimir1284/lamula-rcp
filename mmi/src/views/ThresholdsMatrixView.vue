<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useGateway } from '@/composables/useGateway'
import type { DspInternalStatusSnapshot } from '@/types/mmi'

const { fetchDspInternalStatus } = useGateway()

const dspStatus = ref<DspInternalStatusSnapshot | null>(null)
const loading = ref(false)
const errorMessage = ref<string | null>(null)

// 4 umbrales reales globales expuestos por el contrato DSP
const REAL_THRESHOLDS = [
  { key: 'log_threshold' as const, label: 'LOG', unit: 'dB', description: 'Umbral de potencia logarítmica' },
  { key: 'ccor_threshold' as const, label: 'CSR / CCOR', unit: 'dB', description: 'Rechazo de clutter / relación señal a clutter' },
  { key: 'sig_threshold' as const, label: 'SIG / WSP', unit: 'dB', description: 'Umbral de señal sobre ruido' },
  { key: 'sqi_threshold' as const, label: 'SQI', unit: '', description: 'Índice de calidad de señal (0..1)' },
]

// Las 19 filas del legacy RVP900 (momento/parámetro)
const LEGACY_MOMENTS = [
  { code: 'DBZ', name: 'Reflectividad censurada' },
  { code: 'DBT', name: 'Reflectividad total' },
  { code: 'VEL', name: 'Velocidad Doppler' },
  { code: 'WID', name: 'Ancho espectral' },
  { code: 'ZDR', name: 'Reflectividad diferencial' },
  { code: 'KDP', name: 'Fase diferencial específica' },
  { code: 'PHIDP', name: 'Fase diferencial acumulada' },
  { code: 'RHOHV', name: 'Coeficiente de correlación' },
  { code: 'SQI', name: 'Índice de calidad de señal' },
  { code: 'LDRH', name: 'Razón de despolarización lineal (H)' },
  { code: 'RHOH', name: 'Correlación polarimétrica H' },
  { code: 'PHIH', name: 'Fase polarimétrica H' },
  { code: 'LDRV', name: 'Razón de despolarización lineal (V)' },
  { code: 'RHOV', name: 'Correlación polarimétrica V' },
  { code: 'PHIV', name: 'Fase polarimétrica V' },
  { code: 'HCLASS', name: 'Clasificación de hidrometeoros' },
  { code: 'SNR', name: 'Razón señal a ruido' },
  { code: 'DBZA', name: 'Reflectividad atenuada' },
  { code: 'DBTA', name: 'Reflectividad total atenuada' },
]

async function loadData() {
  loading.value = true
  errorMessage.value = null
  try {
    dspStatus.value = await fetchDspInternalStatus()
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : 'Error cargando estado de umbrales DSP'
  } finally {
    loading.value = false
  }
}

function formatThresholdValue(key: 'log_threshold' | 'ccor_threshold' | 'sig_threshold' | 'sqi_threshold'): string {
  if (!dspStatus.value) return '—'
  const val = dspStatus.value[key]
  if (key === 'sqi_threshold') {
    return val.toFixed(2)
  }
  return `${val.toFixed(1)} dB`
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 overflow-auto p-3 text-xs bg-background text-foreground">
    <!-- Header & Quick Actions -->
    <div class="flex flex-wrap items-center justify-between gap-2 border-b pb-2">
      <div>
        <div class="flex items-center gap-2">
          <h2 class="text-base font-bold tracking-tight">E3 — Thresholds Matrix (Vp)</h2>
          <Badge variant="outline" class="text-xs">Solo lectura</Badge>
        </div>
        <p class="text-muted-foreground text-xs mt-0.5">
          Visualización de umbrales de censura del procesador de señales DSP.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <Button variant="outline" size="sm" :disabled="loading" @click="loadData">
          Actualizar
        </Button>
      </div>
    </div>

    <!-- Error message -->
    <div v-if="errorMessage" class="rounded border border-destructive/50 bg-destructive/10 p-2 text-destructive">
      {{ errorMessage }}
    </div>

    <!-- 4 Umbrales Reales Globales -->
    <Card>
      <CardHeader class="pb-2 pt-3">
        <CardTitle class="text-sm font-semibold flex items-center justify-between">
          <span>Umbrales Reales del Procesador DSP</span>
          <Badge variant="secondary" class="text-xs">4 Umbrales Activos (Globales)</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 pb-3">
        <div
          v-for="t in REAL_THRESHOLDS"
          :key="t.key"
          class="rounded-lg border bg-card p-3 shadow-xs space-y-1"
        >
          <div class="flex items-center justify-between">
            <span class="font-bold text-xs text-foreground">{{ t.label }}</span>
            <Badge variant="outline" class="text-[10px] px-1.5 py-0 border-emerald-500/50 text-emerald-600 dark:text-emerald-400">
              global
            </Badge>
          </div>
          <div class="text-xl font-mono font-bold tracking-tight text-primary">
            {{ formatThresholdValue(t.key) }}
          </div>
          <p class="text-[11px] text-muted-foreground leading-tight">{{ t.description }}</p>
        </div>
      </CardContent>
    </Card>

    <!-- Legacy 19x5 Thresholds Matrix -->
    <Card class="flex-1 min-h-0 flex flex-col">
      <CardHeader class="pb-2 pt-3">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
          <CardTitle class="text-sm font-semibold">
            Matriz Legacy de Umbrales por Momento (RVP900 19×5)
          </CardTitle>
          <span class="text-xs text-muted-foreground">
            Filas no respaldadas por el contrato actual
          </span>
        </div>
      </CardHeader>
      <CardContent class="overflow-x-auto pb-3">
        <div class="rounded border">
          <table class="w-full text-left font-mono text-xs border-collapse">
            <thead>
              <tr class="border-b text-muted-foreground bg-muted/40">
                <th class="py-2 px-3 font-semibold">Momento / Parámetro</th>
                <th class="py-2 px-3 font-semibold text-center">LOG</th>
                <th class="py-2 px-3 font-semibold text-center">CSR</th>
                <th class="py-2 px-3 font-semibold text-center">WSP</th>
                <th class="py-2 px-3 font-semibold text-center">SQI</th>
                <th class="py-2 px-3 font-semibold text-center">PMI</th>
              </tr>
            </thead>
            <tbody>
              <!-- Filas de los 19 momentos legacy, deshabilitadas con texto 'no disponible' -->
              <tr
                v-for="m in LEGACY_MOMENTS"
                :key="m.code"
                class="border-b/50 bg-muted/10 opacity-60 text-muted-foreground select-none"
              >
                <td class="py-1.5 px-3 font-medium">
                  <div class="flex items-center gap-2">
                    <span class="font-bold text-foreground/70">{{ m.code }}</span>
                    <span class="text-[11px] font-sans truncate text-muted-foreground/80">({{ m.name }})</span>
                  </div>
                </td>
                <td class="py-1.5 px-3 text-center text-[11px] italic font-sans">no disponible</td>
                <td class="py-1.5 px-3 text-center text-[11px] italic font-sans">no disponible</td>
                <td class="py-1.5 px-3 text-center text-[11px] italic font-sans">no disponible</td>
                <td class="py-1.5 px-3 text-center text-[11px] italic font-sans">no disponible</td>
                <td class="py-1.5 px-3 text-center text-[11px] italic font-sans">no disponible</td>
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
