<!--
  BurstAfcSetupView.vue: Vista E7 — Burst Pulse & AFC (Mb).

  Esta vista depende de telemetría AFC/burst aún no publicada por el proyecto DSP.
  No hay datos reales recibidos ni merge de dsp.latest_config. La configuración se
  persiste opacamente en app.state.burst_afc_settings.

  Conforme a pendientes-p1.md e inventario-ui.md:
  - Se omiten los indicadores de los seis estados de AFC (Disabled/Manual/NoBurst/Wait/Track/Locked)
    en la vista final ya que no provienen del radar y el documento prohíbe simularlos o fingirlos.
  - Reusa TernaryOverrideField.vue para los controles ternarios (Never/User/Always).
-->
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import ParameterGroupCard from '@/components/domain/ParameterGroupCard.vue'
import TernaryOverrideField from '@/components/domain/TernaryOverrideField.vue'
import { useGateway } from '@/composables/useGateway'
import type { BurstAfcSettings } from '@/types/mmi'

const { fetchBurstAfc, setBurstAfc } = useGateway()

const settings = ref<BurstAfcSettings>({
  tx_if_mhz: 30.0,
  rx_if_mhz: 30.0,
  if_increases_approaching: true,
  phase_lock_burst: 'never',
  min_burst_power_dbm: -10.0,
  burst_analysis_window: 'hamming',
  burst_estimator_settling_s: 0.01,
  afc_enabled: true,
  afc_servo_mode: 'dc_coupled',
  afc_wait_time_s: 1.0,
  afc_hysteresis_inner_khz: 50.0,
  afc_hysteresis_outer_khz: 200.0,
  afc_outer_tolerance_khz: 100.0,
  afc_feedback_slope: 1.0,
  afc_slew_rate_min: 0.1,
  afc_slew_rate_max: 10.0,
  afc_state: 'disabled',
  afc_format: 'bin',
  afc_format_act_low: false,
  afc_uplink_protocol: 'normal',
  fault_status_pin: 1,
  fault_pin_act_low: false,
  burst_freq_increases_with_afc_volts: true,
  enable_burst_tracking: 'never',
  enable_missing_burst_hunt: 'never',
  search_freq_intervals: 5,
  hop_settling_time_s: 0.05,
  auto_hunt_on_reset: false,
  repeat_auto_hunt_s: 10.0,
  burst_power_z0_correction: 'never',
  simulate_burst_samples: false,
  simulated_burst_span_start_mhz: 25.0,
  simulated_burst_span_stop_mhz: 35.0,
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
    settings.value = await fetchBurstAfc()
  } catch (err) {
    isError.value = true
    message.value = err instanceof Error ? err.message : 'Error al cargar configuración de Burst & AFC'
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  message.value = null
  isError.value = false
  try {
    settings.value = await setBurstAfc(settings.value)
    message.value = 'Configuración de Burst & AFC guardada correctamente.'
  } catch (err) {
    isError.value = true
    message.value = err instanceof Error ? err.message : 'Error al guardar configuración de Burst & AFC'
  } finally {
    saving.value = false
  }
}

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
          <h2 class="text-base font-bold tracking-tight">E7 — Burst Pulse & AFC (Mb)</h2>
          <Badge variant="outline" class="text-xs">Setup DSP</Badge>

          <Badge variant="outline" class="border-amber-500/50 bg-amber-500/10 text-amber-500 text-xs">
            Sin backend real
          </Badge>
        </div>
        <p class="text-xs text-muted-foreground mt-0.5">
          Parámetros del pulso de burst, servo de control automático de frecuencia (AFC) y seguimiento.
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

    <!-- Status Message -->
    <div
      v-if="message"
      class="rounded p-2 text-xs"
      :class="isError ? 'border border-destructive/50 bg-destructive/10 text-destructive' : 'border border-emerald-500/50 bg-emerald-500/10 text-emerald-500'"
    >
      {{ message }}
    </div>

    <!-- Callout note regarding DSP telemetry -->
    <div class="rounded border border-amber-500/40 bg-amber-500/5 p-3 text-amber-500/90 text-xs leading-relaxed">
      <strong>Nota de Integración:</strong> Esta vista depende de telemetría de AFC/burst no publicada
      aún por el contrato DSP. Los valores modificados aquí se persisten opacamente en el estado local del gateway RCP.
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- Ternary Overrides (Never / User / Always) -->
      <ParameterGroupCard
        title="Controles de Anulación Ternarios (Never / User / Always)"
        description="Sobreescritura de enganche de fase, seguimiento y corrección Z0"
      >
        <div class="space-y-1">
          <TernaryOverrideField
            v-model="settings.phase_lock_burst"
            label="PhaseLock to the burst pulse"
            description="Enganche de fase del receptor con el pulso transmitido burst"
            :supported="false"
          />
          <TernaryOverrideField
            v-model="settings.enable_burst_tracking"
            label="Enable Burst Pulse Tracking"
            description="Seguimiento automático de posición/frecuencia del pulso burst"
            :supported="false"
          />
          <TernaryOverrideField
            v-model="settings.enable_missing_burst_hunt"
            label="Enable Time/Freq hunt for missing burst"
            description="Búsqueda activa ante pérdida de señal del pulso burst"
            :supported="false"
          />
          <TernaryOverrideField
            v-model="settings.burst_power_z0_correction"
            label="Enable burst power based correction of Z0"
            description="Corrección de potencia cero Z0 basada en amplitud de burst"
            :supported="false"
          />
        </div>
      </ParameterGroupCard>

      <!-- Frequencies & Burst Parameters -->
      <ParameterGroupCard
        title="Frecuencias de FI y Parámetros del Burst"
        description="Frecuencias intermedias de Tx/Rx y nivel mínimo de potencia"
      >
        <div class="space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <div class="space-y-1">
              <label class="text-xs font-medium text-foreground">Tx Intermediate Freq (MHz)</label>
              <Input v-model.number="settings.tx_if_mhz" type="number" step="0.1" class="h-8 font-mono text-xs" />
            </div>
            <div class="space-y-1">
              <label class="text-xs font-medium text-foreground">Rx Intermediate Freq (MHz)</label>
              <Input v-model.number="settings.rx_if_mhz" type="number" step="0.1" class="h-8 font-mono text-xs" />
            </div>
          </div>

          <div class="flex items-center justify-between py-1 border-t border-border/40">
            <span class="text-xs font-medium text-foreground">IF increases for approaching target</span>
            <Button
              type="button"
              variant="outline"
              size="sm"
              class="h-7 text-[11px] font-mono"
              :class="settings.if_increases_approaching ? 'border-primary bg-primary/10 text-primary font-bold' : ''"
              @click="settings.if_increases_approaching = !settings.if_increases_approaching"
            >
              {{ settings.if_increases_approaching ? 'SI' : 'NO' }}
            </Button>
          </div>

          <div class="grid grid-cols-2 gap-3 pt-2 border-t border-border/40">
            <div class="space-y-1">
              <label class="text-xs font-medium text-foreground">Min Burst Power (dBm)</label>
              <Input v-model.number="settings.min_burst_power_dbm" type="number" step="0.5" class="h-8 font-mono text-xs" />
            </div>
            <div class="space-y-1">
              <label class="text-xs font-medium text-foreground">Estimator Settling Time (s)</label>
              <Input v-model.number="settings.burst_estimator_settling_s" type="number" step="0.001" class="h-8 font-mono text-xs" />
            </div>
          </div>

          <div class="space-y-1.5 pt-2 border-t border-border/40">
            <label class="text-xs font-medium text-foreground">Burst Analysis Window</label>
            <div class="grid grid-cols-3 gap-1.5">
              <Button
                v-for="w in (['rect', 'hamming', 'blackman'] as const)"
                :key="w"
                type="button"
                variant="outline"
                size="sm"
                class="text-[11px] font-mono capitalize"
                :class="settings.burst_analysis_window === w ? 'border-primary bg-primary/10 text-primary font-bold' : ''"
                @click="settings.burst_analysis_window = w"
              >
                {{ w }}
              </Button>
            </div>
          </div>
        </div>
      </ParameterGroupCard>

      <!-- AFC Loop & Servo Controls -->
      <ParameterGroupCard
        title="Lazo y Servo AFC"
        description="Histéresis, tolerancias y slew rates del servo AFC"
      >
        <div class="space-y-3">
          <div class="flex items-center justify-between py-1">
            <span class="text-xs font-medium text-foreground">Enable AFC / MFC functions</span>
            <Button
              type="button"
              variant="outline"
              size="sm"
              class="h-7 text-[11px] font-mono"
              :class="settings.afc_enabled ? 'border-primary bg-primary/10 text-primary font-bold' : ''"
              @click="settings.afc_enabled = !settings.afc_enabled"
            >
              {{ settings.afc_enabled ? 'ENABLED' : 'DISABLED' }}
            </Button>
          </div>

          <div class="space-y-1.5 border-t border-border/40 pt-2">
            <label class="text-xs font-medium text-foreground">AFC Servo Mode</label>
            <div class="grid grid-cols-2 gap-1.5">
              <Button
                type="button"
                variant="outline"
                size="sm"
                class="text-[11px] font-mono"
                :class="settings.afc_servo_mode === 'dc_coupled' ? 'border-primary bg-primary/10 text-primary font-bold' : ''"
                @click="settings.afc_servo_mode = 'dc_coupled'"
              >
                0: DC Coupled
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                class="text-[11px] font-mono"
                :class="settings.afc_servo_mode === 'motor_integrator' ? 'border-primary bg-primary/10 text-primary font-bold' : ''"
                @click="settings.afc_servo_mode = 'motor_integrator'"
              >
                1: Motor / Integrator
              </Button>
            </div>
          </div>

          <div class="grid grid-cols-3 gap-2 border-t border-border/40 pt-2">
            <div class="space-y-1">
              <label class="text-[11px] font-medium text-foreground">Wait Time (s)</label>
              <Input v-model.number="settings.afc_wait_time_s" type="number" step="0.1" class="h-8 font-mono text-xs" />
            </div>
            <div class="space-y-1">
              <label class="text-[11px] font-medium text-foreground">Inner Hyst. (kHz)</label>
              <Input v-model.number="settings.afc_hysteresis_inner_khz" type="number" step="1" class="h-8 font-mono text-xs" />
            </div>
            <div class="space-y-1">
              <label class="text-[11px] font-medium text-foreground">Outer Hyst. (kHz)</label>
              <Input v-model.number="settings.afc_hysteresis_outer_khz" type="number" step="1" class="h-8 font-mono text-xs" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3 border-t border-border/40 pt-2">
            <div class="space-y-1">
              <label class="text-xs font-medium text-foreground">Outer Tol. (kHz)</label>
              <Input v-model.number="settings.afc_outer_tolerance_khz" type="number" step="1" class="h-8 font-mono text-xs" />
            </div>
            <div class="space-y-1">
              <label class="text-xs font-medium text-foreground">Feedback Slope</label>
              <Input v-model.number="settings.afc_feedback_slope" type="number" step="0.1" class="h-8 font-mono text-xs" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3 border-t border-border/40 pt-2">
            <div class="space-y-1">
              <label class="text-xs font-medium text-foreground">Slew Rate Min</label>
              <Input v-model.number="settings.afc_slew_rate_min" type="number" step="0.1" class="h-8 font-mono text-xs" />
            </div>
            <div class="space-y-1">
              <label class="text-xs font-medium text-foreground">Slew Rate Max</label>
              <Input v-model.number="settings.afc_slew_rate_max" type="number" step="0.1" class="h-8 font-mono text-xs" />
            </div>
          </div>
        </div>
      </ParameterGroupCard>

      <!-- AFC Format, Uplink & Electrical Parameters -->
      <ParameterGroupCard
        title="Formato y Protocolo AFC Eléctrico"
        description="Formato de salida, bits, polaridad y pines"
      >
        <div class="space-y-3">
          <div class="space-y-1.5">
            <label class="text-xs font-medium text-foreground">AFC Word Format</label>
            <div class="grid grid-cols-3 gap-1.5">
              <Button
                v-for="fmt in (['bin', 'bcd', '8b4d'] as const)"
                :key="fmt"
                type="button"
                variant="outline"
                size="sm"
                class="text-[11px] font-mono uppercase"
                :class="settings.afc_format === fmt ? 'border-primary bg-primary/10 text-primary font-bold' : ''"
                @click="settings.afc_format = fmt"
              >
                {{ fmt }}
              </Button>
            </div>
          </div>

          <div class="space-y-1.5 border-t border-border/40 pt-2">
            <label class="text-xs font-medium text-foreground">Uplink Protocol</label>
            <div class="grid grid-cols-3 gap-1.5">
              <Button
                v-for="proto in (['off', 'normal', 'pin_map'] as const)"
                :key="proto"
                type="button"
                variant="outline"
                size="sm"
                class="text-[11px] font-mono capitalize"
                :class="settings.afc_uplink_protocol === proto ? 'border-primary bg-primary/10 text-primary font-bold' : ''"
                @click="settings.afc_uplink_protocol = proto"
              >
                {{ proto }}
              </Button>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3 border-t border-border/40 pt-2">
            <div class="space-y-1">
              <label class="text-xs font-medium text-foreground">FAULT Status Pin</label>
              <Input v-model.number="settings.fault_status_pin" type="number" class="h-8 font-mono text-xs" />
            </div>
            <div class="flex items-center justify-between pt-4">
              <span class="text-xs font-medium text-foreground">FAULT Pin ActLow</span>
              <Button
                type="button"
                variant="outline"
                size="sm"
                class="h-7 text-[11px] font-mono"
                :class="settings.fault_pin_act_low ? 'border-primary bg-primary/10 text-primary font-bold' : ''"
                @click="settings.fault_pin_act_low = !settings.fault_pin_act_low"
              >
                {{ settings.fault_pin_act_low ? 'SI' : 'NO' }}
              </Button>
            </div>
          </div>

          <div class="flex items-center justify-between border-t border-border/40 pt-2">
            <span class="text-xs font-medium text-foreground">AFC Format ActLow</span>
            <Button
              type="button"
              variant="outline"
              size="sm"
              class="h-7 text-[11px] font-mono"
              :class="settings.afc_format_act_low ? 'border-primary bg-primary/10 text-primary font-bold' : ''"
              @click="settings.afc_format_act_low = !settings.afc_format_act_low"
            >
              {{ settings.afc_format_act_low ? 'SI' : 'NO' }}
            </Button>
          </div>

          <div class="flex items-center justify-between border-t border-border/40 pt-2">
            <span class="text-xs font-medium text-foreground">Burst Freq ↑ with AFC Volts ↑</span>
            <Button
              type="button"
              variant="outline"
              size="sm"
              class="h-7 text-[11px] font-mono"
              :class="settings.burst_freq_increases_with_afc_volts ? 'border-primary bg-primary/10 text-primary font-bold' : ''"
              @click="settings.burst_freq_increases_with_afc_volts = !settings.burst_freq_increases_with_afc_volts"
            >
              {{ settings.burst_freq_increases_with_afc_volts ? 'SI' : 'NO' }}
            </Button>
          </div>
        </div>
      </ParameterGroupCard>

      <!-- Hunt & Simulation Settings -->
      <ParameterGroupCard
        title="Búsqueda y Simulación de Muestras"
        description="Parámetros de búsqueda en frecuencia y generador simulado"
      >
        <div class="space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <div class="space-y-1">
              <label class="text-xs font-medium text-foreground">Search Freq Intervals</label>
              <Input v-model.number="settings.search_freq_intervals" type="number" class="h-8 font-mono text-xs" />
            </div>
            <div class="space-y-1">
              <label class="text-xs font-medium text-foreground">Hop Settling Time (s)</label>
              <Input v-model.number="settings.hop_settling_time_s" type="number" step="0.01" class="h-8 font-mono text-xs" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3 border-t border-border/40 pt-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-medium text-foreground">Auto-Hunt on Reset</span>
              <Button
                type="button"
                variant="outline"
                size="sm"
                class="h-7 text-[11px] font-mono"
                :class="settings.auto_hunt_on_reset ? 'border-primary bg-primary/10 text-primary font-bold' : ''"
                @click="settings.auto_hunt_on_reset = !settings.auto_hunt_on_reset"
              >
                {{ settings.auto_hunt_on_reset ? 'SI' : 'NO' }}
              </Button>
            </div>
            <div class="space-y-1">
              <label class="text-xs font-medium text-foreground">Repeat Hunt Every (s)</label>
              <Input v-model.number="settings.repeat_auto_hunt_s" type="number" step="1" class="h-8 font-mono text-xs" />
            </div>
          </div>

          <div class="border-t border-border/40 pt-2 space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-medium text-foreground">Simulate Burst Samples</span>
              <Button
                type="button"
                variant="outline"
                size="sm"
                class="h-7 text-[11px] font-mono"
                :class="settings.simulate_burst_samples ? 'border-primary bg-primary/10 text-primary font-bold' : ''"
                @click="settings.simulate_burst_samples = !settings.simulate_burst_samples"
              >
                {{ settings.simulate_burst_samples ? 'ON' : 'OFF' }}
              </Button>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div class="space-y-1">
                <label class="text-[11px] font-medium text-foreground">Sim. Span Start (MHz)</label>
                <Input v-model.number="settings.simulated_burst_span_start_mhz" type="number" step="0.1" class="h-8 font-mono text-xs" />
              </div>
              <div class="space-y-1">
                <label class="text-[11px] font-medium text-foreground">Sim. Span Stop (MHz)</label>
                <Input v-model.number="settings.simulated_burst_span_stop_mhz" type="number" step="0.1" class="h-8 font-mono text-xs" />
              </div>
            </div>
          </div>
        </div>
      </ParameterGroupCard>
    </div>
  </div>
</template>
