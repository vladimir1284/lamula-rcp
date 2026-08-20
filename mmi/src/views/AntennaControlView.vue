<script setup lang="ts">
import { computed, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useGateway } from '@/composables/useGateway'
import type { AntennaAxis, AntennaMovementRequest, AntennaPositioningRequest, RoutineResult } from '@/types/mmi'

const { control, antenna, postControl } = useGateway()

const isActive = computed(() => control.value?.mode === 'active')

// --- Jog (Rutina 5, movimiento continuo) ---------------------------------
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
    jogResult.value = await postControl<RoutineResult>('/api/control/antenna-movement', req)
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
const gainVPerDeg = ref<number | undefined>(undefined)
const maxVoltage = ref<number | undefined>(undefined)
const toleranceDeg = ref<number | undefined>(undefined)
const timeoutS = ref<number | undefined>(undefined)
const posBusy = ref(false)
const posResult = ref<RoutineResult | null>(null)
const posError = ref<string | null>(null)

const posReady = computed(
  () =>
    targetDeg.value !== undefined &&
    gainVPerDeg.value !== undefined &&
    maxVoltage.value !== undefined &&
    toleranceDeg.value !== undefined &&
    timeoutS.value !== undefined,
)

async function runPositioning() {
  if (!posReady.value) return
  posBusy.value = true
  posError.value = null
  try {
    const req: AntennaPositioningRequest = {
      axis: posAxis.value,
      target_deg: targetDeg.value as number,
      gain_v_per_deg: gainVPerDeg.value as number,
      max_voltage: maxVoltage.value as number,
      tolerance_deg: toleranceDeg.value as number,
      timeout_s: timeoutS.value as number,
    }
    posResult.value = await postControl<RoutineResult>('/api/control/antenna-positioning', req)
  } catch (e) {
    posError.value = e instanceof Error ? e.message : String(e)
  } finally {
    posBusy.value = false
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
      <CardContent class="flex flex-wrap items-center gap-4 text-sm">
        <template v-if="antenna">
          <span>az: {{ antenna.az_deg.toFixed(2) }}° ({{ antenna.az_rate_deg_s.toFixed(3) }}°/s)</span>
          <span>el: {{ antenna.el_deg.toFixed(2) }}° ({{ antenna.el_rate_deg_s.toFixed(3) }}°/s)</span>
          <Badge v-if="!antenna.az_valid || !antenna.el_valid" variant="destructive">encoder inválido</Badge>
          <Badge v-if="antenna.degraded" variant="secondary">degradado</Badge>
        </template>
        <span v-else class="text-muted-foreground">sin posición todavía</span>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Jog — movimiento continuo (Rutina 5)</CardTitle>
      </CardHeader>
      <CardContent class="flex flex-col gap-3">
        <div class="flex flex-wrap items-center gap-3 text-sm">
          <label class="flex items-center gap-1"><input v-model="jogAxis" type="radio" value="azimuth"> azimut</label>
          <label class="flex items-center gap-1"><input v-model="jogAxis" type="radio" value="elevation"> elevación</label>
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
        <div class="flex flex-wrap items-center gap-3 text-sm">
          <label class="flex items-center gap-1"><input v-model="posAxis" type="radio" value="azimuth"> azimut</label>
          <label class="flex items-center gap-1"><input v-model="posAxis" type="radio" value="elevation"> elevación</label>
        </div>
        <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <label class="flex flex-col gap-1 text-xs">
            target_deg
            <Input v-model.number="targetDeg" type="number" step="0.1" />
          </label>
          <label class="flex flex-col gap-1 text-xs">
            gain_v_per_deg (sin confirmar)
            <Input v-model.number="gainVPerDeg" type="number" step="0.01" />
          </label>
          <label class="flex flex-col gap-1 text-xs">
            max_voltage (sin confirmar)
            <Input v-model.number="maxVoltage" type="number" step="0.1" />
          </label>
          <label class="flex flex-col gap-1 text-xs">
            tolerance_deg (sin confirmar)
            <Input v-model.number="toleranceDeg" type="number" step="0.1" />
          </label>
          <label class="flex flex-col gap-1 text-xs">
            timeout_s (sin confirmar)
            <Input v-model.number="timeoutS" type="number" step="1" />
          </label>
        </div>
        <p class="text-xs text-muted-foreground">
          Puede tardar hasta timeout_s segundos en responder -- sin progreso intermedio, es síncrono.
        </p>
        <div class="flex flex-wrap items-center gap-2">
          <Button :disabled="!isActive || posBusy || !posReady" @click="runPositioning">
            {{ posBusy ? 'Posicionando...' : 'Posicionar' }}
          </Button>
          <span v-if="posError" class="text-sm text-destructive">{{ posError }}</span>
          <Badge v-if="posResult" :variant="posResult.outcome === 'success' ? 'default' : 'destructive'">
            {{ posResult.outcome }}
          </Badge>
        </div>
        <ul v-if="posResult" class="flex flex-col gap-0.5 text-xs text-muted-foreground">
          <li v-for="s in posResult.steps" :key="s.signal_id">{{ s.ok ? '✓' : '✗' }} {{ s.signal_id }} — {{ s.detail }}</li>
        </ul>
      </CardContent>
    </Card>
  </div>
</template>
