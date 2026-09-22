<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import ParameterGroupCard from '@/components/domain/ParameterGroupCard.vue'
import TernaryOverrideField from '@/components/domain/TernaryOverrideField.vue'
import { useGateway } from '@/composables/useGateway'
import type { ProcessingOptionsSettings } from '@/types/mmi'

const { fetchProcessingOptions, setProcessingOptions } = useGateway()

const settings = ref<ProcessingOptionsSettings>({
  spectral_window: 'user',
  r2_processing: 'never',
  clutter_microsuppression: 'never',
  ppp_autocorrels: 'user',
  unfold_velocity: 'always',
  process_custom_trigs: 'never',
  interference_filter: 'none',
  phidp_offset_deg: 0.0,
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
    settings.value = await fetchProcessingOptions()
  } catch (err) {
    isError.value = true
    message.value = err instanceof Error ? err.message : 'Error al cargar opciones de procesamiento'
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  message.value = null
  isError.value = false
  try {
    settings.value = await setProcessingOptions(settings.value)
    message.value = 'Opciones de procesamiento actualizadas correctamente.'
  } catch (err) {
    isError.value = true
    message.value = err instanceof Error ? err.message : 'Error al guardar opciones de procesamiento'
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
          <h2 class="text-base font-bold tracking-tight">E2 — Processing Options (Mp)</h2>
          <Badge variant="outline" class="text-xs">Setup DSP</Badge>
        </div>
        <p class="text-xs text-muted-foreground mt-0.5">
          Opciones generales de procesamiento de señales, desambiguación y filtros RFI.
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

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- Ternary Overrides (Never / User / Always) -->
      <ParameterGroupCard
        title="Controles de Anulación Ternarios (Never / User / Always)"
        description="Sobreescritura de algoritmos de momentos, velocidad y triggers"
      >
        <div class="space-y-1">
          <TernaryOverrideField
            v-model="settings.r2_processing"
            label="R2 Processing"
            description="Cálculo preciso R0, R1, R2 de ancho espectral"
            :supported="false"
          />
          <TernaryOverrideField
            v-model="settings.clutter_microsuppression"
            label="Clutter Microsuppression"
            description="Supresión de micro-clutter en la densidad de potencia"
            :supported="false"
          />
          <TernaryOverrideField
            v-model="settings.ppp_autocorrels"
            label="PPP autocorrels from DFTs"
            description="Autocorrelaciones pulse-pair calculadas desde espectro DFT"
            :supported="false"
          />
          <TernaryOverrideField
            v-model="settings.unfold_velocity"
            label="Unfold Velocity (Vh-Vl)"
            description="Desplegado de velocidad dual-PRF o PRT escalonado"
            :supported="false"
          />
          <TernaryOverrideField
            v-model="settings.process_custom_trigs"
            label="Process w/ custom trigs"
            description="Procesamiento con patrones de trigger personalizados"
            :supported="false"
          />
        </div>
      </ParameterGroupCard>

      <!-- Windows & RFI Filters -->
      <div class="space-y-4">
        <ParameterGroupCard
          title="Ventanas Espectrales y Filtros RFI"
          description="Selección de ventana de ponderación y filtrado de interferencias"
        >
          <div class="space-y-3">
            <div class="space-y-1.5">
              <div class="flex items-center justify-between">
                <label class="text-xs font-medium text-foreground">Spectral Window</label>
                <Badge variant="outline" class="border-amber-500/50 bg-amber-500/10 text-amber-500 text-[9px]">Sin backend</Badge>
              </div>
              <div class="grid grid-cols-4 gap-1.5">
                <Button
                  v-for="w in (['user', 'rect', 'hamming', 'blackman'] as const)"
                  :key="w"
                  type="button"
                  variant="outline"
                  size="sm"
                  class="text-[11px] font-mono capitalize"
                  :class="settings.spectral_window === w ? 'border-primary bg-primary/10 text-primary font-bold' : ''"
                  @click="settings.spectral_window = w"
                >
                  {{ w }}
                </Button>
              </div>
            </div>

            <div class="space-y-1.5 pt-2 border-t border-border/40">
              <div class="flex items-center justify-between">
                <label class="text-xs font-medium text-foreground">Interference Filter (RFI)</label>
                <Badge variant="outline" class="border-amber-500/50 bg-amber-500/10 text-amber-500 text-[9px]">Sin backend</Badge>
              </div>
              <div class="grid grid-cols-4 gap-1.5">
                <Button
                  v-for="f in (['none', 'alg1', 'alg2', 'alg3'] as const)"
                  :key="f"
                  type="button"
                  variant="outline"
                  size="sm"
                  class="text-[11px] font-mono uppercase"
                  :class="settings.interference_filter === f ? 'border-primary bg-primary/10 text-primary font-bold' : ''"
                  @click="settings.interference_filter = f"
                >
                  {{ f }}
                </Button>
              </div>
            </div>
          </div>
        </ParameterGroupCard>

        <!-- Polarimetric Adjustments -->
        <ParameterGroupCard
          title="Ajustes Polarimétricos"
          description="Offset de fase diferencial ΦDP"
        >
          <div class="space-y-1.5">
            <div class="flex items-center justify-between">
              <label class="text-xs font-medium text-foreground">PhiDP Offset (deg)</label>
              <Badge variant="outline" class="border-emerald-500/50 text-emerald-500 text-[10px]">Dato real (solo lectura)</Badge>
            </div>
            <div class="flex items-center gap-2">
              <Input
                :model-value="settings.phidp_offset_deg"
                type="number"
                disabled
                class="h-8 font-mono text-xs"
              />
              <span class="text-muted-foreground font-mono">deg</span>
            </div>
            <p class="text-[11px] text-muted-foreground">
              Desfasaje estático de sistema aplicado a la fase diferencial cruzada ΦDP, reportado
              por el DSP. No editable: no existe escritura RCP→DSP para este campo hoy.
            </p>
          </div>
        </ParameterGroupCard>
      </div>
    </div>
  </div>
</template>
