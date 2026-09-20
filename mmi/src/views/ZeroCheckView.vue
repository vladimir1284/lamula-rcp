<!--
  ZeroCheckView.vue: Vista G5 — Zero Check (RAVIS §7.4.2).
  Muestreo de piso de ruido del receptor.
-->
<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import JobActionPanel from '@/components/domain/JobActionPanel.vue'
import NoiseLevelReadout from '@/components/domain/NoiseLevelReadout.vue'
import PrecheckList from '@/components/domain/PrecheckList.vue'
import ScheduleInfoRow from '@/components/domain/ScheduleInfoRow.vue'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useGateway } from '@/composables/useGateway'
import type { RoutineResult, ZeroCheckSnapshot } from '@/types/mmi'

const {
  control,
  maintenance,
  halConnected,
  fetchZeroCheck,
  runControlJob,
  cancelControlJob,
} = useGateway()

const snapshot = ref<ZeroCheckSnapshot | null>(null)
const busy = ref(false)
const jobId = ref<string | null>(null)
const result = ref<RoutineResult | null>(null)
const error = ref<string | null>(null)

let pollTimer: ReturnType<typeof setInterval> | null = null

const isControlActive = computed(() => control.value?.mode === 'active')
const isMaintenanceActive = computed(() => maintenance.value?.level === 'MANT')
const isRemoteOk = computed(() => halConnected.value !== false)

// Precondición UI Común: Modo Mantenimiento activo (A4) + Autoridad de Control activa (A3) + ACU/LCU en Remote
const preconditions = computed(() => [
  { label: 'Modo Mantenimiento activo (A4)', ok: isMaintenanceActive.value },
  { label: 'Autoridad de Control activa (A3)', ok: isControlActive.value },
  { label: 'ACU / LCU en Modo Remoto', ok: isRemoteOk.value },
])

const canExecute = computed(() => isMaintenanceActive.value && isControlActive.value && isRemoteOk.value)

async function refresh() {
  try {
    snapshot.value = await fetchZeroCheck()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

async function runZeroCheckJob() {
  busy.value = true
  error.value = null
  jobId.value = null
  try {
    result.value = await runControlJob<RoutineResult>('/api/control/zero-check', undefined, (id) => {
      jobId.value = id
    })
    await refresh()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    busy.value = false
    jobId.value = null
  }
}

async function cancelZeroCheckJob() {
  if (!jobId.value) return
  try {
    await cancelControlJob(jobId.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

onMounted(() => {
  refresh()
  pollTimer = setInterval(refresh, 2000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 overflow-auto p-3">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold text-foreground">Vista G5 — Zero Check</h2>
    </div>

    <!-- Indicador de mediciones actuales de ruido -->
    <NoiseLevelReadout
      :noise-high-dbm="snapshot?.noise_high_dbm"
      :noise-low-dbm="snapshot?.noise_low_dbm"
      :last-run-at-wall="snapshot?.last_run_at_wall"
    />

    <!-- Panel de ejecución manual y precondiciones -->
    <Card>
      <CardHeader>
        <CardTitle class="text-base font-semibold">Ejecución Manual de Muestreo (Zero Check)</CardTitle>
      </CardHeader>
      <CardContent class="flex flex-col gap-4">
        <PrecheckList :checks="preconditions" />
        <JobActionPanel
          run-label="Ejecutar Zero Check"
          busy-text="Ejecutando muestreo de ruido..."
          :busy="busy"
          :job-id="jobId"
          :result="result"
          :error="error"
          :run-disabled="!canExecute"
          @run="runZeroCheckJob"
          @cancel="cancelZeroCheckJob"
        />
      </CardContent>
    </Card>

    <!-- Fila de información sobre planificación de fondo -->
    <ScheduleInfoRow
      :interval-s="snapshot?.interval_s ?? 3600"
      :enabled="snapshot?.enabled ?? true"
      :last-run-at-wall="snapshot?.last_run_at_wall"
      :next-run-at-wall="snapshot?.next_run_at_wall"
    />
  </div>
</template>
