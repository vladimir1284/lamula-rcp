<!--
  TxSamplingAdjustView.vue: Vista G2 — TX Sampling Adjust (RAVIS §7.4.1 y §14.2.1).
  Ajuste del muestreo de pulso TX (TX Start/Stop Sample, TX Sample, TX Frequency,
  Commanded LO Freq.) con lectura cruzada contra ASCOPE (D2) y Scan Worksheet.
-->
<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import IndicatorLamp from '@/components/shell/IndicatorLamp.vue'
import ParameterField from '@/components/domain/ParameterField.vue'
import SetSaveActions from '@/components/domain/SetSaveActions.vue'
import { useGateway } from '@/composables/useGateway'
import type { TxSamplingAdjustParams, TxSamplingAdjustSnapshot } from '@/types/mmi'

const { fetchTxSamplingAdjust, setTxSamplingAdjust, saveTxSamplingAdjust, fetchScanWorksheet } = useGateway()

const snapshot = ref<TxSamplingAdjustSnapshot | null>(null)
const draft = ref<TxSamplingAdjustParams>({
  tx_start_sample: 10,
  tx_stop_sample: 50,
  tx_sample: 16,
  tx_frequency: 30.0,
  commanded_lo_freq: 5600.0,
})
const draftTouched = ref(false)
const busy = ref(false)
const error = ref<string | null>(null)
const activePulseWidthUs = ref<number | null>(null)

let pollTimer: ReturnType<typeof setInterval> | null = null

function isAccepted(read: number | null | undefined, cmd: number): boolean {
  if (read === null || read === undefined) return false
  return Math.abs(read - cmd) < 0.001
}

const isStartAccepted = computed(() => isAccepted(snapshot.value?.tx_start_sample_read, draft.value.tx_start_sample))
const isStopAccepted = computed(() => isAccepted(snapshot.value?.tx_stop_sample_read, draft.value.tx_stop_sample))
const isSampleAccepted = computed(() => isAccepted(snapshot.value?.tx_sample_read, draft.value.tx_sample))
const isFreqAccepted = computed(() => isAccepted(snapshot.value?.tx_frequency_read, draft.value.tx_frequency))
const isLoFreqAccepted = computed(() => isAccepted(snapshot.value?.commanded_lo_freq_read, draft.value.commanded_lo_freq))

async function refresh() {
  try {
    snapshot.value = await fetchTxSamplingAdjust()
    if (!draftTouched.value && snapshot.value.params) {
      draft.value = { ...snapshot.value.params }
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

async function loadScanCutPulseWidth() {
  try {
    const cuts = await fetchScanWorksheet()
    if (cuts.length > 0 && cuts[0]?.pulse_width_us !== undefined) {
      activePulseWidthUs.value = cuts[0].pulse_width_us
    } else {
      activePulseWidthUs.value = null
    }
  } catch {
    activePulseWidthUs.value = null
  }
}

async function doSet() {
  busy.value = true
  error.value = null
  try {
    const params = await setTxSamplingAdjust(draft.value)
    if (snapshot.value) snapshot.value.params = params
    draftTouched.value = false
    await refresh()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    busy.value = false
  }
}

async function doSave() {
  busy.value = true
  error.value = null
  try {
    await doSet()
    await saveTxSamplingAdjust()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    busy.value = false
  }
}

function doReset() {
  if (snapshot.value?.params) {
    draft.value = { ...snapshot.value.params }
    draftTouched.value = false
  }
}

onMounted(() => {
  refresh()
  loadScanCutPulseWidth()
  pollTimer = setInterval(refresh, 2000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 overflow-auto p-3">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold text-foreground">G2 — TX Sampling Adjust</h2>
        <p class="text-xs text-muted-foreground">
          Ajuste del temporizado y muestreo del pulso TX del receptor digital (DRX / RSP).
        </p>
      </div>
      <div class="flex items-center gap-3">
        <button
          type="button"
          class="rounded-md border border-border bg-card px-2.5 py-1 text-xs font-medium text-foreground hover:bg-accent"
          @click="refresh"
        >
          Actualizar lecturas DRX
        </button>
        <IndicatorLamp
          label="Bus Modbus"
          :state="snapshot?.bus_ok ? 'ok' : 'fault'"
          :detail="snapshot?.bus_ok ? 'Conectado' : 'Sin comunicación Modbus'"
        />
      </div>
    </div>

    <p v-if="error" class="text-xs font-medium text-destructive">{{ error }}</p>

    <!-- Cross-view hint -->
    <div class="rounded-md border border-blue-500/30 bg-blue-500/10 p-3 text-xs text-blue-900 dark:text-blue-100">
      <div class="flex items-start gap-2">
        <svg class="mt-0.5 h-4 w-4 text-blue-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div class="space-y-1">
          <p class="font-medium">Lectura cruzada contra ASCOPE (D2) y Scan Worksheet:</p>
          <p class="text-[11px] opacity-90">
            El técnico lee la posición del bin en el ASCOPE (D2), multiplica por 10 e ingresa las muestras de inicio y fin (en unidades de 29 ns).
            <span v-if="activePulseWidthUs !== null">
              Ancho de pulso activo en Scan Worksheet (<code class="font-mono">pulse_width_us</code>):
              <strong class="font-mono">{{ activePulseWidthUs.toFixed(2) }} µs</strong>.
            </span>
            <span v-else>
              Scan Worksheet sin cortes configurados.
            </span>
          </p>
        </div>
      </div>
    </div>

    <!-- Parameter form grid -->
    <Card>
      <CardHeader class="pb-2">
        <CardTitle class="text-sm font-semibold">Parámetros de Muestreo TX</CardTitle>
      </CardHeader>
      <CardContent class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <ParameterField
          v-model="draft.tx_start_sample"
          label="TX Start Sample"
          unit="29 ns"
          :read-only-value="snapshot?.tx_start_sample_read"
          :accepted="isStartAccepted"
          helpText="Inicio de ventana de detección TX"
          @update:model-value="draftTouched = true"
        />

        <ParameterField
          v-model="draft.tx_stop_sample"
          label="TX Stop Sample"
          unit="29 ns"
          :read-only-value="snapshot?.tx_stop_sample_read"
          :accepted="isStopAccepted"
          helpText="Fin de ventana de detección TX"
          @update:model-value="draftTouched = true"
        />

        <ParameterField
          v-model="draft.tx_sample"
          label="TX Sample Count"
          unit="pulsos"
          :read-only-value="snapshot?.tx_sample_read"
          :accepted="isSampleAccepted"
          helpText="Muestras por pulso para fase/potencia"
          @update:model-value="draftTouched = true"
        />

        <ParameterField
          v-model="draft.tx_frequency"
          label="TX Frequency"
          unit="MHz"
          :read-only-value="snapshot?.tx_frequency_read"
          :accepted="isFreqAccepted"
          helpText="Frecuencia intermedia medida por el DRX"
          @update:model-value="draftTouched = true"
        />

        <ParameterField
          v-model="draft.commanded_lo_freq"
          label="Commanded LO Freq."
          unit="MHz"
          :read-only-value="snapshot?.commanded_lo_freq_read"
          :accepted="isLoFreqAccepted"
          helpText="Primer oscilador local nominal"
          @update:model-value="draftTouched = true"
        />
      </CardContent>
    </Card>

    <!-- Set / Save Actions -->
    <SetSaveActions
      :dirty="draftTouched"
      :busy="busy"
      @set="doSet"
      @save="doSave"
      @reset="doReset"
    />
  </div>
</template>
