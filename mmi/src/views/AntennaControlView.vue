<script setup lang="ts">
import { computed, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import AntennaPositionReadout from '@/components/domain/AntennaPositionReadout.vue'
import AxisPositioningFields, {
  type PartialAxisPositioningParams,
} from '@/components/domain/AxisPositioningFields.vue'
import AxisSelector from '@/components/domain/AxisSelector.vue'
import JobActionPanel from '@/components/domain/JobActionPanel.vue'
import { useGateway } from '@/composables/useGateway'
import type { AntennaAxis, AntennaMovementRequest, AntennaPositioningRequest, RoutineResult } from '@/types/mmi'

const { control, antenna, runControlJob, cancelControlJob } = useGateway()

const isActive = computed(() => control.value?.mode === 'active')

// --- Jog (Rutina 5, movimiento continuo) ---------------------------------
// Panel propio, no JobActionPanel: "Detener" no cancela un job por id, manda
// un comando nuevo (0V) -- semántica distinta al patrón ejecutar/cancelar.
const jogAxis = ref<AntennaAxis>('azimuth')
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

function move() {
  if (jogVoltage.value === undefined) return
  runJog(jogVoltage.value)
}

function stop() {
  // 0 V no es un valor inventado -- es el literal de "detener" que el
  // propio backend documenta como especial (nunca lo rechaza la guarda).
  runJog(0)
}

// --- Posicionar (Rutina 6, control proporcional a un angulo) -------------
const posAxis = ref<AntennaAxis>('azimuth')
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

const posReady = computed(
  () =>
    targetDeg.value !== undefined &&
    posFields.value.gain_v_per_deg !== undefined &&
    posFields.value.max_voltage !== undefined &&
    posFields.value.tolerance_deg !== undefined &&
    posFields.value.timeout_s !== undefined,
)

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
  <div class="mx-auto flex max-w-3xl flex-col gap-4 p-6">
    <h1 class="text-2xl font-semibold">Antenna Control</h1>

    <Card>
      <CardHeader>
        <CardTitle>Posición en vivo</CardTitle>
      </CardHeader>
      <CardContent>
        <AntennaPositionReadout :antenna="antenna" show-rates />
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Jog — movimiento continuo (Rutina 5)</CardTitle>
      </CardHeader>
      <CardContent class="flex flex-col gap-3">
        <div class="flex flex-wrap items-center gap-3">
          <AxisSelector v-model="jogAxis" />
          <Input
            v-model.number="jogVoltage"
            type="number"
            step="0.1"
            placeholder="voltage_reference (sin valor confirmado, ingrese uno)"
            class="w-72"
          />
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <Button :disabled="!isActive || jogBusy || jogVoltage === undefined" @click="move">Mover</Button>
          <Button variant="destructive" :disabled="jogBusy" @click="stop">Detener</Button>
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

    <Card>
      <CardHeader>
        <CardTitle>Posicionar — control proporcional a un ángulo (Rutina 6)</CardTitle>
      </CardHeader>
      <CardContent class="flex flex-col gap-3">
        <AxisSelector v-model="posAxis" />
        <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <label class="flex flex-col gap-1 text-xs">
            target_deg
            <Input v-model.number="targetDeg" type="number" step="0.1" />
          </label>
        </div>
        <AxisPositioningFields v-model="posFields" />
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
</template>
