<!--
  TxPowerCalibrationView.vue: Vista G3 — TX Power Calibration (RAVIS §7.4.1 / §14).
  Wizard guiado de calibración de potencia TX con entrada manual de lecturas y temporizador de caldeo de 20 min.
-->
<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import JobActionPanel from '@/components/domain/JobActionPanel.vue'
import PrecheckList from '@/components/domain/PrecheckList.vue'
import WarmupTimer from '@/components/domain/WarmupTimer.vue'
import WizardStepper from '@/components/domain/WizardStepper.vue'
import type { WizardStepItem } from '@/components/domain/WizardStepper.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useGateway } from '@/composables/useGateway'
import type { CalibrationLogEntry, ControlJobStatusResponse, PowerMonitorSnapshot, RoutineResult } from '@/types/mmi'

const {
  control,
  maintenance,
  halConnected,
  fetchPowerMonitor,
  fetchCalibrationLog,
  advanceControlJobStep,
  runControlJob,
  cancelControlJob,
} = useGateway()

const powerSnapshot = ref<PowerMonitorSnapshot | null>(null)
const calibrationLogs = ref<CalibrationLogEntry[]>([])
const busy = ref(false)
const jobId = ref<string | null>(null)
const currentJobStatus = ref<ControlJobStatusResponse | null>(null)
const result = ref<RoutineResult | null>(null)
const error = ref<string | null>(null)

// Temporizador de caldeo (20 min)
const isWarmupComplete = ref(false)
const isRadiating = computed(() => powerSnapshot.value?.radiating ?? false)

// Precondiciones
const isControlActive = computed(() => control.value?.mode === 'active')
const isMaintenanceActive = computed(() => maintenance.value?.level === 'MANT')
const isRemoteOk = computed(() => halConnected.value !== false)

const preconditions = computed(() => [
  { label: 'Modo Mantenimiento activo (MANT)', ok: isMaintenanceActive.value },
  { label: 'Autoridad de Control activa (ACTIVE)', ok: isControlActive.value },
  { label: 'ACU / LCU en Modo Remoto', ok: isRemoteOk.value },
  { label: 'Caldeo de radiación completo (20 min)', ok: isWarmupComplete.value },
])

const canExecute = computed(
  () => isMaintenanceActive.value && isControlActive.value && isRemoteOk.value && isWarmupComplete.value,
)

// Datos del formulario interactivo por paso
const inputMeasuredPowerKw = ref<number>(250.0)
const inputCouplerOffsetDb = ref<number>(0.0)
const isSubmittingStep = ref(false)

// Pasos del Wizard
const wizardSteps = computed<WizardStepItem[]>(() => {
  const cStep = currentJobStatus.value?.current_step ?? 1
  const jStatus = currentJobStatus.value?.status

  if (result.value) {
    const isSuccess = result.value.outcome === 'success'
    return [
      { title: 'Verificación de Precondiciones y Caldeo', status: 'completed' },
      { title: 'Entrada de Potencia de Referencia', status: 'completed' },
      { title: 'Ajuste de Desfase de Acoplador', status: isSuccess ? 'completed' : 'failed' },
    ]
  }

  if (!busy.value) {
    return [
      { title: 'Verificación de Precondiciones y Caldeo', description: 'Requiere 20 min de radiación activa', status: 'pending' },
      { title: 'Entrada de Potencia de Referencia', description: 'Lectura con medidor de potencia externo (kW)', status: 'pending' },
      { title: 'Ajuste de Desfase de Acoplador', description: 'Ajuste fino de atenuación (dB)', status: 'pending' },
    ]
  }

  return [
    {
      title: 'Verificación de Precondiciones y Caldeo',
      status: cStep > 1 ? 'completed' : cStep === 1 ? (jStatus === 'awaiting_operator_input' ? 'active' : 'active') : 'pending',
    },
    {
      title: 'Entrada de Potencia de Referencia',
      description: 'Ingrese la potencia pico medida en kW',
      status: cStep > 2 ? 'completed' : cStep === 2 ? 'active' : 'pending',
    },
    {
      title: 'Ajuste de Desfase de Acoplador',
      description: 'Ajuste fino de atenuación (dB)',
      status: cStep > 3 ? 'completed' : cStep === 3 ? 'active' : 'pending',
    },
  ]
})

let pollTimer: ReturnType<typeof setInterval> | null = null

async function refresh() {
  try {
    powerSnapshot.value = await fetchPowerMonitor()
    calibrationLogs.value = await fetchCalibrationLog()
  } catch (e) {
    // best effort error handling
  }
}

function handleWarmupChange(complete: boolean) {
  isWarmupComplete.value = complete
}

async function startCalibrationWizard() {
  busy.value = true
  error.value = null
  jobId.value = null
  currentJobStatus.value = null
  result.value = null

  try {
    result.value = await runControlJob<RoutineResult>(
      '/api/control/tx-power-calibration',
      undefined,
      (id) => {
        jobId.value = id
      },
      (job) => {
        currentJobStatus.value = job
      },
    )
    await refresh()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    busy.value = false
    jobId.value = null
    currentJobStatus.value = null
  }
}

async function cancelWizard() {
  if (!jobId.value) return
  try {
    await cancelControlJob(jobId.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

async function submitStepInput() {
  if (!jobId.value) return
  isSubmittingStep.value = true
  try {
    const cStep = currentJobStatus.value?.current_step
    let payloadData: Record<string, unknown> = {}
    if (cStep === 2) {
      payloadData = { measured_power_kw: Number(inputMeasuredPowerKw.value) }
    } else if (cStep === 3) {
      payloadData = { coupler_offset_db: Number(inputCouplerOffsetDb.value) }
    }

    const updatedJob = await advanceControlJobStep(jobId.value, payloadData)
    currentJobStatus.value = updatedJob
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    isSubmittingStep.value = false
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
      <h2 class="text-lg font-semibold text-foreground">Vista G3 — Calibración de Potencia TX</h2>
    </div>

    <!-- Temporizador de Caldeo Obligatorio (20 min) -->
    <WarmupTimer
      :radiating="isRadiating"
      :required-seconds="1200"
      @warmup-change="handleWarmupChange"
    />

    <!-- Layout principal de 2 columnas: Wizard a la izq, Precondiciones/Acción a la der -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <!-- Columna 1: Stepper del Wizard e Inserción de Datos -->
      <Card>
        <CardHeader>
          <CardTitle class="text-base font-semibold">Procedimiento de Calibración</CardTitle>
        </CardHeader>
        <CardContent class="flex flex-col gap-6">
          <WizardStepper :steps="wizardSteps" :current-step-index="(currentJobStatus?.current_step ?? 1) - 1" />

          <!-- Formulario para el paso interactivo activo -->
          <div
            v-if="busy && currentJobStatus?.status === 'awaiting_operator_input'"
            class="flex flex-col gap-3 rounded-lg border border-border bg-card p-4"
          >
            <div class="flex items-center justify-between">
              <span class="text-sm font-semibold text-primary">
                Paso {{ currentJobStatus.current_step }}: {{ currentJobStatus.step_name }}
              </span>
              <Badge variant="outline">Aguardando Operador</Badge>
            </div>
            <p class="text-xs text-muted-foreground">{{ currentJobStatus.prompt }}</p>

            <!-- Inputs según el paso actual -->
            <div v-if="currentJobStatus.current_step === 2" class="flex flex-col gap-2">
              <label class="text-xs font-medium">Potencia Pico Medida en Medidor Externo (kW):</label>
              <Input v-model.number="inputMeasuredPowerKw" type="number" step="0.1" class="w-full" />
            </div>

            <div v-else-if="currentJobStatus.current_step === 3" class="flex flex-col gap-2">
              <label class="text-xs font-medium">Offset de Atenuación de Acoplador (dB):</label>
              <Input v-model.number="inputCouplerOffsetDb" type="number" step="0.01" class="w-full" />
            </div>

            <Button :disabled="isSubmittingStep" @click="submitStepInput">
              {{ isSubmittingStep ? 'Enviando...' : 'Confirmar y Avanzar Paso' }}
            </Button>
          </div>
        </CardContent>
      </Card>

      <!-- Columna 2: Precondiciones y Control de Ejecución del Job -->
      <Card>
        <CardHeader>
          <CardTitle class="text-base font-semibold">Verificación de Precondiciones y Control</CardTitle>
        </CardHeader>
        <CardContent class="flex flex-col gap-4">
          <PrecheckList :checks="preconditions" />

          <JobActionPanel
            run-label="Iniciar Wizard de Calibración"
            busy-text="Wizard en ejecución..."
            :busy="busy"
            :job-id="jobId"
            :result="result"
            :error="error"
            :run-disabled="!canExecute"
            @run="startCalibrationWizard"
            @cancel="cancelWizard"
          />
        </CardContent>
      </Card>
    </div>

    <!-- Registro Histórico de Calibraciones (Calibration Log) -->
    <Card>
      <CardHeader>
        <CardTitle class="text-base font-semibold">Histórico de Actividades de Calibración (G8)</CardTitle>
      </CardHeader>
      <CardContent>
        <div v-if="calibrationLogs.length === 0" class="text-xs text-muted-foreground">
          No hay registros de calibración.
        </div>
        <ul v-else class="flex flex-col gap-2 text-xs">
          <li
            v-for="(log, idx) in calibrationLogs"
            :key="idx"
            class="flex flex-col gap-0.5 border-b border-border pb-2 last:border-0"
          >
            <div class="flex items-center justify-between">
              <span class="font-medium text-foreground">{{ log.procedure }} — {{ log.message }}</span>
              <span class="text-muted-foreground">{{ new Date(log.at_wall).toLocaleString() }}</span>
            </div>
            <div class="flex items-center gap-2 text-muted-foreground">
              <span>Operador: {{ log.actor }}</span>
              <span v-if="log.detail">— Detail: {{ log.detail }}</span>
            </div>
          </li>
        </ul>
      </CardContent>
    </Card>
  </div>
</template>
