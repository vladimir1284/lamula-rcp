<!--
  TxSamplingAdjustView.vue: Vista G2 — TX Sampling Adjust.
  Permite ajustar los parámetros de muestreo TX (TX Sample, TX Frequency, Commanded LO Freq,
  TX Start/Stop Sample) y realizar una lectura cruzada con parámetros del pulso TX/scan (ASCOPE D2).
-->
<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import IndicatorLamp from '@/components/shell/IndicatorLamp.vue'
import ParameterGroupCard from '@/components/domain/ParameterGroupCard.vue'
import ParameterField from '@/components/domain/ParameterField.vue'
import SetSaveActions from '@/components/domain/SetSaveActions.vue'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useGateway } from '@/composables/useGateway'
import type { TxSamplingAdjustParams, TxSamplingAdjustSnapshot } from '@/types/mmi'

const { fetchTxSamplingAdjust, setTxSamplingAdjust, saveTxSamplingAdjust } = useGateway()

const snapshot = ref<TxSamplingAdjustSnapshot | null>(null)
const draft = ref<TxSamplingAdjustParams>({
  tx_sample: 128,
  tx_frequency_mhz: 2800,
  commanded_lo_freq_mhz: 2770,
  tx_start_sample: 32,
  tx_stop_sample: 256,
})

const initialParams = ref<TxSamplingAdjustParams | null>(null)
const busy = ref(false)
const error = ref<string | null>(null)
let pollTimer: ReturnType<typeof setInterval> | null = null

async function refresh() {
  try {
    const snap = await fetchTxSamplingAdjust()
    snapshot.value = snap
    if (!initialParams.value && snap.params) {
      initialParams.value = { ...snap.params }
      draft.value = { ...snap.params }
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

const dirty = computed(() => {
  if (!initialParams.value) return true
  return (
    draft.value.tx_sample !== initialParams.value.tx_sample ||
    draft.value.tx_frequency_mhz !== initialParams.value.tx_frequency_mhz ||
    draft.value.commanded_lo_freq_mhz !== initialParams.value.commanded_lo_freq_mhz ||
    draft.value.tx_start_sample !== initialParams.value.tx_start_sample ||
    draft.value.tx_stop_sample !== initialParams.value.tx_stop_sample
  )
})

function isAccepted(commanded: number, readout: number | null): boolean {
  if (readout === null || readout === undefined) return false
  return Math.abs(commanded - readout) < 0.001
}

async function doSet() {
  busy.value = true
  error.value = null
  try {
    const updated = await setTxSamplingAdjust(draft.value)
    initialParams.value = { ...updated }
    if (snapshot.value) {
      snapshot.value.params = { ...updated }
    }
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

function resetDraft() {
  if (initialParams.value) {
    draft.value = { ...initialParams.value }
  }
}

onMounted(() => {
  refresh()
  pollTimer = setInterval(refresh, 1000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 overflow-auto p-3">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-base font-semibold text-foreground">G2 — TX Sampling Adjust</h2>
        <p class="text-xs text-muted-foreground">
          Ajuste de muestreo de pulso transmisor y frecuencia LO comandada con lectura cruzada contra ASCOPE (D2).
        </p>
      </div>
      <IndicatorLamp
        label="Bus Modbus"
        :state="snapshot?.bus_ok ? 'ok' : 'fault'"
        :detail="snapshot?.bus_ok ? 'Conectado' : 'Sin comunicación Modbus'"
      />
    </div>

    <p v-if="error" class="text-xs font-medium text-destructive">{{ error }}</p>

    <div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
      <!-- Panel de Lectura Cruzada ASCOPE (D2) / Contrato Scan -->
      <Card class="border-border/80 bg-card/80 shadow-xs lg:col-span-1">
        <CardHeader class="border-b border-border/50 pb-2.5 pt-3.5">
          <CardTitle class="text-sm font-semibold tracking-wide text-foreground">
            Lectura Cruzada ASCOPE (D2)
          </CardTitle>
          <p class="text-xs text-muted-foreground">
            Parámetros de pulso TX / escaneo del contrato de dominio
          </p>
        </CardHeader>
        <CardContent class="p-4 flex flex-col gap-3 text-xs">
          <div class="flex flex-col gap-1 rounded-md border border-border/50 bg-muted/20 p-2.5">
            <span class="text-muted-foreground">Ancho de Pulso (pulse_width_us)</span>
            <span class="font-mono text-sm font-semibold text-foreground">1.00 µs</span>
          </div>

          <div class="flex flex-col gap-1 rounded-md border border-border/50 bg-muted/20 p-2.5">
            <span class="text-muted-foreground">Frecuencia de Repetición (prf_hz)</span>
            <span class="font-mono text-sm font-semibold text-foreground">1000 Hz</span>
          </div>

          <div class="flex flex-col gap-1 rounded-md border border-border/50 bg-muted/20 p-2.5">
            <span class="text-muted-foreground">Límite Duty Cycle Guard</span>
            <span class="font-mono text-sm font-semibold text-foreground">0.085 %</span>
          </div>

          <p class="text-[11px] text-muted-foreground italic">
            Valores de referencia de sincronización de pulso verificados contra `src/core/contracts/scan.py`.
          </p>
        </CardContent>
      </Card>

      <!-- Panel Principales Parámetros de Muestreo TX -->
      <div class="lg:col-span-2 flex flex-col gap-4">
        <ParameterGroupCard
          title="Parámetros de Ajuste TX"
          description="Ajuste de tiempos de muestreo y frecuencias LO comandadas"
        >
          <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
            <ParameterField
              v-model="draft.tx_sample"
              label="TX Sample"
              unit="samples"
              :readout="snapshot?.tx_sample_readout ?? null"
              :accepted="isAccepted(draft.tx_sample, snapshot?.tx_sample_readout ?? null)"
              :disabled="busy"
              :min="0"
              :max="1024"
            />

            <ParameterField
              v-model="draft.tx_frequency_mhz"
              label="TX Frequency"
              unit="MHz"
              :readout="snapshot?.tx_frequency_readout_mhz ?? null"
              :accepted="isAccepted(draft.tx_frequency_mhz, snapshot?.tx_frequency_readout_mhz ?? null)"
              :disabled="busy"
              :min="2000"
              :max="4000"
            />

            <ParameterField
              v-model="draft.commanded_lo_freq_mhz"
              label="Commanded LO Freq."
              unit="MHz"
              :readout="snapshot?.commanded_lo_freq_readout_mhz ?? null"
              :accepted="isAccepted(draft.commanded_lo_freq_mhz, snapshot?.commanded_lo_freq_readout_mhz ?? null)"
              :disabled="busy"
              :min="2000"
              :max="4000"
            />

            <ParameterField
              v-model="draft.tx_start_sample"
              label="TX Start Sample"
              unit="samples"
              :readout="snapshot?.tx_start_sample_readout ?? null"
              :accepted="isAccepted(draft.tx_start_sample, snapshot?.tx_start_sample_readout ?? null)"
              :disabled="busy"
              :min="0"
              :max="1024"
            />

            <ParameterField
              v-model="draft.tx_stop_sample"
              label="TX Stop Sample"
              unit="samples"
              :readout="snapshot?.tx_stop_sample_readout ?? null"
              :accepted="isAccepted(draft.tx_stop_sample, snapshot?.tx_stop_sample_readout ?? null)"
              :disabled="busy"
              :min="0"
              :max="1024"
            />
          </div>
        </ParameterGroupCard>

        <!-- Acciones Set / Save -->
        <SetSaveActions
          :dirty="dirty"
          :busy="busy"
          :can-save="!snapshot?.radiating"
          save-blocked-reason="No se puede guardar mientras el radar está radiando"
          @set="doSet"
          @save="doSave"
          @reset="resetDraft"
        />
      </div>
    </div>
  </div>
</template>
