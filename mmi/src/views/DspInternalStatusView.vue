<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import ConfirmDangerDialog from '@/components/domain/ConfirmDangerDialog.vue'
import RawStatusWordsPanel from '@/components/domain/RawStatusWordsPanel.vue'
import { useGateway } from '@/composables/useGateway'
import type { DspInternalStatusSnapshot } from '@/types/mmi'

const { maintenance, fetchDspInternalStatus, resetDspCounters } = useGateway()

const dspStatus = ref<DspInternalStatusSnapshot | null>(null)
const loading = ref(false)
const errorMessage = ref<string | null>(null)

const showResetDialog = ref(false)
const resetting = ref(false)
const resetSuccessMessage = ref<string | null>(null)

const isMaintenanceUnlocked = computed(() => maintenance.value?.level === 'MANT')

async function loadData() {
  loading.value = true
  errorMessage.value = null
  try {
    dspStatus.value = await fetchDspInternalStatus()
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : 'Error cargando estado interno DSP'
  } finally {
    loading.value = false
  }
}

async function handleConfirmReset() {
  resetting.value = true
  resetSuccessMessage.value = null
  try {
    const res = await resetDspCounters()
    resetSuccessMessage.value = res.message
    showResetDialog.value = false
    await loadData()
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : 'Error al reiniciar contadores'
  } finally {
    resetting.value = false
  }
}

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400)
  const h = Math.floor((seconds % 86400) / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (d > 0) return `${d}d ${h}h ${m}m ${s}s`
  if (h > 0) return `${h}h ${m}m ${s}s`
  if (m > 0) return `${m}m ${s}s`
  return `${s}s`
}

function phaseName(phase: number): string {
  switch (phase) {
    case 0:
      return 'SETUP'
    case 1:
      return 'RUNNING'
    case 2:
      return 'FAULT'
    default:
      return `FASE ${phase}`
  }
}

function severityLabel(sev: number): { text: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' } {
  switch (sev) {
    case 0:
      return { text: 'INFO', variant: 'outline' }
    case 1:
      return { text: 'WARNING', variant: 'secondary' }
    case 2:
      return { text: 'FAULT', variant: 'destructive' }
    case 3:
      return { text: 'CONFIG_ERROR', variant: 'destructive' }
    default:
      return { text: `SEV ${sev}`, variant: 'default' }
  }
}

const triggerDriftNs = computed(() => {
  if (!dspStatus.value) return 0
  return dspStatus.value.trigger_period_meas_ns - dspStatus.value.trigger_period_cmd_ns
})

const binsOkPercent = computed(() => {
  if (!dspStatus.value || dspStatus.value.bins_total === 0) return 100
  return ((dspStatus.value.bins_ok / dspStatus.value.bins_total) * 100).toFixed(2)
})

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 overflow-auto p-3 text-xs">
    <!-- Header & Quick Actions -->
    <div class="flex flex-wrap items-center justify-between gap-2 border-b pb-2">
      <div>
        <h2 class="text-base font-bold tracking-tight">E12 — DSP Internal Status (V / Vz)</h2>
        <p class="text-muted-foreground text-xs">
          Telemetría de diagnóstico interno, contadores GPARM y palabras de estado del procesador de señales
        </p>
      </div>

      <div class="flex items-center gap-2">
        <Button variant="outline" size="sm" :disabled="loading" @click="loadData">
          Actualizar
        </Button>
        <Button
          variant="destructive"
          size="sm"
          :disabled="!isMaintenanceUnlocked"
          @click="showResetDialog = true"
        >
          Reiniciar Contadores (Vz)
        </Button>
      </div>
    </div>

    <!-- Feedback messages -->
    <div v-if="errorMessage" class="rounded border border-destructive/50 bg-destructive/10 p-2 text-destructive">
      {{ errorMessage }}
    </div>
    <div v-if="resetSuccessMessage" class="rounded border border-emerald-500/50 bg-emerald-500/10 p-2 text-emerald-600 dark:text-emerald-400">
      {{ resetSuccessMessage }}
    </div>
    <div v-if="!isMaintenanceUnlocked" class="rounded border border-amber-500/30 bg-amber-500/10 p-2 text-amber-700 dark:text-amber-300">
      Aviso: El reinicio de contadores requiere nivel de mantenimiento MANT activo.
    </div>

    <div v-if="dspStatus" class="space-y-4">
      <!-- General Status Card -->
      <Card>
        <CardHeader class="pb-2">
          <CardTitle class="text-sm font-semibold">Resumen General del Procesador</CardTitle>
        </CardHeader>
        <CardContent class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          <div>
            <span class="text-muted-foreground block">Estado Enlace</span>
            <Badge :variant="dspStatus.connected ? 'default' : 'destructive'">
              {{ dspStatus.connected ? 'Conectado' : 'Desconectado' }}
            </Badge>
          </div>

          <div>
            <span class="text-muted-foreground block">Fase DSP</span>
            <Badge variant="outline">{{ phaseName(dspStatus.phase) }}</Badge>
          </div>

          <div>
            <span class="text-muted-foreground block">Severidad</span>
            <Badge :variant="severityLabel(dspStatus.severity).variant">
              {{ severityLabel(dspStatus.severity).text }}
            </Badge>
          </div>

          <div>
            <span class="text-muted-foreground block">Uptime</span>
            <span class="font-mono font-medium">{{ formatUptime(dspStatus.uptime_s) }}</span>
          </div>

          <div>
            <span class="text-muted-foreground block">Último Error</span>
            <span class="font-mono font-medium">0x{{ dspStatus.last_error.toString(16).padStart(4, '0').toUpperCase() }}</span>
          </div>

          <div>
            <span class="text-muted-foreground block">Secuencia Config</span>
            <span class="font-mono font-medium">#{{ dspStatus.config_seq }}</span>
          </div>
        </CardContent>
      </Card>

      <!-- Radial & Gate Telemetry (GPARM) -->
      <Card>
        <CardHeader class="pb-2">
          <CardTitle class="text-sm font-semibold">Contadores de Adquisición y Triggers (GPARM)</CardTitle>
        </CardHeader>
        <CardContent class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="space-y-1">
            <span class="text-muted-foreground block">Radiales Entrada (`rays_in`)</span>
            <span class="text-sm font-mono font-bold">{{ dspStatus.rays_in.toLocaleString() }}</span>
          </div>

          <div class="space-y-1">
            <span class="text-muted-foreground block">Radiales Salida (`rays_out`)</span>
            <span class="text-sm font-mono font-bold">{{ dspStatus.rays_out.toLocaleString() }}</span>
          </div>

          <div class="space-y-1">
            <span class="text-muted-foreground block">Radiales Descartados (`rays_dropped`)</span>
            <span class="text-sm font-mono font-bold" :class="dspStatus.rays_dropped > 0 ? 'text-destructive' : ''">
              {{ dspStatus.rays_dropped.toLocaleString() }}
            </span>
          </div>

          <div class="space-y-1">
            <span class="text-muted-foreground block">Profundidad Cola Process</span>
            <span class="text-sm font-mono font-bold">{{ dspStatus.queue_depth }}</span>
          </div>

          <div class="space-y-1">
            <span class="text-muted-foreground block">Celdas Procesadas OK</span>
            <span class="text-sm font-mono font-bold">
              {{ dspStatus.bins_ok.toLocaleString() }} / {{ dspStatus.bins_total.toLocaleString() }} ({{ binsOkPercent }}%)
            </span>
          </div>

          <div class="space-y-1">
            <span class="text-muted-foreground block">Periodo Trigger Comandado</span>
            <span class="text-sm font-mono font-bold">{{ (dspStatus.trigger_period_cmd_ns / 1000).toFixed(1) }} µs</span>
          </div>

          <div class="space-y-1">
            <span class="text-muted-foreground block">Periodo Trigger Medido</span>
            <span class="text-sm font-mono font-bold">{{ (dspStatus.trigger_period_meas_ns / 1000).toFixed(1) }} µs</span>
          </div>

          <div class="space-y-1">
            <span class="text-muted-foreground block">Deriva de Trigger</span>
            <span class="text-sm font-mono font-bold" :class="Math.abs(triggerDriftNs) > 1000 ? 'text-amber-500' : ''">
              {{ triggerDriftNs }} ns
            </span>
          </div>
        </CardContent>
      </Card>

      <!-- Geometry & Processing Parameters -->
      <Card>
        <CardHeader class="pb-2">
          <CardTitle class="text-sm font-semibold">Parámetros de Geometría y Configuración Actual</CardTitle>
        </CardHeader>
        <CardContent class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <span class="text-muted-foreground block">Canales RX</span>
            <span class="font-mono font-semibold">{{ dspStatus.n_rx_channels }}</span>
          </div>
          <div>
            <span class="text-muted-foreground block">Número de Celdas (`n_gates`)</span>
            <span class="font-mono font-semibold">{{ dspStatus.n_gates }}</span>
          </div>
          <div>
            <span class="text-muted-foreground block">Pulsos por Rayo (`n_pulses`)</span>
            <span class="font-mono font-semibold">{{ dspStatus.n_pulses }}</span>
          </div>
          <div>
            <span class="text-muted-foreground block">PRF Efectiva</span>
            <span class="font-mono font-semibold">{{ dspStatus.prf_hz.toFixed(1) }} Hz</span>
          </div>
          <div>
            <span class="text-muted-foreground block">Espaciado Celdas</span>
            <span class="font-mono font-semibold">{{ dspStatus.gate_spacing_m }} m</span>
          </div>
          <div>
            <span class="text-muted-foreground block">Umbral SQI</span>
            <span class="font-mono font-semibold">{{ dspStatus.sqi_threshold }}</span>
          </div>
          <div>
            <span class="text-muted-foreground block">Umbral SIG</span>
            <span class="font-mono font-semibold">{{ dspStatus.sig_threshold }} dB</span>
          </div>
          <div>
            <span class="text-muted-foreground block">Filtro RFI</span>
            <span class="font-mono font-semibold">{{ dspStatus.rfi_filter === 0 ? 'Desactivado' : `Modo ${dspStatus.rfi_filter}` }}</span>
          </div>
        </CardContent>
      </Card>

      <!-- Channel Noise & Offsets -->
      <Card>
        <CardHeader class="pb-2">
          <CardTitle class="text-sm font-semibold">Mediciones por Canal RX (Ruido y Offset DC)</CardTitle>
        </CardHeader>
        <CardContent class="overflow-x-auto">
          <table class="w-full text-left font-mono text-xs">
            <thead>
              <tr class="border-b text-muted-foreground">
                <th class="py-1">Canal</th>
                <th class="py-1">Nivel Ruido (dBm)</th>
                <th class="py-1">Offset DC (I)</th>
                <th class="py-1">Offset DC (Q)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ch in dspStatus.n_rx_channels" :key="ch - 1" class="border-b/50">
                <td class="py-1 font-sans font-medium">Canal {{ ch - 1 }}</td>
                <td class="py-1">{{ dspStatus.noise_floor_dbm[ch - 1]?.toFixed(2) ?? '—' }} dBm</td>
                <td class="py-1">{{ dspStatus.dc_offset_i[ch - 1]?.toFixed(4) ?? '—' }}</td>
                <td class="py-1">{{ dspStatus.dc_offset_q[ch - 1]?.toFixed(4) ?? '—' }}</td>
              </tr>
            </tbody>
          </table>
        </CardContent>
      </Card>

      <!-- Raw Status Words Panel -->
      <RawStatusWordsPanel
        :bite-flags="dspStatus.bite_flags"
        :capability-flags="dspStatus.capability_flags"
      />
    </div>

    <!-- Confirm Danger Dialog for Vz Reset -->
    <ConfirmDangerDialog
      v-model:open="showResetDialog"
      title="Reiniciar Contadores de Trigger (Vz)"
      description="Esta acción reiniciará los contadores acumulados de radiales y triggers en el procesador DSP."
      action-label="Reiniciar Contadores"
      require-typing="REINICIAR"
      :loading="resetting"
      :consequences="[
        'Los contadores de radiales de entrada, salida y descartados volverán a 0.',
        'Se enviará el mandato de control RESET_COUNTERS (Vz) al hardware DSP.'
      ]"
      @confirm="handleConfirmReset"
    />
  </div>
</template>
