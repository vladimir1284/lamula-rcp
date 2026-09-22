<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import WizardStepper, { type WizardStepItem } from '@/components/domain/WizardStepper.vue'
import OperatorPromptDialog from '@/components/domain/OperatorPromptDialog.vue'
import UnsavedResultBanner from '@/components/domain/UnsavedResultBanner.vue'
import { useGateway } from '@/composables/useGateway'
import type { CalibrationLogEntry, ControlJobStatusResponse, RoutineResult, SinglePointCalibrationMode } from '@/types/mmi'

const {
  control,
  maintenance,
  halConnected,
  fetchCalibrationLog,
  advanceControlJobStep,
  runControlJob,
  saveSinglePointCalibrationResult,
} = useGateway()

const mode = ref<SinglePointCalibrationMode>('auto')
const running = ref(false)
const currentJobId = ref<string | null>(null)
const stepIndex = ref(1)
const promptOpen = ref(false)
const promptTitle = ref('')
const promptMessage = ref('')
const promptLabel = ref<string | undefined>()
const promptDefaultValue = ref<number | undefined>()
const promptInputKey = ref<string>('')

const isSaved = ref(true)
const savingResult = ref(false)
const routineResult = ref<RoutineResult | null>(null)
const calibrationLogs = ref<CalibrationLogEntry[]>([])
const error = ref<string | null>(null)

// Precondiciones tomadas del estado real del gateway, no de props -- mismo
// patron que TxPowerCalibrationView.vue (G3).
const isMaintenanceUnlocked = computed(() => maintenance.value?.level === 'MANT')
const isControlActive = computed(() => control.value?.mode === 'active')
const isRemoteOk = computed(() => halConnected.value !== false)

const preconditionList = computed(() => [
  { id: 'MANT', label: 'Modo Mantenimiento activo (MANT)', ok: isMaintenanceUnlocked.value },
  { id: 'ACTIVE', label: 'Autoridad de Control activa (ACTIVE)', ok: isControlActive.value },
  { id: 'REMOTE', label: 'ACU / LCU en Modo Remoto', ok: isRemoteOk.value },
])

const canExecute = computed(() => isMaintenanceUnlocked.value && isControlActive.value && isRemoteOk.value)

const stepsAutoRaw = [
  'Verificación de Precondiciones',
  'Generación de Señal Interna',
  'Medición y Cálculo de Constante',
]

const stepsExternalRaw = [
  'Verificación de Precondiciones',
  'Inyección de Señal Externa',
  'Retiro de Señal y Medición',
]

const currentSteps = computed<WizardStepItem[]>(() => {
  const titles = mode.value === 'auto' ? stepsAutoRaw : stepsExternalRaw
  return titles.map((title, idx) => {
    const stepNum = idx + 1
    let status: 'pending' | 'active' | 'completed' | 'failed' = 'pending'
    if (routineResult.value?.outcome === 'failed') {
      status = 'failed'
    } else if (routineResult.value?.outcome === 'success') {
      status = 'completed'
    } else if (stepNum < stepIndex.value) {
      status = 'completed'
    } else if (stepNum === stepIndex.value) {
      status = 'active'
    }
    return { title, status }
  })
})

async function loadLogs() {
  calibrationLogs.value = await fetchCalibrationLog()
}

function handleJobStatus(job: ControlJobStatusResponse) {
  if (job.current_step) stepIndex.value = job.current_step

  if (job.status === 'awaiting_operator_input') {
    promptTitle.value = job.step_name || 'Entrada del Operador Requerida'
    promptMessage.value = job.prompt || 'Por favor ingrese el valor solicitado para continuar.'
    if (job.current_step === 2) {
      promptLabel.value = 'Potencia Inyectada (dBm)'
      promptDefaultValue.value = -30.0
      promptInputKey.value = 'injected_power_dbm'
    } else {
      promptLabel.value = 'Constante de Radar Medida (dB)'
      promptDefaultValue.value = 68.5
      promptInputKey.value = 'measured_radar_constant_db'
    }
    promptOpen.value = true
  }
}

async function handleStart() {
  if (!canExecute.value || running.value) return
  running.value = true
  error.value = null
  stepIndex.value = 1
  isSaved.value = true
  routineResult.value = null
  currentJobId.value = null

  try {
    routineResult.value = await runControlJob<RoutineResult>(
      '/api/control/single-point-calibration',
      { mode: mode.value },
      (id) => {
        currentJobId.value = id
      },
      handleJobStatus,
    )
    if (routineResult.value?.outcome === 'success') {
      stepIndex.value = currentSteps.value.length
      isSaved.value = false
    }
    await loadLogs()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    running.value = false
  }
}

async function handlePromptConfirm(val: number | null) {
  promptOpen.value = false
  if (!currentJobId.value) return
  const payload: Record<string, unknown> = {}
  if (promptInputKey.value) {
    payload[promptInputKey.value] = val
  }
  try {
    await advanceControlJobStep(currentJobId.value, payload)
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
    running.value = false
  }
}

function handlePromptCancel() {
  promptOpen.value = false
  running.value = false
}

async function handleSave() {
  if (!currentJobId.value) return
  savingResult.value = true
  error.value = null
  try {
    await saveSinglePointCalibrationResult(currentJobId.value)
    isSaved.value = true
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    savingResult.value = false
  }
}

onMounted(async () => {
  await loadLogs()
})
</script>

<template>
  <div class="p-6 space-y-6 max-w-7xl mx-auto dark:text-slate-100">
    <!-- Encabezado de Vista -->
    <div class="flex items-center justify-between border-b pb-4 dark:border-slate-700">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Vista G4 — Calibración de Punto Único
        </h1>
        <p class="text-sm text-slate-500 dark:text-slate-400">
          Calibración de punto único del receptor utilizando el generador interno automático o señal externa guiada.
        </p>
      </div>
      <div class="text-right">
        <span class="rounded bg-slate-100 dark:bg-slate-800 px-3 py-1 font-mono text-xs font-semibold text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-600">
          RAVIS §7.4.2 / §14.3
        </span>
      </div>
    </div>

    <!-- Banner de error si existe -->
    <div v-if="error" class="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-xs text-destructive">
      {{ error }}
    </div>

    <!-- Persistent Unsaved Banner -->
    <UnsavedResultBanner :saved="isSaved" @save="handleSave" />

    <!-- Modos de Calibración -->
    <div class="rounded-lg border bg-white p-6 shadow-sm dark:bg-slate-800 dark:border-slate-700">
      <h2 class="text-lg font-bold text-slate-800 dark:text-slate-100 mb-4">
        Modo de Calibración
      </h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label
          class="flex items-start space-x-3 p-4 rounded-lg border cursor-pointer transition"
          :class="mode === 'auto' ? 'border-emerald-500 bg-emerald-50/30 dark:bg-emerald-950/20' : 'border-slate-200 dark:border-slate-700'"
        >
          <input v-model="mode" type="radio" value="auto" :disabled="running" class="mt-1 text-emerald-600 focus:ring-emerald-500" />
          <div>
            <div class="font-semibold text-slate-900 dark:text-slate-100">Escenario 1: Generador Interno (Automático)</div>
            <div class="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Ejecuta el muestreo automatizado inyectando el generador interno del receptor y calculando directamente la constante de radar.
            </div>
          </div>
        </label>

        <label
          class="flex items-start space-x-3 p-4 rounded-lg border cursor-pointer transition"
          :class="mode === 'external' ? 'border-emerald-500 bg-emerald-50/30 dark:bg-emerald-950/20' : 'border-slate-200 dark:border-slate-700'"
        >
          <input v-model="mode" type="radio" value="external" :disabled="running" class="mt-1 text-emerald-600 focus:ring-emerald-500" />
          <div>
            <div class="font-semibold text-slate-900 dark:text-slate-100">Escenario 2: Generador Externo (Intervención del Operador)</div>
            <div class="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Procedimiento interactivo guiado donde el operador conecta un generador de señal externo e introduce las lecturas obtenidas.
            </div>
          </div>
        </label>
      </div>
    </div>

    <!-- Layout Principal: Stepper + Precondiciones -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Wizard Stepper -->
      <div class="lg:col-span-2 rounded-lg border bg-white p-6 shadow-sm dark:bg-slate-800 dark:border-slate-700 space-y-6">
        <h2 class="text-lg font-bold text-slate-800 dark:text-slate-100">
          Procedimiento Guiado
        </h2>
        <WizardStepper
          :steps="currentSteps"
          :current-step="stepIndex"
          :is-complete="routineResult?.outcome === 'success'"
        />

        <div v-if="routineResult" class="rounded-lg border p-4 bg-slate-50 dark:bg-slate-900 dark:border-slate-700">
          <h3 class="text-sm font-bold text-slate-700 dark:text-slate-200 mb-2">
            Resultados Obtenidos:
          </h3>
          <div class="grid grid-cols-2 gap-2 text-xs font-mono">
            <template v-for="step in routineResult.steps" :key="step.signal_id">
              <div v-if="step.signal_id.startsWith('rx.single_point')" class="p-2 bg-white dark:bg-slate-800 rounded border dark:border-slate-700">
                <span class="text-slate-500 dark:text-slate-400 block">{{ step.signal_id }}:</span>
                <span class="font-bold text-slate-800 dark:text-slate-200">{{ step.detail }}</span>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- Precondiciones y Control -->
      <div class="rounded-lg border bg-white p-6 shadow-sm dark:bg-slate-800 dark:border-slate-700 space-y-6">
        <h2 class="text-lg font-bold text-slate-800 dark:text-slate-100">
          Verificación de Precondiciones
        </h2>
        <ul class="space-y-3">
          <li v-for="item in preconditionList" :key="item.id" class="flex items-center space-x-2 text-sm">
            <span :class="item.ok ? 'text-emerald-500 font-bold' : 'text-rose-500 font-bold'">
              {{ item.ok ? '✓' : '✗' }}
            </span>
            <span :class="item.ok ? 'text-slate-700 dark:text-slate-200' : 'text-slate-400 dark:text-slate-500'">
              {{ item.label }}
            </span>
          </li>
        </ul>

        <div class="pt-4 border-t dark:border-slate-700">
          <button
            type="button"
            :disabled="running || !canExecute"
            class="w-full rounded-md bg-emerald-600 py-2.5 px-4 text-sm font-semibold text-white shadow hover:bg-emerald-700 disabled:opacity-50"
            @click="handleStart"
          >
            {{ running ? 'Ejecutando Calibración...' : 'Iniciar Calibración de Punto Único' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Histórico Actividades G8 -->
    <div class="rounded-lg border bg-white p-6 shadow-sm dark:bg-slate-800 dark:border-slate-700 space-y-4">
      <h2 class="text-lg font-bold text-slate-800 dark:text-slate-100">
        Histórico de Actividades de Calibración (G8)
      </h2>
      <div v-if="calibrationLogs.length === 0" class="text-sm text-slate-500 italic py-4">
        Sin registros de calibración.
      </div>
      <div v-else class="space-y-2 max-h-60 overflow-y-auto pr-2">
        <div
          v-for="(log, idx) in calibrationLogs"
          :key="idx"
          class="p-3 rounded border text-xs flex justify-between items-start dark:border-slate-700 dark:bg-slate-900"
        >
          <div>
            <div class="font-bold text-slate-800 dark:text-slate-200">{{ log.procedure }} — {{ log.message }}</div>
            <div class="text-slate-500 dark:text-slate-400 mt-0.5">
              Operador: {{ log.actor }} <span v-if="log.detail">— Detail: {{ log.detail }}</span>
            </div>
          </div>
          <div class="text-slate-400 font-mono text-[10px]">
            {{ new Date(log.at_wall).toLocaleString() }}
          </div>
        </div>
      </div>
    </div>

    <!-- Dialogo Interactivo Modal para entrada de operador -->
    <OperatorPromptDialog
      :open="promptOpen"
      :title="promptTitle"
      :prompt="promptMessage"
      :input-label="promptLabel"
      :default-value="promptDefaultValue"
      @confirm="handlePromptConfirm"
      @cancel="handlePromptCancel"
    />
  </div>
</template>
