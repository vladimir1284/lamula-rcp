<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import ParameterGroupCard from '@/components/domain/ParameterGroupCard.vue'
import EquationPanel from '@/components/domain/EquationPanel.vue'
import SetSaveActions from '@/components/domain/SetSaveActions.vue'
import { Input } from '@/components/ui/input'
import { useGateway } from '@/composables/useGateway'
import type { RadarConstantParameters, RadarConstantSnapshot } from '@/types/mmi'

const { fetchRadarConstant, setRadarConstant, saveRadarConstant, maintenance } = useGateway()

const snapshot = ref<RadarConstantSnapshot | null>(null)
const draft = ref<RadarConstantParameters>({
  pulse_width_us: 1.0,
  zero_check_high_dbm: -75.0,
  zero_check_low_dbm: -80.0,
  tx_losses_db: 1.5,
  rx_losses_db: 1.5,
  radome_losses_db: 0.5,
  atmospheric_attenuation_db_km: 0.016,
  horizontal_beam_width_deg: 0.95,
  vertical_beam_width_deg: 0.95,
  antenna_gain_db: 45.0,
  wavelength_cm: 5.33,
  noise_figure_db: 2.5,
  filter_init_pulses: 4,
})

const activeField = ref<string | null>(null)
const dirty = ref(false)
const busy = ref(false)
const error = ref<string | null>(null)

const isMaintenanceUnlocked = computed(() => maintenance.value?.level === 'MANT')

async function load() {
  try {
    const res = await fetchRadarConstant()
    snapshot.value = res
    if (!dirty.value) {
      draft.value = { ...res.params }
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

function onInput(field: string) {
  activeField.value = field
  dirty.value = true
}

function onFocus(field: string) {
  activeField.value = field
}

function onBlur() {
  activeField.value = null
}

function resetDraft() {
  if (snapshot.value) {
    draft.value = { ...snapshot.value.params }
    dirty.value = false
    error.value = null
  }
}

async function doSet() {
  busy.value = true
  error.value = null
  try {
    const res = await setRadarConstant(draft.value)
    snapshot.value = res
    dirty.value = false
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
    if (dirty.value) {
      await setRadarConstant(draft.value)
    }
    const res = await saveRadarConstant()
    snapshot.value = res
    dirty.value = false
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    busy.value = false
  }
}

onMounted(() => {
  load()
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 overflow-auto p-4">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-3">
      <div>
        <h2 class="text-lg font-bold tracking-tight text-foreground">
          G7 — Radar Constant Parameters
        </h2>
        <p class="text-xs text-muted-foreground">
          RAVIS §7.4.6 (Misc) & §14.3.4 — Parámetros estáticos de instalación para el cálculo de la constante del radar.
        </p>
      </div>

      <!-- Indicador / Bloqueo por Mantenimiento -->
      <div class="flex items-center gap-2 text-xs">
        <span
          class="inline-block h-2 w-2 rounded-full"
          :class="isMaintenanceUnlocked ? 'bg-emerald-500' : 'bg-amber-500'"
        />
        <span class="font-medium text-muted-foreground">
          {{ isMaintenanceUnlocked ? 'Modo Mantenimiento Activo (Edición Permitida)' : 'Solo Lectura (Requiere Mantenimiento MANT)' }}
        </span>
      </div>
    </div>

    <!-- Banner de error si existe -->
    <div v-if="error" class="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-xs text-destructive">
      {{ error }}
    </div>

    <!-- Panel Superior: Ecuación y Resultado Calculado -->
    <div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
      <div class="lg:col-span-2">
        <EquationPanel :active-field="activeField" />
      </div>

      <div class="flex flex-col justify-between rounded-lg border border-border bg-card p-4 shadow-xs">
        <div>
          <span class="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Constante del Radar Calculada (C_r)
          </span>
          <div class="mt-2 flex items-baseline gap-2">
            <span class="font-mono text-3xl font-extrabold text-emerald-400">
              {{ snapshot?.radar_constant_db !== undefined ? snapshot.radar_constant_db.toFixed(2) : '—' }}
            </span>
            <span class="font-mono text-sm font-semibold text-muted-foreground">dB</span>
          </div>
          <p class="mt-2 text-xs text-muted-foreground">
            Constante derivada en dB enviada en la cabecera de radiales hacia el DSP/DRX.
          </p>
        </div>

        <div class="mt-4 border-t border-border/60 pt-3 text-xs text-muted-foreground">
          <span class="font-semibold text-foreground">Zero Check Status:</span>
          Se actualiza automáticamente durante la rutina de calibración de ruido.
        </div>
      </div>
    </div>

    <!-- Barra de Acciones Set / Save -->
    <SetSaveActions
      :dirty="dirty"
      :can-save="isMaintenanceUnlocked"
      save-blocked-reason="La edición y guardado requiere nivel de acceso Mantenimiento (MANT)"
      :busy="busy"
      @set="doSet"
      @save="doSave"
      @reset="resetDraft"
    />

    <!-- Grupos de Parámetros -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      <!-- 1. Ancho de Pulso y Ruido -->
      <ParameterGroupCard title="Ancho de Pulso & Zero Check" description="Pulsos nominales y calibración de ruido">
        <div class="space-y-3 text-xs">
          <div>
            <label class="block font-medium text-foreground">Pulse Width [µs]</label>
            <Input
              v-model.number="draft.pulse_width_us"
              type="number"
              step="0.1"
              :disabled="!isMaintenanceUnlocked || busy"
              class="mt-1 h-8 font-mono text-xs"
              @input="onInput('pulse_width_us')"
              @focus="onFocus('pulse_width_us')"
              @blur="onBlur"
            />
          </div>

          <div>
            <label class="block font-medium text-foreground">Zero Check High Ch [dBm]</label>
            <Input
              v-model.number="draft.zero_check_high_dbm"
              type="number"
              step="0.1"
              :disabled="!isMaintenanceUnlocked || busy"
              class="mt-1 h-8 font-mono text-xs"
              @input="onInput('zero_check_high_dbm')"
              @focus="onFocus('zero_check_high_dbm')"
              @blur="onBlur"
            />
          </div>

          <div>
            <label class="block font-medium text-foreground">Zero Check Low Ch [dBm]</label>
            <Input
              v-model.number="draft.zero_check_low_dbm"
              type="number"
              step="0.1"
              :disabled="!isMaintenanceUnlocked || busy"
              class="mt-1 h-8 font-mono text-xs"
              @input="onInput('zero_check_low_dbm')"
              @focus="onFocus('zero_check_low_dbm')"
              @blur="onBlur"
            />
          </div>
        </div>
      </ParameterGroupCard>

      <!-- 2. Pérdidas -->
      <ParameterGroupCard title="Pérdidas de RF & Atmósfera" description="Pérdidas en guía de onda y medio">
        <div class="space-y-3 text-xs">
          <div>
            <label class="block font-medium text-foreground">TX Losses [dB]</label>
            <Input
              v-model.number="draft.tx_losses_db"
              type="number"
              step="0.01"
              :disabled="!isMaintenanceUnlocked || busy"
              class="mt-1 h-8 font-mono text-xs"
              @input="onInput('tx_losses_db')"
              @focus="onFocus('tx_losses_db')"
              @blur="onBlur"
            />
          </div>

          <div>
            <label class="block font-medium text-foreground">RX Losses [dB]</label>
            <Input
              v-model.number="draft.rx_losses_db"
              type="number"
              step="0.01"
              :disabled="!isMaintenanceUnlocked || busy"
              class="mt-1 h-8 font-mono text-xs"
              @input="onInput('rx_losses_db')"
              @focus="onFocus('rx_losses_db')"
              @blur="onBlur"
            />
          </div>

          <div>
            <label class="block font-medium text-foreground">Radome Losses [dB]</label>
            <Input
              v-model.number="draft.radome_losses_db"
              type="number"
              step="0.01"
              :disabled="!isMaintenanceUnlocked || busy"
              class="mt-1 h-8 font-mono text-xs"
              @input="onInput('radome_losses_db')"
              @focus="onFocus('radome_losses_db')"
              @blur="onBlur"
            />
          </div>

          <div>
            <label class="block font-medium text-foreground">Atmospheric Atten. [dB/km]</label>
            <Input
              v-model.number="draft.atmospheric_attenuation_db_km"
              type="number"
              step="0.001"
              :disabled="!isMaintenanceUnlocked || busy"
              class="mt-1 h-8 font-mono text-xs"
              @input="onInput('atmospheric_attenuation_db_km')"
              @focus="onFocus('atmospheric_attenuation_db_km')"
              @blur="onBlur"
            />
          </div>
        </div>
      </ParameterGroupCard>

      <!-- 3. Antena -->
      <ParameterGroupCard title="Geometría de Antena" description="Anchos de haz y ganancia de reflector">
        <div class="space-y-3 text-xs">
          <div>
            <label class="block font-medium text-foreground">Horizontal Beam Width [°]</label>
            <Input
              v-model.number="draft.horizontal_beam_width_deg"
              type="number"
              step="0.01"
              :disabled="!isMaintenanceUnlocked || busy"
              class="mt-1 h-8 font-mono text-xs"
              @input="onInput('horizontal_beam_width_deg')"
              @focus="onFocus('horizontal_beam_width_deg')"
              @blur="onBlur"
            />
          </div>

          <div>
            <label class="block font-medium text-foreground">Vertical Beam Width [°]</label>
            <Input
              v-model.number="draft.vertical_beam_width_deg"
              type="number"
              step="0.01"
              :disabled="!isMaintenanceUnlocked || busy"
              class="mt-1 h-8 font-mono text-xs"
              @input="onInput('vertical_beam_width_deg')"
              @focus="onFocus('vertical_beam_width_deg')"
              @blur="onBlur"
            />
          </div>

          <div>
            <label class="block font-medium text-foreground">Antenna Gain [dB]</label>
            <Input
              v-model.number="draft.antenna_gain_db"
              type="number"
              step="0.1"
              :disabled="!isMaintenanceUnlocked || busy"
              class="mt-1 h-8 font-mono text-xs"
              @input="onInput('antenna_gain_db')"
              @focus="onFocus('antenna_gain_db')"
              @blur="onBlur"
            />
          </div>
        </div>
      </ParameterGroupCard>

      <!-- 4. Sistema -->
      <ParameterGroupCard title="Parámetros de Sistema" description="Frecuencia, figura de ruido y filtros">
        <div class="space-y-3 text-xs">
          <div>
            <label class="block font-medium text-foreground">Wavelength [cm]</label>
            <Input
              v-model.number="draft.wavelength_cm"
              type="number"
              step="0.01"
              :disabled="!isMaintenanceUnlocked || busy"
              class="mt-1 h-8 font-mono text-xs"
              @input="onInput('wavelength_cm')"
              @focus="onFocus('wavelength_cm')"
              @blur="onBlur"
            />
          </div>

          <div>
            <label class="block font-medium text-foreground">Noise Figure [dB] (opcional)</label>
            <Input
              :model-value="draft.noise_figure_db ?? undefined"
              type="number"
              step="0.1"
              :disabled="!isMaintenanceUnlocked || busy"
              class="mt-1 h-8 font-mono text-xs"
              @update:model-value="draft.noise_figure_db = $event === '' || $event === undefined ? null : Number($event); onInput('noise_figure_db')"
              @focus="onFocus('noise_figure_db')"
              @blur="onBlur"
            />
          </div>

          <div>
            <label class="block font-medium text-foreground">Filter Init Pulses</label>
            <Input
              v-model.number="draft.filter_init_pulses"
              type="number"
              step="1"
              :disabled="!isMaintenanceUnlocked || busy"
              class="mt-1 h-8 font-mono text-xs"
              @input="onInput('filter_init_pulses')"
              @focus="onFocus('filter_init_pulses')"
              @blur="onBlur"
            />
          </div>
        </div>
      </ParameterGroupCard>
    </div>
  </div>
</template>
