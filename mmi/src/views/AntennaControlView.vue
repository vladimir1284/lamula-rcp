<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import AntennaAngleDial from '@/components/domain/AntennaAngleDial.vue'
import AxisPositioningFields, {
  type PartialAxisPositioningParams,
} from '@/components/domain/AxisPositioningFields.vue'
import AxisSelector from '@/components/domain/AxisSelector.vue'
import JobActionPanel from '@/components/domain/JobActionPanel.vue'
import LevelBar from '@/components/domain/LevelBar.vue'
import StepWidthSetup from '@/components/domain/StepWidthSetup.vue'
import { useGateway } from '@/composables/useGateway'
import type { AntennaAxis, AntennaMovementRequest, AntennaPositioningRequest, AntennaStepConfig, RoutineResult } from '@/types/mmi'

const { control, antenna, runControlJob, cancelControlJob, fetchStepConfig } = useGateway()

const isActive = computed(() => control.value?.mode === 'active')

// --- Lectura para los dials AZ/EL ------------------------------------------
// targetDeg/toleranceDeg sólo se muestran en el dial del eje que Posicionar
// (Rutina 6) tiene seleccionado -- es el único setpoint real que existe; el
// otro eje no tiene nominal que mostrar.
const azValid = computed(() => (antenna.value ? antenna.value.az_valid && !antenna.value.az_fault : true))
const elValid = computed(() => (antenna.value ? antenna.value.el_valid && !antenna.value.el_fault : true))

// --- Jog (Rutina 5, movimiento continuo) ---------------------------------
// Panel propio, no JobActionPanel: "Detener" no cancela un job por id, manda
// un comando nuevo (0V) -- semántica distinta al patrón ejecutar/cancelar.
const jogAxis = ref<AntennaAxis>('azimuth')
const posAxis = ref<AntennaAxis>('azimuth')
// Sin valor inicial: no hay ganancia volt->grados/s confirmada (PEND-RCP-07),
// el operador tiene que traer el voltaje, no esta vista.
const jogVoltage = ref<number | undefined>(undefined)
const jogBusy = ref(false)
const jogResult = ref<RoutineResult | null>(null)
const jogError = ref<string | null>(null)

async function runJog(voltage: number) {
  jogBusy.value = true
  jogError.value = null
  try {
    const req: AntennaMovementRequest = { axis: jogAxis.value, voltage_reference: voltage }
    jogResult.value = await runControlJob<RoutineResult>('/api/control/antenna-movement', req)
  } catch (e) {
    jogError.value = e instanceof Error ? e.message : String(e)
  } finally {
    jogBusy.value = false
  }
}

// CW/CCW mantener-presionado: al soltar manda 0V, el literal de "detener"
// que el backend documenta como especial (nunca lo rechaza la guarda) --
// misma llamada que el botón "Detener" explícito.
function startJog(sign: 1 | -1) {
  if (jogVoltage.value === undefined) return
  runJog(sign * jogVoltage.value)
}

function stopJog() {
  runJog(0)
}

// --- Eje operativo compartido ---------------------------------------------
// Jog y Posicionar tienen cada uno su propio axis porque son rutinas
// independientes (podés jog-ear AZ mientras dejás un setpoint de EL
// cargado) -- pero en el caso común el operador quiere moverlos juntos.
// Sincronizado por default; "SYNC: OFF" vuelve a mostrar los selectores
// independientes de cada card.
const axisSynced = ref(true)

function setSharedAxis(axis: AntennaAxis) {
  jogAxis.value = axis
  posAxis.value = axis
}

watch(jogAxis, (v) => {
  if (axisSynced.value) posAxis.value = v
})
watch(posAxis, (v) => {
  if (axisSynced.value) jogAxis.value = v
})

// --- Posicionar (Rutina 6, control proporcional a un angulo) -------------
const targetDeg = ref<number | undefined>(undefined)
const posFields = ref<PartialAxisPositioningParams>({
  gain_v_per_deg: undefined,
  max_voltage: undefined,
  tolerance_deg: undefined,
  timeout_s: undefined,
})
const posBusy = ref(false)
const posJobId = ref<string | null>(null)
const posResult = ref<RoutineResult | null>(null)
const posError = ref<string | null>(null)

const stepModalOpen = ref(false)
const stepConfig = ref<AntennaStepConfig>({ azimuth_step_deg: 1.0, elevation_step_deg: 1.0 })

onMounted(async () => {
  try {
    stepConfig.value = await fetchStepConfig()
  } catch {
    // fallback a defaults
  }
})

function onStepConfigSaved(cfg: AntennaStepConfig) {
  stepConfig.value = cfg
}

const posParamsReady = computed(
  () =>
    posFields.value.gain_v_per_deg !== undefined &&
    posFields.value.max_voltage !== undefined &&
    posFields.value.tolerance_deg !== undefined &&
    posFields.value.timeout_s !== undefined,
)

const posReady = computed(
  () => targetDeg.value !== undefined && posParamsReady.value,
)

// Distancia real al setpoint vs la tolerancia configurada -- mismo par
// nominal/actual que .value-nominal/.value-actual, en forma de barra.
const posCurrentDeg = computed(() =>
  posAxis.value === 'azimuth' ? antenna.value?.az_deg : antenna.value?.el_deg,
)
const posDivergenceDeg = computed(() => {
  if (targetDeg.value === undefined || posCurrentDeg.value === undefined) return null
  return Math.abs(posCurrentDeg.value - targetDeg.value)
})
const posDivergenceTone = computed(() => {
  if (posDivergenceDeg.value === null || posFields.value.tolerance_deg === undefined) return 'neutral'
  return posDivergenceDeg.value <= posFields.value.tolerance_deg ? 'ok' : 'warn'
})

const currentStepDeg = computed(() =>
  posAxis.value === 'azimuth' ? stepConfig.value.azimuth_step_deg : stepConfig.value.elevation_step_deg,
)

// multiplier sobre el paso YA configurado (StepWidthSetup) -- ×0.1/×1/×10,
// nunca un grado fijo inventado: la precisión real la trae el operador.
async function stepMove(deltaSign: number, multiplier = 1) {
  const currentPos = posAxis.value === 'azimuth' ? (antenna.value?.az_deg ?? 0) : (antenna.value?.el_deg ?? 0)
  const step = posAxis.value === 'azimuth' ? stepConfig.value.azimuth_step_deg : stepConfig.value.elevation_step_deg
  targetDeg.value = currentPos + deltaSign * step * multiplier
  await runPositioning()
}

function clearTarget() {
  targetDeg.value = undefined
}

async function runPositioning() {
  if (!posReady.value) return
  posBusy.value = true
  posError.value = null
  posJobId.value = null
  try {
    const req: AntennaPositioningRequest = {
      axis: posAxis.value,
      target_deg: targetDeg.value as number,
      gain_v_per_deg: posFields.value.gain_v_per_deg as number,
      max_voltage: posFields.value.max_voltage as number,
      tolerance_deg: posFields.value.tolerance_deg as number,
      timeout_s: posFields.value.timeout_s as number,
    }
    posResult.value = await runControlJob<RoutineResult>('/api/control/antenna-positioning', req, (id) => {
      posJobId.value = id
    })
  } catch (e) {
    posError.value = e instanceof Error ? e.message : String(e)
  } finally {
    posBusy.value = false
    posJobId.value = null
  }
}

// Cancela un Posicionar en curso -- a diferencia del Jog (que se detiene
// mandando 0V como un comando nuevo), el proprocional de la Rutina 6 sigue
// pidiendo voltajes por su cuenta cada iteracion hasta llegar a tolerancia;
// sin cancelar el job de verdad, un 0V manual desde otra parte de la MMI
// quedaria sobrescrito en la proxima iteracion (ver docstring de
// antenna_positioning.py).
async function cancelPositioning() {
  if (!posJobId.value) return
  try {
    await cancelControlJob(posJobId.value)
  } catch (e) {
    posError.value = e instanceof Error ? e.message : String(e)
  }
}
</script>

<template>
  <div class="@container flex h-full min-h-0 flex-col gap-4 overflow-auto p-3">
    <div class="flex shrink-0 flex-wrap items-center gap-2 rounded-md border border-border bg-card px-3 py-2">
      <span class="text-xs font-medium uppercase tracking-wide text-muted-foreground">Canal operativo</span>
      <Button
        :variant="jogAxis === 'azimuth' && posAxis === 'azimuth' ? 'ok' : 'outline'"
        size="sm"
        :class="jogAxis === 'azimuth' && posAxis === 'azimuth' ? 'shadow-[0_0_8px_currentColor]' : ''"
        @click="setSharedAxis('azimuth')"
      >
        Eje azimut
      </Button>
      <Button
        :variant="jogAxis === 'elevation' && posAxis === 'elevation' ? 'ok' : 'outline'"
        size="sm"
        :class="jogAxis === 'elevation' && posAxis === 'elevation' ? 'shadow-[0_0_8px_currentColor]' : ''"
        @click="setSharedAxis('elevation')"
      >
        Eje elevación
      </Button>
      <Button
        :variant="axisSynced ? 'secondary' : 'outline'"
        size="sm"
        class="ml-auto"
        :title="axisSynced ? 'Jog y Posicionar comparten eje' : 'Jog y Posicionar con eje independiente'"
        @click="axisSynced = !axisSynced"
      >
        {{ axisSynced ? 'SYNC: ON' : 'SYNC: OFF' }}
      </Button>
    </div>

    <div class="grid grid-cols-1 items-start gap-4 @2xl:grid-cols-2">
      <Card class="shrink-0">
        <CardHeader>
          <div class="flex items-center gap-2">
            <Badge variant="outline" class="font-mono text-[10px]">AZ</Badge>
            <CardTitle>Azimut</CardTitle>
          </div>
          <CardDescription class="font-mono text-[10px] uppercase tracking-wider">
            // compás 0°–360°
          </CardDescription>
          <CardAction>
            <Badge v-if="!azValid" variant="destructive">sin dato válido</Badge>
          </CardAction>
        </CardHeader>
        <CardContent class="flex flex-col items-center gap-2">
          <AntennaAngleDial
            axis="azimuth"
            :value-deg="antenna?.az_deg ?? 0"
            :rate-deg-s="antenna?.az_rate_deg_s ?? null"
            :target-deg="posAxis === 'azimuth' ? (targetDeg ?? null) : null"
            :tolerance-deg="posAxis === 'azimuth' ? (posFields.tolerance_deg ?? null) : null"
            :valid="azValid"
          />
        </CardContent>
      </Card>
      <Card class="shrink-0">
        <CardHeader>
          <div class="flex items-center gap-2">
            <Badge variant="outline" class="font-mono text-[10px]">EL</Badge>
            <CardTitle>Elevación</CardTitle>
          </div>
          <CardDescription class="font-mono text-[10px] uppercase tracking-wider">
            // arco 0°–90°, horizonte→cenit
          </CardDescription>
          <CardAction>
            <Badge v-if="!elValid" variant="destructive">sin dato válido</Badge>
          </CardAction>
        </CardHeader>
        <CardContent class="flex flex-col items-center gap-2">
          <AntennaAngleDial
            axis="elevation"
            :value-deg="antenna?.el_deg ?? 0"
            :rate-deg-s="antenna?.el_rate_deg_s ?? null"
            :target-deg="posAxis === 'elevation' ? (targetDeg ?? null) : null"
            :tolerance-deg="posAxis === 'elevation' ? (posFields.tolerance_deg ?? null) : null"
            :valid="elValid"
          />
        </CardContent>
      </Card>
    </div>

    <div class="grid grid-cols-1 items-start gap-4 @2xl:grid-cols-2">
    <Card class="shrink-0">
      <CardHeader>
        <CardTitle>Jog — movimiento continuo (Rutina 5)</CardTitle>
      </CardHeader>
      <CardContent class="flex flex-col gap-3">
        <div class="flex flex-wrap items-end gap-3">
          <AxisSelector v-if="!axisSynced" v-model="jogAxis" />
          <span v-else class="text-sm text-muted-foreground">
            Eje: <span class="font-medium text-foreground">{{ jogAxis === 'azimuth' ? 'azimut' : 'elevación' }}</span>
          </span>
          <label class="flex flex-col gap-1 text-xs">
            voltage_reference
            <Input v-model.number="jogVoltage" type="number" step="0.1" placeholder="V" class="w-24" />
          </label>
        </div>
        <p class="text-xs text-muted-foreground">
          Sin valor confirmado todavía (PEND-RCP-07) -- traiga el voltaje, la vista no propone uno.
        </p>
        <div class="flex items-stretch gap-2">
          <Button
            variant="secondary"
            size="lg"
            class="h-16 flex-1 text-base font-semibold transition-transform active:scale-[0.98]"
            :disabled="!isActive || jogVoltage === undefined"
            @mousedown="startJog(-1)"
            @mouseup="stopJog"
            @mouseleave="stopJog"
          >
            ◀ CCW
          </Button>
          <Button
            variant="secondary"
            size="lg"
            class="h-16 flex-1 text-base font-semibold transition-transform active:scale-[0.98]"
            :disabled="!isActive || jogVoltage === undefined"
            @mousedown="startJog(1)"
            @mouseup="stopJog"
            @mouseleave="stopJog"
          >
            CW ▶
          </Button>
        </div>
        <p class="text-xs text-muted-foreground">Mantener presionado para mover; soltar detiene.</p>
        <div class="flex flex-wrap items-center gap-2">
          <Button variant="destructive" :disabled="jogBusy" @click="stopJog">Detener</Button>
          <span v-if="jogBusy" class="text-sm text-muted-foreground">en curso...</span>
          <span v-if="jogError" class="text-sm text-destructive">{{ jogError }}</span>
          <Badge v-if="jogResult" :variant="jogResult.outcome === 'success' ? 'default' : 'destructive'">
            {{ jogResult.outcome }}
          </Badge>
        </div>
        <ul v-if="jogResult" class="flex flex-col gap-0.5 text-xs text-muted-foreground">
          <li v-for="s in jogResult.steps" :key="s.signal_id">{{ s.ok ? '✓' : '✗' }} {{ s.signal_id }} — {{ s.detail }}</li>
        </ul>
      </CardContent>
    </Card>

    <Card class="shrink-0">
      <CardHeader>
        <div class="flex items-center gap-2">
          <Badge variant="outline" class="font-mono text-[10px]">RUTINA 06</Badge>
          <CardTitle>Posicionamiento absoluto</CardTitle>
        </div>
        <CardDescription class="font-mono text-[10px] uppercase tracking-wider">
          // setpoint servo, control proporcional
        </CardDescription>
        <CardAction>
          <AxisSelector v-if="!axisSynced" v-model="posAxis" />
          <span v-else class="text-sm text-muted-foreground">
            Eje: <span class="font-medium text-foreground">{{ posAxis === 'azimuth' ? 'azimut' : 'elevación' }}</span>
          </span>
        </CardAction>
      </CardHeader>
      <CardContent class="flex flex-col gap-3">
        <StepWidthSetup
          v-model:open="stepModalOpen"
          @saved="onStepConfigSaved"
        />

        <!-- Readout tipo "display digital": mismo tratamiento visual que el
             dial (mono, grande, glow), con CLR y la tolerancia real (no un
             "±0.01°" de relleno) al lado. -->
        <div class="flex flex-col gap-1">
          <div class="flex items-center justify-between">
            <span class="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Ángulo objetivo (target_deg)
            </span>
            <span v-if="posFields.tolerance_deg !== undefined" class="font-mono text-[10px] text-muted-foreground">
              precisión ±{{ posFields.tolerance_deg }}°
            </span>
          </div>
          <div class="flex items-stretch gap-2">
            <div class="flex flex-1 items-baseline gap-1 rounded-md border border-border bg-background px-3 py-2">
              <input
                v-model.number="targetDeg"
                type="number"
                step="0.1"
                placeholder="—"
                class="w-full min-w-0 bg-transparent font-mono text-2xl font-bold tracking-tight tabular-nums text-telemetry-live drop-shadow-[0_0_6px_currentColor] outline-none"
              >
              <span class="text-sm text-muted-foreground">° DEG</span>
            </div>
            <Button variant="outline" size="sm" :disabled="targetDeg === undefined" @click="clearTarget">
              CLR
            </Button>
          </div>
        </div>

        <!-- Pasos finos/gruesos: ×0.1, ×1, ×10 del paso YA configurado
             (StepWidthSetup) -- nunca un grado fijo inventado. -->
        <div class="flex flex-col gap-1">
          <div class="flex items-center justify-between">
            <span class="text-xs font-medium uppercase tracking-wide text-muted-foreground">Paso rápido</span>
            <Button variant="secondary" size="sm" @click="stepModalOpen = true">Configurar paso ({{ currentStepDeg }}°)</Button>
          </div>
          <div class="grid grid-cols-6 gap-1">
            <Button variant="outline" size="sm" :disabled="!isActive || posBusy || !posParamsReady" @click="stepMove(-1, 10)">
              −{{ (currentStepDeg * 10).toFixed(2) }}°
            </Button>
            <Button variant="outline" size="sm" :disabled="!isActive || posBusy || !posParamsReady" @click="stepMove(-1, 1)">
              −{{ currentStepDeg.toFixed(2) }}°
            </Button>
            <Button variant="outline" size="sm" :disabled="!isActive || posBusy || !posParamsReady" @click="stepMove(-1, 0.1)">
              −{{ (currentStepDeg * 0.1).toFixed(2) }}°
            </Button>
            <Button variant="outline" size="sm" :disabled="!isActive || posBusy || !posParamsReady" @click="stepMove(1, 0.1)">
              +{{ (currentStepDeg * 0.1).toFixed(2) }}°
            </Button>
            <Button variant="outline" size="sm" :disabled="!isActive || posBusy || !posParamsReady" @click="stepMove(1, 1)">
              +{{ currentStepDeg.toFixed(2) }}°
            </Button>
            <Button variant="outline" size="sm" :disabled="!isActive || posBusy || !posParamsReady" @click="stepMove(1, 10)">
              +{{ (currentStepDeg * 10).toFixed(2) }}°
            </Button>
          </div>
        </div>

        <AxisPositioningFields v-model="posFields" />
        <LevelBar
          v-if="posDivergenceDeg !== null"
          label="Distancia a setpoint"
          :value="posDivergenceDeg"
          :min="0"
          :max="Math.max(posFields.tolerance_deg ?? 0.1, posDivergenceDeg, 0.001) * 1.5"
          :tone="posDivergenceTone"
          unit="°"
        />
        <p class="text-xs text-muted-foreground">
          Puede tardar hasta timeout_s segundos en completarse -- el botón queda deshabilitado
          mientras se sondea el resultado.
        </p>
        <JobActionPanel
          run-label="Posicionar"
          running-label="Posicionando..."
          cancel-label="Cancelar"
          :busy="posBusy"
          :job-id="posJobId"
          :result="posResult"
          :error="posError"
          :run-disabled="!isActive || !posReady"
          @run="runPositioning"
          @cancel="cancelPositioning"
        />
      </CardContent>
    </Card>
    </div>
  </div>
</template>
