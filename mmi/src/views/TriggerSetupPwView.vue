<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import ParameterGroupCard from '@/components/domain/ParameterGroupCard.vue'
import ConditionalFieldGroup from '@/components/domain/ConditionalFieldGroup.vue'
import { useGateway } from '@/composables/useGateway'
import type { TriggerSetupPwSettings } from '@/types/mmi'

const { fetchTriggerSetupPw, setTriggerSetupPw } = useGateway()

export type PulseWidthTab = 'short' | 'medium' | 'long'

const activePw = ref<PulseWidthTab>('medium')

const pwProfiles: Record<PulseWidthTab, { label: string; widthUs: number }> = {
  short: { label: 'Pulso Corto (0.5 µs)', widthUs: 0.5 },
  medium: { label: 'Pulso Medio (1.0 µs)', widthUs: 1.0 },
  long: { label: 'Pulso Largo (2.0 µs)', widthUs: 2.0 },
}

const settings = ref<TriggerSetupPwSettings>({
  selected_pulse_width: 'medium',
  gate_spacing_m: 150.0,
  prf_hz: 1000.0,
  external_pretrigger_delay_us: 0.0,
  current_noise_level_dbm: -110.0,
  powerup_noise_level_dbm: -112.0,
  triggers: [
    { trigger_index: 1, name: 'Trig 1 (Tx)', start_us: 0.0, width_us: 1.0, high: true, prt_term_enabled: false },
    { trigger_index: 2, name: 'Trig 2 (Rx)', start_us: 0.5, width_us: 1.0, high: true, prt_term_enabled: false },
    { trigger_index: 3, name: 'Trig 3 (Aux)', start_us: 1.0, width_us: 2.0, high: true, prt_term_enabled: false },
    { trigger_index: 4, name: 'Trig 4 (Spare)', start_us: 2.0, width_us: 2.0, high: false, prt_term_enabled: false },
  ],
})

const loading = ref(false)
const saving = ref(false)
const message = ref<string | null>(null)
const isError = ref(false)

async function loadData() {
  loading.value = true
  message.value = null
  isError.value = false
  try {
    settings.value = await fetchTriggerSetupPw()
    if (settings.value.selected_pulse_width) {
      activePw.value = settings.value.selected_pulse_width
    }
  } catch (err) {
    isError.value = true
    message.value = err instanceof Error ? err.message : 'Error al cargar configuración de triggers'
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  message.value = null
  isError.value = false
  try {
    settings.value.selected_pulse_width = activePw.value
    settings.value = await setTriggerSetupPw(settings.value)
    message.value = 'Selección de ancho de pulso guardada. gate_spacing_m/prf_hz son solo lectura (dato real del DSP).'
  } catch (err) {
    isError.value = true
    message.value = err instanceof Error ? err.message : 'Error al guardar configuración'
  } finally {
    saving.value = false
  }
}

watch(activePw, (newPw) => {
  if (newPw === 'short') settings.value.gate_spacing_m = 75.0
  else if (newPw === 'medium') settings.value.gate_spacing_m = 150.0
  else if (newPw === 'long') settings.value.gate_spacing_m = 300.0
})

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 overflow-auto p-4 text-xs bg-background text-foreground">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-2 border-b pb-3">
      <div>
        <div class="flex items-center gap-2">
          <h2 class="text-base font-bold tracking-tight">E6 — Trigger Setup por Pulse Width (Mt&lt;n&gt;)</h2>
          <Badge variant="outline" class="text-xs">Setup DSP / DRx</Badge>
        </div>
        <p class="text-xs text-muted-foreground mt-0.5">
          Alineación de retardos/anchura de triggers y resolución espacial por ancho de pulso.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <Button variant="outline" size="sm" :disabled="loading" @click="loadData">
          Refrescar
        </Button>
        <Button size="sm" :disabled="saving" @click="handleSave">
          Aplicar Cambios
        </Button>
      </div>
    </div>

    <!-- Pulse Width Selector Tabs -->
    <div class="flex items-center gap-2 border-b border-border/50 pb-2">
      <span class="text-xs font-semibold text-muted-foreground mr-2">Ancho de Pulso:</span>
      <button
        v-for="(pwInfo, pwKey) in pwProfiles"
        :key="pwKey"
        type="button"
        class="px-3 py-1.5 text-xs font-medium rounded-md transition-all cursor-pointer"
        :class="activePw === pwKey ? 'bg-primary text-primary-foreground shadow-xs font-bold' : 'bg-muted/50 text-muted-foreground hover:bg-muted hover:text-foreground'"
        @click="activePw = pwKey"
      >
        {{ pwInfo.label }}
      </button>
    </div>

    <!-- Status Message -->
    <div
      v-if="message"
      class="rounded p-2 text-xs"
      :class="isError ? 'border border-destructive/50 bg-destructive/10 text-destructive' : 'border border-emerald-500/50 bg-emerald-500/10 text-emerald-500'"
    >
      {{ message }}
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- Real Parameter: Gate Spacing (Dato Real) -->
      <ParameterGroupCard
        title="Máscara de Rango y PRF (Dato Real, solo lectura)"
        :description="`Parámetros espaciales activos reportados por el DSP para el perfil de pulso ${pwProfiles[activePw].label}`"
      >
        <div class="space-y-4">
          <div class="space-y-1.5">
            <div class="flex items-center justify-between">
              <label class="text-xs font-medium text-foreground">Range Mask Spacing (gate_spacing_m)</label>
              <Badge variant="outline" class="border-emerald-500/50 text-emerald-500 text-[10px]">Dato real (solo lectura)</Badge>
            </div>
            <div class="flex items-center gap-2">
              <Input
                :model-value="settings.gate_spacing_m"
                type="number"
                disabled
                class="h-8 font-mono text-xs"
              />
              <span class="text-muted-foreground font-mono">m</span>
            </div>
            <p class="text-[11px] text-muted-foreground">
              Espaciado físico de celda de rango reportado por el DSP. No editable: no existe
              escritura RCP→DSP para este campo hoy.
            </p>
          </div>

          <div class="space-y-1.5">
            <div class="flex items-center justify-between">
              <label class="text-xs font-medium text-foreground">Pulse Repetition Frequency (prf_hz)</label>
              <Badge variant="outline" class="border-emerald-500/50 text-emerald-500 text-[10px]">Dato real (solo lectura)</Badge>
            </div>
            <div class="flex items-center gap-2">
              <Input
                :model-value="settings.prf_hz"
                type="number"
                disabled
                class="h-8 font-mono text-xs"
              />
              <span class="text-muted-foreground font-mono">Hz</span>
            </div>
          </div>
        </div>
      </ParameterGroupCard>

      <!-- Read-Only Trigger Timing Table (Alineación DRx/FPGA) -->
      <ParameterGroupCard
        title="Tabla de Triggers (Solo Lectura de Alineación)"
        description="Retardos y anchura de triggers del DRx / FPGA (no editables en operación)"
      >
        <div class="overflow-x-auto">
          <table class="w-full text-left font-mono text-xs border-collapse">
            <thead>
              <tr class="border-b text-muted-foreground bg-muted/30">
                <th class="py-1.5 px-2">Trigger</th>
                <th class="py-1.5 px-2 text-right">Start (µs)</th>
                <th class="py-1.5 px-2 text-right">Width (µs)</th>
                <th class="py-1.5 px-2 text-center">High</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="trig in settings.triggers"
                :key="trig.trigger_index"
                class="border-b/40 text-foreground/80"
              >
                <td class="py-1.5 px-2 font-medium font-sans">{{ trig.name }}</td>
                <td class="py-1.5 px-2 text-right font-mono">{{ trig.start_us.toFixed(1) }}</td>
                <td class="py-1.5 px-2 text-right font-mono">{{ trig.width_us.toFixed(1) }}</td>
                <td class="py-1.5 px-2 text-center">
                  <Badge variant="outline" class="text-[9px] px-1 py-0" :class="trig.high ? 'border-primary text-primary' : 'text-muted-foreground'">
                    {{ trig.high ? 'SI' : 'NO' }}
                  </Badge>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="text-[11px] text-muted-foreground mt-2 italic">
          Los 4 pares de retardo/anchura de trigger se calibran en puesta en marcha y son de solo lectura.
        </p>
      </ParameterGroupCard>

      <!-- Additional PW Parameters - ConditionalFieldGroup Mock -->
      <ConditionalFieldGroup
        title="Parámetros Frecuencia Intermedia y Muestreo DRx"
        description="Frecuencias IF y ventana de estimador de burst por ancho de pulso"
        :supported="false"
      >
        <div class="grid grid-cols-2 gap-3">
          <div class="space-y-1">
            <label class="text-[11px] text-muted-foreground">Tx IF Frequency</label>
            <div class="flex items-center gap-1">
              <Input type="number" disabled value="30.0" class="h-8 font-mono text-xs" />
              <span class="text-muted-foreground text-[10px]">MHz</span>
            </div>
          </div>

          <div class="space-y-1">
            <label class="text-[11px] text-muted-foreground">Rx IF Frequency</label>
            <div class="flex items-center gap-1">
              <Input type="number" disabled value="30.0" class="h-8 font-mono text-xs" />
              <span class="text-muted-foreground text-[10px]">MHz</span>
            </div>
          </div>

          <div class="space-y-1">
            <label class="text-[11px] text-muted-foreground">Burst Estimator Length</label>
            <div class="flex items-center gap-1">
              <Input type="number" disabled value="16" class="h-8 font-mono text-xs" />
              <span class="text-muted-foreground text-[10px]">bins</span>
            </div>
          </div>

          <div class="space-y-1">
            <label class="text-[11px] text-muted-foreground">Tx Waveform</label>
            <Input type="text" disabled value="0: CWPulse" class="h-8 font-mono text-xs" />
          </div>
        </div>
      </ConditionalFieldGroup>

      <!-- Noise Level Defaults - ConditionalFieldGroup Mock -->
      <ConditionalFieldGroup
        title="Niveles de Ruido por Ancho de Pulso"
        description="Nivel de ruido medido en operación y al encendido"
        :supported="false"
      >
        <div class="grid grid-cols-2 gap-3">
          <div class="space-y-1">
            <label class="text-[11px] text-muted-foreground">Current Noise Level</label>
            <div class="flex items-center gap-1">
              <Input v-model.number="settings.current_noise_level_dbm" type="number" disabled class="h-8 font-mono text-xs" />
              <span class="text-muted-foreground text-[10px]">dBm</span>
            </div>
          </div>
          <div class="space-y-1">
            <label class="text-[11px] text-muted-foreground">Powerup Noise Level</label>
            <div class="flex items-center gap-1">
              <Input v-model.number="settings.powerup_noise_level_dbm" type="number" disabled class="h-8 font-mono text-xs" />
              <span class="text-muted-foreground text-[10px]">dBm</span>
            </div>
          </div>
        </div>
      </ConditionalFieldGroup>
    </div>
  </div>
</template>
