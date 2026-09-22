<!--
  CalibrationHubView.vue: Vista G1 — Calibration Hub (RAVIS §7.4 + §14).
  Vista de agregación pura de solo lectura: estado de precondiciones,
  fecha/resultado de última calibración por tipo y registro histórico de actividades.
-->
<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import PrecheckList from '@/components/domain/PrecheckList.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useGateway } from '@/composables/useGateway'
import type { CalibrationLogEntry, RadarConstantSnapshot, ZeroCheckSnapshot } from '@/types/mmi'

const emit = defineEmits<{
  (e: 'navigate', viewId: string): void
}>()

const {
  control,
  maintenance,
  halConnected,
  fetchCalibrationLog,
  fetchZeroCheck,
  fetchRadarConstant,
} = useGateway()

const zeroCheckSnapshot = ref<ZeroCheckSnapshot | null>(null)
const radarConstantSnapshot = ref<RadarConstantSnapshot | null>(null)
const logs = ref<CalibrationLogEntry[]>([])
const error = ref<string | null>(null)
const busy = ref(false)

let pollTimer: ReturnType<typeof setInterval> | null = null

const isControlActive = computed(() => control.value?.mode === 'active')
const isMaintenanceActive = computed(() => maintenance.value?.level === 'MANT')
const isRemoteOk = computed(() => halConnected.value !== false)

// Precondiciones de UI: Mantenimiento (A4) + Autoridad Activa (A3) + Conexión HAL/Remote
const preconditions = computed(() => [
  { label: 'Modo Mantenimiento activo (A4)', ok: isMaintenanceActive.value },
  { label: 'Autoridad de Control activa (A3)', ok: isControlActive.value },
  { label: 'ACU / LCU en Modo Remoto / Conectado', ok: isRemoteOk.value },
])

async function refreshData() {
  try {
    const [zCheck, rConst, logEntries] = await Promise.all([
      fetchZeroCheck().catch(() => null),
      fetchRadarConstant().catch(() => null),
      fetchCalibrationLog().catch(() => []),
    ])
    zeroCheckSnapshot.value = zCheck
    radarConstantSnapshot.value = rConst
    logs.value = logEntries
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

// Helpers para extraer última entrada de log por procedimiento
function getLatestLog(procedureSubstring: string): CalibrationLogEntry | undefined {
  const sub = procedureSubstring.toLowerCase()
  return logs.value.find((l) => l.procedure.toLowerCase().includes(sub))
}

const lastTxPowerLog = computed(() => getLatestLog('tx power') || getLatestLog('g3'))
const lastTxSamplingLog = computed(() => getLatestLog('tx sampling') || getLatestLog('g2'))
const lastSinglePointLog = computed(() => getLatestLog('single point') || getLatestLog('g4'))

function navigateTo(viewId: string) {
  emit('navigate', viewId)
}

function formatDate(isoStr?: string | null): string {
  if (!isoStr) return '—'
  try {
    const d = new Date(isoStr)
    return d.toLocaleString()
  } catch {
    return isoStr
  }
}

function getOutcomeBadgeVariant(severity?: string | null): 'default' | 'destructive' | 'outline' | 'secondary' {
  if (severity === 'error') return 'destructive'
  if (severity === 'warn') return 'secondary'
  if (severity === 'info') return 'default'
  return 'outline'
}

onMounted(() => {
  refreshData()
  pollTimer = setInterval(refreshData, 5000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 overflow-auto p-4">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-3">
      <div>
        <div class="flex items-center gap-2">
          <h2 class="text-lg font-bold tracking-tight text-foreground">
            G1 — Calibration Hub
          </h2>
          <Badge variant="outline" class="text-xs">
            Vista de Agregación
          </Badge>
        </div>
        <p class="text-xs text-muted-foreground mt-0.5">
          RAVIS §7.4 + §14 — Estado de precondiciones, snapshot y resumen de procedimientos de calibración.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <Button size="sm" variant="outline" class="h-8 text-xs" @click="refreshData">
          Actualizar Datos
        </Button>
        <Button size="sm" variant="secondary" class="h-8 text-xs" @click="navigateTo('calibration-log')">
          Ver Log Completo (G8)
        </Button>
      </div>
    </div>

    <!-- Error Callout -->
    <div v-if="error" class="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-xs text-destructive">
      {{ error }}
    </div>

    <!-- Precondiciones y Estado Global -->
    <div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
      <Card class="lg:col-span-1">
        <CardHeader class="pb-2">
          <CardTitle class="text-sm font-semibold">Estado de Precondiciones</CardTitle>
          <CardDescription class="text-xs">
            Verificación requerida antes de iniciar procedimientos de calibración
          </CardDescription>
        </CardHeader>
        <CardContent class="pt-2">
          <PrecheckList :checks="preconditions" />
        </CardContent>
      </Card>

      <!-- Resumen General -->
      <Card class="lg:col-span-2">
        <CardHeader class="pb-2">
          <CardTitle class="text-sm font-semibold">Resumen del Estado del Sistema</CardTitle>
          <CardDescription class="text-xs">
            Parámetros de calibración derivados y estatus de rutinas automáticas
          </CardDescription>
        </CardHeader>
        <CardContent class="grid grid-cols-1 gap-4 sm:grid-cols-3 pt-2 text-xs">
          <div class="rounded-lg border bg-muted/30 p-3">
            <span class="font-medium text-muted-foreground block mb-1">Zero Check (Ruido)</span>
            <div class="font-mono text-base font-bold text-emerald-400">
              {{ zeroCheckSnapshot?.noise_high_dbm !== null && zeroCheckSnapshot?.noise_high_dbm !== undefined ? `${zeroCheckSnapshot.noise_high_dbm.toFixed(1)} dBm` : '—' }}
            </div>
            <span class="text-[11px] text-muted-foreground">
              Último: {{ formatDate(zeroCheckSnapshot?.last_run_at_wall) }}
            </span>
          </div>

          <div class="rounded-lg border bg-muted/30 p-3">
            <span class="font-medium text-muted-foreground block mb-1">Constante del Radar (C_r)</span>
            <div class="font-mono text-base font-bold text-emerald-400">
              {{ radarConstantSnapshot?.radar_constant_db !== undefined ? `${radarConstantSnapshot.radar_constant_db.toFixed(2)} dB` : '—' }}
            </div>
            <span class="text-[11px] text-muted-foreground">
              Pulso: {{ radarConstantSnapshot?.params?.pulse_width_us ?? '—' }} µs
            </span>
          </div>

          <div class="rounded-lg border bg-muted/30 p-3">
            <span class="font-medium text-muted-foreground block mb-1">Registros en Log</span>
            <div class="font-mono text-base font-bold text-foreground">
              {{ logs.length }}
            </div>
            <span class="text-[11px] text-muted-foreground">
              Último evento: {{ logs.length > 0 ? formatDate(logs[0].at_wall) : 'Sin entradas' }}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Tipos de Calibración / Accesos directos -->
    <div class="space-y-2">
      <h3 class="text-sm font-semibold text-foreground">Procedimientos de Calibración</h3>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        <!-- 1. Zero Check (G5) -->
        <Card class="flex flex-col justify-between">
          <CardHeader class="pb-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-emerald-500 uppercase tracking-wider">G5 — Zero Check</span>
              <Badge variant="outline" class="text-[10px]">Periódico / Manual</Badge>
            </div>
            <CardTitle class="text-sm">Zero Check</CardTitle>
            <CardDescription class="text-xs">Muestreo y sustracción del piso de ruido del receptor.</CardDescription>
          </CardHeader>
          <CardContent class="space-y-2 text-xs">
            <div class="flex justify-between border-t pt-2">
              <span class="text-muted-foreground">Última ejecución:</span>
              <span class="font-mono">{{ formatDate(zeroCheckSnapshot?.last_run_at_wall) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-muted-foreground">Ruido High / Low:</span>
              <span class="font-mono">
                {{ zeroCheckSnapshot?.noise_high_dbm ?? '—' }} / {{ zeroCheckSnapshot?.noise_low_dbm ?? '—' }} dBm
              </span>
            </div>
            <Button size="sm" variant="outline" class="w-full mt-2 text-xs h-7" @click="navigateTo('zero-check')">
              Abrir Vista G5
            </Button>
          </CardContent>
        </Card>

        <!-- 2. TX Power Calibration (G3) -->
        <Card class="flex flex-col justify-between">
          <CardHeader class="pb-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-emerald-500 uppercase tracking-wider">G3 — TX Power Calibration</span>
              <Badge variant="outline" class="text-[10px]">Wizard Guiado</Badge>
            </div>
            <CardTitle class="text-sm">Calibración de Potencia TX</CardTitle>
            <CardDescription class="text-xs">Ajuste guiado de potencia de transmisión por ancho de pulso.</CardDescription>
          </CardHeader>
          <CardContent class="space-y-2 text-xs">
            <div class="flex justify-between border-t pt-2">
              <span class="text-muted-foreground">Última ejecución:</span>
              <span class="font-mono">{{ formatDate(lastTxPowerLog?.at_wall) }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-muted-foreground">Último resultado:</span>
              <Badge :variant="getOutcomeBadgeVariant(lastTxPowerLog?.severity)" class="text-[10px]">
                {{ lastTxPowerLog?.message || 'Sin registro' }}
              </Badge>
            </div>
            <Button size="sm" variant="outline" class="w-full mt-2 text-xs h-7" @click="navigateTo('tx-power-calibration')">
              Abrir Vista G3
            </Button>
          </CardContent>
        </Card>

        <!-- 3. Radar Constant Parameters (G7) -->
        <Card class="flex flex-col justify-between">
          <CardHeader class="pb-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-emerald-500 uppercase tracking-wider">G7 — Radar Constant</span>
              <Badge variant="outline" class="text-[10px]">Parámetros Estáticos</Badge>
            </div>
            <CardTitle class="text-sm">Constante del Radar</CardTitle>
            <CardDescription class="text-xs">Parámetros de pérdidas, geometría de antena y figura de ruido.</CardDescription>
          </CardHeader>
          <CardContent class="space-y-2 text-xs">
            <div class="flex justify-between border-t pt-2">
              <span class="text-muted-foreground">Constante C_r:</span>
              <span class="font-mono font-semibold">{{ radarConstantSnapshot?.radar_constant_db !== undefined ? `${radarConstantSnapshot.radar_constant_db.toFixed(2)} dB` : '—' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-muted-foreground">Ganancia Antena:</span>
              <span class="font-mono">{{ radarConstantSnapshot?.params?.antenna_gain_db ?? '—' }} dB</span>
            </div>
            <Button size="sm" variant="outline" class="w-full mt-2 text-xs h-7" @click="navigateTo('radar-constant')">
              Abrir Vista G7
            </Button>
          </CardContent>
        </Card>

        <!-- 4. TX Sampling Adjust (G2) -->
        <Card class="flex flex-col justify-between opacity-80">
          <CardHeader class="pb-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-muted-foreground uppercase tracking-wider">G2 — TX Sampling</span>
              <Badge variant="secondary" class="text-[10px]">Pendiente P2</Badge>
            </div>
            <CardTitle class="text-sm">TX Sampling Adjust</CardTitle>
            <CardDescription class="text-xs">Temporizado de muestreo del pulso transmitido.</CardDescription>
          </CardHeader>
          <CardContent class="space-y-2 text-xs">
            <div class="flex justify-between border-t pt-2">
              <span class="text-muted-foreground">Última ejecución:</span>
              <span class="font-mono">{{ formatDate(lastTxSamplingLog?.at_wall) }}</span>
            </div>
            <Button size="sm" variant="ghost" disabled class="w-full mt-2 text-xs h-7">
              Vista no disponible
            </Button>
          </CardContent>
        </Card>

        <!-- 5. Single Point Calibration (G4) -->
        <Card class="flex flex-col justify-between opacity-80">
          <CardHeader class="pb-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-muted-foreground uppercase tracking-wider">G4 — Single Point</span>
              <Badge variant="secondary" class="text-[10px]">Pendiente P2</Badge>
            </div>
            <CardTitle class="text-sm">Single Point Calibration</CardTitle>
            <CardDescription class="text-xs">Inyección de señal calibrada para determinar respuesta lineal.</CardDescription>
          </CardHeader>
          <CardContent class="space-y-2 text-xs">
            <div class="flex justify-between border-t pt-2">
              <span class="text-muted-foreground">Última ejecución:</span>
              <span class="font-mono">{{ formatDate(lastSinglePointLog?.at_wall) }}</span>
            </div>
            <Button size="sm" variant="ghost" disabled class="w-full mt-2 text-xs h-7">
              Vista no disponible
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>

    <!-- Registro de Actividades Recientes (Historial de Calibration Log) -->
    <Card>
      <CardHeader class="pb-2 flex flex-row items-center justify-between">
        <div>
          <CardTitle class="text-sm font-semibold">Registro Histórico de Calibraciones (Recientes)</CardTitle>
          <CardDescription class="text-xs">Últimos eventos registrados en /api/calibration-log</CardDescription>
        </div>
        <Button size="sm" variant="ghost" class="text-xs h-7" @click="navigateTo('calibration-log')">
          Ver Todo →
        </Button>
      </CardHeader>
      <CardContent class="pt-0">
        <div v-if="logs.length === 0" class="py-6 text-center text-xs text-muted-foreground">
          No hay registros de calibración grabados aún.
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="border-b text-muted-foreground">
              <tr>
                <th class="py-2 pr-3 font-medium">Fecha / Hora</th>
                <th class="py-2 px-3 font-medium">Procedimiento</th>
                <th class="py-2 px-3 font-medium">Operador</th>
                <th class="py-2 px-3 font-medium">Severidad</th>
                <th class="py-2 pl-3 font-medium">Mensaje</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border/50 font-mono text-[11px]">
              <tr v-for="(entry, idx) in logs.slice(0, 5)" :key="idx" class="hover:bg-muted/20">
                <td class="py-2 pr-3 whitespace-nowrap text-muted-foreground">{{ formatDate(entry.at_wall) }}</td>
                <td class="py-2 px-3 font-medium text-foreground whitespace-nowrap">{{ entry.procedure }}</td>
                <td class="py-2 px-3 text-muted-foreground whitespace-nowrap">{{ entry.actor }}</td>
                <td class="py-2 px-3 whitespace-nowrap">
                  <Badge :variant="getOutcomeBadgeVariant(entry.severity)" class="text-[10px] px-1.5 py-0">
                    {{ entry.severity }}
                  </Badge>
                </td>
                <td class="py-2 pl-3 text-foreground">{{ entry.message }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
