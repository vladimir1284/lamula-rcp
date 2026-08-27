<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import AxisPositioningFields, {
  type PartialAxisPositioningParams,
} from '@/components/domain/AxisPositioningFields.vue'
import JobActionPanel from '@/components/domain/JobActionPanel.vue'
import { GATEWAY_HTTP, useGateway } from '@/composables/useGateway'
import {
  MOMENT_IDS,
  type MomentId,
  type ScanCut,
  type ScanCutExecutionRequest,
  type ScanCutResult,
} from '@/types/scan'

const { control, runControlJob, cancelControlJob } = useGateway()
const isActive = computed(() => control.value?.mode === 'active')

const worksheet = ref<ScanCut[]>([])
const loadError = ref<string | null>(null)
const submitError = ref<string | null>(null)

type Mode = 'ppi' | 'rhi'
const mode = ref<Mode>('ppi')

// Campos compartidos por ambos modos.
const prfHz = ref(1000)
const pulseWidthUs = ref(1)
const selectedMoments = ref<Set<MomentId>>(new Set(['UZ']))

// Campos PPI.
const elevationDeg = ref(0)
const azimuthStartDeg = ref(0)
const azimuthEndDeg = ref(360)

// Campos RHI.
const azimuthDeg = ref(0)
const elevationStartDeg = ref(-1)
const elevationEndDeg = ref(90)

function toggleMoment(id: MomentId) {
  const next = new Set(selectedMoments.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  selectedMoments.value = next
}

// Validacion de cliente minima -- solo lo visible en el form (rangos,
// start != end, al menos un moment). La validacion completa (Pydantic) la
// hace el backend; esto es feedback antes de golpear la red, no un
// duplicado de esa logica.
const clientError = computed(() => {
  if (selectedMoments.value.size === 0) return 'seleccione al menos un moment'
  if (mode.value === 'ppi') {
    if (elevationDeg.value < -90 || elevationDeg.value > 90) return 'elevation_deg fuera de rango (-90..90)'
    if (azimuthStartDeg.value < 0 || azimuthStartDeg.value >= 360) return 'azimuth_start_deg fuera de rango (0..<360)'
    if (azimuthEndDeg.value < 0 || azimuthEndDeg.value > 360) return 'azimuth_end_deg fuera de rango (0..360)'
    if (azimuthStartDeg.value === azimuthEndDeg.value) return 'azimuth_start_deg y azimuth_end_deg no pueden ser iguales'
  } else {
    if (azimuthDeg.value < 0 || azimuthDeg.value >= 360) return 'azimuth_deg fuera de rango (0..<360)'
    if (elevationStartDeg.value < -90 || elevationStartDeg.value > 90) return 'elevation_start_deg fuera de rango (-90..90)'
    if (elevationEndDeg.value < -90 || elevationEndDeg.value > 90) return 'elevation_end_deg fuera de rango (-90..90)'
    if (elevationStartDeg.value === elevationEndDeg.value) return 'elevation_start_deg y elevation_end_deg no pueden ser iguales'
  }
  if (prfHz.value <= 0) return 'prf_hz debe ser mayor que 0'
  if (pulseWidthUs.value <= 0) return 'pulse_width_us debe ser mayor que 0'
  return null
})

function buildCut(): ScanCut {
  const moments = [...selectedMoments.value]
  if (mode.value === 'ppi') {
    return {
      mode: 'ppi',
      elevation_deg: elevationDeg.value,
      azimuth_start_deg: azimuthStartDeg.value,
      azimuth_end_deg: azimuthEndDeg.value,
      prf_hz: prfHz.value,
      pulse_width_us: pulseWidthUs.value,
      moments,
    }
  }
  return {
    mode: 'rhi',
    azimuth_deg: azimuthDeg.value,
    elevation_start_deg: elevationStartDeg.value,
    elevation_end_deg: elevationEndDeg.value,
    prf_hz: prfHz.value,
    pulse_width_us: pulseWidthUs.value,
    moments,
  }
}

async function fetchWorksheet() {
  const res = await fetch(`${GATEWAY_HTTP}/api/scan/worksheet`)
  if (!res.ok) throw new Error(`GET /api/scan/worksheet: HTTP ${res.status}`)
  worksheet.value = (await res.json()) as ScanCut[]
}

async function addCut() {
  submitError.value = null
  if (clientError.value) {
    submitError.value = clientError.value
    return
  }
  const res = await fetch(`${GATEWAY_HTTP}/api/scan/worksheet`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(buildCut()),
  })
  if (!res.ok) {
    const body = await res.text()
    submitError.value = `POST /api/scan/worksheet: HTTP ${res.status} — ${body}`
    return
  }
  worksheet.value = (await res.json()) as ScanCut[]
}

async function removeCut(index: number) {
  const res = await fetch(`${GATEWAY_HTTP}/api/scan/worksheet/${index}`, { method: 'DELETE' })
  if (!res.ok) return
  worksheet.value = (await res.json()) as ScanCut[]
}

// --- Ejecucion de un corte (Scan Controller, POST
// /api/scan/worksheet/{index}/execute) -- panel unico compartido por todo el
// worksheet, no un formulario por fila (mismo criterio que Jog/Posicionar en
// AntennaControlView.vue). Ningun campo lleva default: no hay ganancia
// volt->grados/s ni velocidad de barrido confirmadas (PEND-RCP-07/09), el
// operador tiene que traerlas.
const execIndex = ref<number | undefined>(undefined)
const azFields = ref<PartialAxisPositioningParams>({
  gain_v_per_deg: undefined,
  max_voltage: undefined,
  tolerance_deg: undefined,
  timeout_s: undefined,
})
const elFields = ref<PartialAxisPositioningParams>({
  gain_v_per_deg: undefined,
  max_voltage: undefined,
  tolerance_deg: undefined,
  timeout_s: undefined,
})
const sweepVoltageMagnitude = ref<number | undefined>(undefined)
const sweepToleranceDeg = ref<number | undefined>(undefined)
const sweepTimeoutS = ref<number | undefined>(undefined)
const execBusy = ref(false)
const execJobId = ref<string | null>(null)
const execResult = ref<ScanCutResult | null>(null)
const execError = ref<string | null>(null)

function axisFieldsReady(fields: PartialAxisPositioningParams): boolean {
  return (
    fields.gain_v_per_deg !== undefined &&
    fields.max_voltage !== undefined &&
    fields.tolerance_deg !== undefined &&
    fields.timeout_s !== undefined
  )
}

const execReady = computed(
  () =>
    execIndex.value !== undefined &&
    axisFieldsReady(azFields.value) &&
    axisFieldsReady(elFields.value) &&
    sweepVoltageMagnitude.value !== undefined &&
    sweepToleranceDeg.value !== undefined &&
    sweepTimeoutS.value !== undefined,
)

async function executeCut() {
  if (!execReady.value) return
  execBusy.value = true
  execError.value = null
  execJobId.value = null
  try {
    const azimuth_positioning = {
      gain_v_per_deg: azFields.value.gain_v_per_deg as number,
      max_voltage: azFields.value.max_voltage as number,
      tolerance_deg: azFields.value.tolerance_deg as number,
      timeout_s: azFields.value.timeout_s as number,
    }
    const elevation_positioning = {
      gain_v_per_deg: elFields.value.gain_v_per_deg as number,
      max_voltage: elFields.value.max_voltage as number,
      tolerance_deg: elFields.value.tolerance_deg as number,
      timeout_s: elFields.value.timeout_s as number,
    }
    const req: ScanCutExecutionRequest = {
      azimuth_positioning,
      elevation_positioning,
      sweep_voltage_magnitude: sweepVoltageMagnitude.value as number,
      sweep_tolerance_deg: sweepToleranceDeg.value as number,
      sweep_timeout_s: sweepTimeoutS.value as number,
    }
    execResult.value = await runControlJob<ScanCutResult>(
      `/api/scan/worksheet/${execIndex.value}/execute`,
      req,
      (id) => {
        execJobId.value = id
      },
    )
  } catch (e) {
    execError.value = e instanceof Error ? e.message : String(e)
  } finally {
    execBusy.value = false
    execJobId.value = null
  }
}

// Cancela una ejecucion en curso -- el Scan Controller detiene el eje de
// barrido antes de que el job quede en `done` (ver docstring de
// core/scan_controller.py, bloque try/except CancelledError).
async function cancelExecution() {
  if (!execJobId.value) return
  try {
    await cancelControlJob(execJobId.value)
  } catch (e) {
    execError.value = e instanceof Error ? e.message : String(e)
  }
}

function summarize(cut: ScanCut): string {
  if (cut.mode === 'ppi') {
    return `elev ${cut.elevation_deg}° · az ${cut.azimuth_start_deg}°→${cut.azimuth_end_deg}°`
  }
  return `az ${cut.azimuth_deg}° · elev ${cut.elevation_start_deg}°→${cut.elevation_end_deg}°`
}

onMounted(() => {
  fetchWorksheet().catch((e) => {
    loadError.value = e instanceof Error ? e.message : String(e)
  })
})
</script>

<template>
  <div class="mx-auto flex max-w-3xl flex-col gap-4 p-6">
    <h1 class="text-2xl font-semibold">Scan Worksheet</h1>
    <p class="text-sm text-muted-foreground">
      Cortes de escaneo manuales (PPI/RHI) -- sin scheduler automatico ni ejecucion todavia.
    </p>

    <Card>
      <CardHeader>
        <CardTitle>Nuevo corte</CardTitle>
      </CardHeader>
      <CardContent class="flex flex-col gap-3">
        <div class="flex gap-4 text-sm">
          <label class="flex items-center gap-1">
            <input type="radio" value="ppi" v-model="mode">
            PPI
          </label>
          <label class="flex items-center gap-1">
            <input type="radio" value="rhi" v-model="mode">
            RHI
          </label>
        </div>

        <div v-if="mode === 'ppi'" class="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <label class="flex flex-col gap-1 text-sm">
            elevation_deg
            <Input v-model.number="elevationDeg" type="number" min="-90" max="90" step="0.1" />
          </label>
          <label class="flex flex-col gap-1 text-sm">
            azimuth_start_deg
            <Input v-model.number="azimuthStartDeg" type="number" min="0" max="359.999" step="0.1" />
          </label>
          <label class="flex flex-col gap-1 text-sm">
            azimuth_end_deg
            <Input v-model.number="azimuthEndDeg" type="number" min="0" max="360" step="0.1" />
          </label>
        </div>
        <div v-else class="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <label class="flex flex-col gap-1 text-sm">
            azimuth_deg
            <Input v-model.number="azimuthDeg" type="number" min="0" max="359.999" step="0.1" />
          </label>
          <label class="flex flex-col gap-1 text-sm">
            elevation_start_deg
            <Input v-model.number="elevationStartDeg" type="number" min="-90" max="90" step="0.1" />
          </label>
          <label class="flex flex-col gap-1 text-sm">
            elevation_end_deg
            <Input v-model.number="elevationEndDeg" type="number" min="-90" max="90" step="0.1" />
          </label>
        </div>

        <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <label class="flex flex-col gap-1 text-sm">
            prf_hz
            <Input v-model.number="prfHz" type="number" min="0.01" step="1" />
          </label>
          <label class="flex flex-col gap-1 text-sm">
            pulse_width_us
            <Input v-model.number="pulseWidthUs" type="number" min="0.01" step="0.1" />
          </label>
        </div>

        <div class="flex flex-col gap-1 text-sm">
          moments
          <div class="flex flex-wrap gap-2">
            <label
              v-for="id in MOMENT_IDS"
              :key="id"
              class="flex items-center gap-1 rounded border px-2 py-1"
            >
              <input
                type="checkbox"
                :checked="selectedMoments.has(id)"
                @change="toggleMoment(id)"
              >
              {{ id }}
            </label>
          </div>
        </div>

        <p v-if="submitError" class="text-sm text-destructive">{{ submitError }}</p>
        <div>
          <Button @click="addCut">Agregar</Button>
        </div>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Worksheet ({{ worksheet.length }} corte(s))</CardTitle>
      </CardHeader>
      <CardContent class="flex flex-col gap-2">
        <p v-if="loadError" class="text-sm text-destructive">{{ loadError }}</p>
        <p v-else-if="worksheet.length === 0" class="text-sm text-muted-foreground">
          Sin cortes todavia.
        </p>
        <div
          v-for="(cut, index) in worksheet"
          :key="index"
          class="flex flex-wrap items-center justify-between gap-2 rounded border p-2 text-sm"
        >
          <div class="flex flex-wrap items-center gap-2">
            <Badge variant="default">{{ cut.mode.toUpperCase() }}</Badge>
            <span>{{ summarize(cut) }}</span>
            <span class="text-muted-foreground">
              PRF {{ cut.prf_hz }} Hz · PW {{ cut.pulse_width_us }} µs · {{ cut.moments.join(', ') }}
            </span>
          </div>
          <Button variant="destructive" size="sm" @click="removeCut(index)">Eliminar</Button>
        </div>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Ejecutar corte (Scan Controller)</CardTitle>
      </CardHeader>
      <CardContent class="flex flex-col gap-3">
        <p class="text-xs text-muted-foreground">
          Posiciona el eje fijo y barre el eje móvil del corte elegido (Rutinas 5/6). No sube HV
          ni radía, y no aplica prf_hz/pulse_width_us (PEND-RCP-08/09/10, ver pendientes.md).
        </p>
        <label class="flex flex-col gap-1 text-sm">
          corte a ejecutar
          <select v-model.number="execIndex" class="rounded border bg-background px-2 py-1">
            <option :value="undefined" disabled>seleccione un corte</option>
            <option v-for="(cut, index) in worksheet" :key="index" :value="index">
              #{{ index }} — {{ cut.mode.toUpperCase() }} · {{ summarize(cut) }}
            </option>
          </select>
        </label>

        <div class="grid grid-cols-2 gap-4 sm:grid-cols-2">
          <AxisPositioningFields v-model="azFields" axis-label="azimuth_positioning (sin confirmar)" />
          <AxisPositioningFields v-model="elFields" axis-label="elevation_positioning (sin confirmar)" />
        </div>

        <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <label class="flex flex-col gap-1 text-xs">
            sweep_voltage_magnitude (sin confirmar)
            <Input v-model.number="sweepVoltageMagnitude" type="number" step="0.1" min="0.001" />
          </label>
          <label class="flex flex-col gap-1 text-xs">
            sweep_tolerance_deg (sin confirmar)
            <Input v-model.number="sweepToleranceDeg" type="number" step="0.1" />
          </label>
          <label class="flex flex-col gap-1 text-xs">
            sweep_timeout_s (sin confirmar)
            <Input v-model.number="sweepTimeoutS" type="number" step="1" />
          </label>
        </div>

        <JobActionPanel
          run-label="Ejecutar"
          running-label="Ejecutando..."
          :busy="execBusy"
          :job-id="execJobId"
          :result="execResult"
          :error="execError"
          :run-disabled="!isActive || !execReady"
          @run="executeCut"
          @cancel="cancelExecution"
        />
      </CardContent>
    </Card>
  </div>
</template>
