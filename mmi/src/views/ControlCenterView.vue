<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import AntennaPositionReadout from '@/components/domain/AntennaPositionReadout.vue'
import ConnectionStatusBadge from '@/components/domain/ConnectionStatusBadge.vue'
import ControlAuthorityCard from '@/components/domain/ControlAuthorityCard.vue'
import JobActionPanel from '@/components/domain/JobActionPanel.vue'
import { useGateway } from '@/composables/useGateway'
import type {
  AntennaUnitPowerOnRequest,
  ReceiverPowerOnRequest,
  RoutineResult,
  TransmitterPowerOnRequest,
  WsMessage,
} from '@/types/mmi'

const { status, messages, control, antenna, dsp, fetchStatus, setControlMode, runControlJob, cancelControlJob } =
  useGateway()

const actor = ref('operador')
const busy = ref(false)
const error = ref<string | null>(null)

// Encendido -- sin valor inicial en los inputs obligatorios: ninguno tiene
// un valor real confirmado del lado de core/control_routines/ (PEND-RCP-07),
// ponerle un default aca seria fabricar el mismo tipo de numero sin respaldo
// que el backend ya se niega a inventar.
const isActive = computed(() => control.value?.mode === 'active')

const generalBusy = ref(false)
const generalJobId = ref<string | null>(null)
const generalResult = ref<RoutineResult | null>(null)
const generalError = ref<string | null>(null)

const txWarmupTimeoutS = ref<number | undefined>(undefined)
const txBusy = ref(false)
const txJobId = ref<string | null>(null)
const txResult = ref<RoutineResult | null>(null)
const txError = ref<string | null>(null)

const rxConfirmTimeoutS = ref<number | undefined>(undefined)
const rxBusy = ref(false)
const rxJobId = ref<string | null>(null)
const rxResult = ref<RoutineResult | null>(null)
const rxError = ref<string | null>(null)

const auConfirmTimeoutS = ref<number | undefined>(undefined)
const auBusy = ref(false)
const auJobId = ref<string | null>(null)
const auResult = ref<RoutineResult | null>(null)
const auError = ref<string | null>(null)

// Cancelar estas cuatro rutinas es de menor riesgo que Jog/Posicionar/Scan
// Cut (D-12 extendido, ver docstring de core/control_routines/): son pulsos
// digitales momentaneos + sondeo de confirmacion, no actuacion continua --
// cancelar a mitad de camino no deja nada moviendose indefinidamente, por
// eso ninguna de las cuatro tiene el `except BaseException` de limpieza que
// si necesitan `antenna_movement.py`/`antenna_positioning.py`/`scan_controller.py`.
async function cancelGeneralPowerOn() {
  if (!generalJobId.value) return
  try {
    await cancelControlJob(generalJobId.value)
  } catch (e) {
    generalError.value = e instanceof Error ? e.message : String(e)
  }
}

async function cancelTransmitterPowerOn() {
  if (!txJobId.value) return
  try {
    await cancelControlJob(txJobId.value)
  } catch (e) {
    txError.value = e instanceof Error ? e.message : String(e)
  }
}

async function cancelReceiverPowerOn() {
  if (!rxJobId.value) return
  try {
    await cancelControlJob(rxJobId.value)
  } catch (e) {
    rxError.value = e instanceof Error ? e.message : String(e)
  }
}

async function cancelAntennaUnitPowerOn() {
  if (!auJobId.value) return
  try {
    await cancelControlJob(auJobId.value)
  } catch (e) {
    auError.value = e instanceof Error ? e.message : String(e)
  }
}

async function runGeneralPowerOn() {
  generalBusy.value = true
  generalError.value = null
  generalJobId.value = null
  try {
    generalResult.value = await runControlJob<RoutineResult>('/api/control/general-power-on', undefined, (id) => {
      generalJobId.value = id
    })
  } catch (e) {
    generalError.value = e instanceof Error ? e.message : String(e)
  } finally {
    generalBusy.value = false
    generalJobId.value = null
  }
}

async function runTransmitterPowerOn() {
  if (txWarmupTimeoutS.value === undefined) return
  txBusy.value = true
  txError.value = null
  txJobId.value = null
  try {
    const req: TransmitterPowerOnRequest = { warmup_timeout_s: txWarmupTimeoutS.value }
    txResult.value = await runControlJob<RoutineResult>('/api/control/transmitter-power-on', req, (id) => {
      txJobId.value = id
    })
  } catch (e) {
    txError.value = e instanceof Error ? e.message : String(e)
  } finally {
    txBusy.value = false
    txJobId.value = null
  }
}

async function runReceiverPowerOn() {
  if (rxConfirmTimeoutS.value === undefined) return
  rxBusy.value = true
  rxError.value = null
  rxJobId.value = null
  try {
    const req: ReceiverPowerOnRequest = { confirm_timeout_s: rxConfirmTimeoutS.value }
    rxResult.value = await runControlJob<RoutineResult>('/api/control/receiver-power-on', req, (id) => {
      rxJobId.value = id
    })
  } catch (e) {
    rxError.value = e instanceof Error ? e.message : String(e)
  } finally {
    rxBusy.value = false
    rxJobId.value = null
  }
}

async function runAntennaUnitPowerOn() {
  if (auConfirmTimeoutS.value === undefined) return
  auBusy.value = true
  auError.value = null
  auJobId.value = null
  try {
    const req: AntennaUnitPowerOnRequest = { confirm_timeout_s: auConfirmTimeoutS.value }
    auResult.value = await runControlJob<RoutineResult>('/api/control/antenna-unit-power-on', req, (id) => {
      auJobId.value = id
    })
  } catch (e) {
    auError.value = e instanceof Error ? e.message : String(e)
  } finally {
    auBusy.value = false
    auJobId.value = null
  }
}

function messageLabel(msg: WsMessage): string {
  if (msg.type === 'event') return `${msg.kind} (${msg.actor})`
  if (msg.type === 'antenna') return `az=${msg.position.az_deg.toFixed(1)} el=${msg.position.el_deg.toFixed(1)}`
  if (msg.type === 'session') return `rcp ${msg.rcp_version}`
  return ''
}

async function toggleControl() {
  if (!control.value) return
  busy.value = true
  error.value = null
  try {
    const nextMode = control.value.mode === 'active' ? 'passive' : 'active'
    await setControlMode({ mode: nextMode, actor: actor.value })
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    busy.value = false
  }
}

onMounted(async () => {
  try {
    await fetchStatus()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
})
</script>

<template>
  <div class="mx-auto flex max-w-3xl flex-col gap-4 p-6">
    <h1 class="text-2xl font-semibold">Control Center</h1>

    <Card>
      <CardHeader>
        <CardTitle>Conexión al gateway</CardTitle>
      </CardHeader>
      <CardContent class="flex flex-wrap items-center gap-3">
        <ConnectionStatusBadge :status="status" />
        <Badge :variant="dsp?.connected ? 'default' : 'secondary'">
          DSP {{ dsp?.connected ? 'conectado' : 'sin conexión' }}
        </Badge>
        <span v-if="error" class="text-destructive">{{ error }}</span>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Autoridad de control</CardTitle>
      </CardHeader>
      <CardContent>
        <ControlAuthorityCard
          :control="control"
          editable
          :actor="actor"
          :busy="busy"
          @update:actor="actor = $event"
          @toggle="toggleControl"
        />
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Antena</CardTitle>
      </CardHeader>
      <CardContent>
        <AntennaPositionReadout :antenna="antenna" />
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Encendido</CardTitle>
      </CardHeader>
      <CardContent class="flex flex-col gap-4">
        <JobActionPanel
          run-label="General power-on"
          :busy="generalBusy"
          :job-id="generalJobId"
          :result="generalResult"
          :error="generalError"
          :run-disabled="!isActive"
          busy-text="en curso..."
          @run="runGeneralPowerOn"
          @cancel="cancelGeneralPowerOn"
        />

        <Separator />

        <JobActionPanel
          run-label="Transmisor power-on"
          :busy="txBusy"
          :job-id="txJobId"
          :result="txResult"
          :error="txError"
          :run-disabled="!isActive || txWarmupTimeoutS === undefined"
          busy-text="en curso..."
          @run="runTransmitterPowerOn"
          @cancel="cancelTransmitterPowerOn"
        >
          <template #params>
            <Input
              v-model.number="txWarmupTimeoutS"
              type="number"
              placeholder="warmup_timeout_s (sin valor confirmado, ingrese uno)"
              class="w-72"
            />
          </template>
        </JobActionPanel>

        <Separator />

        <JobActionPanel
          run-label="Receptor power-on"
          :busy="rxBusy"
          :job-id="rxJobId"
          :result="rxResult"
          :error="rxError"
          :run-disabled="!isActive || rxConfirmTimeoutS === undefined"
          busy-text="en curso..."
          @run="runReceiverPowerOn"
          @cancel="cancelReceiverPowerOn"
        >
          <template #params>
            <Input
              v-model.number="rxConfirmTimeoutS"
              type="number"
              placeholder="confirm_timeout_s (sin valor confirmado, ingrese uno)"
              class="w-72"
            />
          </template>
        </JobActionPanel>

        <Separator />

        <JobActionPanel
          run-label="Unidad de antena power-on"
          :busy="auBusy"
          :job-id="auJobId"
          :result="auResult"
          :error="auError"
          :run-disabled="!isActive || auConfirmTimeoutS === undefined"
          busy-text="en curso..."
          @run="runAntennaUnitPowerOn"
          @cancel="cancelAntennaUnitPowerOn"
        >
          <template #params>
            <Input
              v-model.number="auConfirmTimeoutS"
              type="number"
              placeholder="confirm_timeout_s (sin valor confirmado, ingrese uno)"
              class="w-72"
            />
          </template>
        </JobActionPanel>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Log de mensajes</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea class="h-64 w-full">
          <ul class="flex flex-col gap-1 text-sm">
            <li v-for="(msg, i) in [...messages].reverse()" :key="i" class="flex items-center gap-2">
              <Badge variant="outline" class="w-20 shrink-0 justify-center">{{ msg.type }}</Badge>
              <span>{{ messageLabel(msg) }}</span>
            </li>
          </ul>
        </ScrollArea>
      </CardContent>
    </Card>
  </div>
</template>
