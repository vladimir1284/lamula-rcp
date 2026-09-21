<script setup lang="ts">
import { computed, ref } from 'vue'
import SetupHubGrid, { type SetupHubItem } from '@/components/domain/SetupHubGrid.vue'
import ExportConfigButton from '@/components/domain/ExportConfigButton.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

const emit = defineEmits<{
  (e: 'navigate', viewId: string): void
}>()

// Definición de las vistas de la familia E (Setup DSP) y F (Ajuste asistido)
const hubItems = ref<SetupHubItem[]>([
  {
    id: 'mp-processing-options',
    code: 'E2',
    title: 'Processing Options (Mp)',
    family: 'Setup DSP',
    description: 'Espectros, algoritmos R2/microsupresión, series temporales, polarimetría y KDP.',
    dirty: true,
    access: 'MANT',
    available: false,
  },
  {
    id: 'thresholds-matrix',
    code: 'E3',
    title: 'Thresholds Matrix (Vp)',
    family: 'Setup DSP',
    description: 'Matriz de 19 parámetros × 5 umbrales y banderas TCF (solo lectura).',
    dirty: false,
    access: 'MANT',
    available: true,
  },
  {
    id: 'clutter-filters',
    code: 'E4',
    title: 'Clutter Filters (Mf)',
    family: 'Setup DSP',
    description: 'Filtros de clutter fijos, variables y modelo gaussiano con anchos Doppler.',
    dirty: false,
    access: 'MANT',
    available: false,
  },
  {
    id: 'trigger-setup-general',
    code: 'E5',
    title: 'Trigger Setup General (Mt)',
    family: 'Setup DSP',
    description: 'PRF, ancho de pulso, pretrigger externo y sector blanking de triggers.',
    dirty: true,
    access: 'MANT',
    available: false,
  },
  {
    id: 'trigger-setup-pw',
    code: 'E6',
    title: 'Trigger Setup por Pulse Width (Mt<n>)',
    family: 'Setup DSP',
    description: 'Tabla de retardo y anchura de triggers (solo lectura de alineación).',
    dirty: false,
    access: 'MANT',
    available: false,
  },
  {
    id: 'mb-setup',
    code: 'E7',
    title: 'Burst Pulse & AFC (Mb)',
    family: 'Setup DSP',
    description: 'Frecuencias IF, umbral de burst, lazo AFC (DC/Motor) y mapa de pines.',
    dirty: false,
    access: 'MANT',
    available: true,
  },
  {
    id: 'transmissions-modulations',
    code: 'E8',
    title: 'Transmissions & Modulations (Mz)',
    family: 'Setup DSP',
    description: 'Modulación de fase, canales A/B y chirping FM según tipo de transmisor.',
    dirty: false,
    access: 'MANT',
    available: false,
  },
  {
    id: 'top-level-configuration',
    code: 'E9',
    title: 'Top-Level Configuration (Mc)',
    family: 'Setup DSP',
    description: 'Red UDP, reloj IFD, entradas de ángulo TAG y modo de receptor.',
    dirty: false,
    access: 'MANT',
    available: false,
  },
  {
    id: 'debug-options',
    code: 'E10',
    title: 'Debug Options (M+)',
    family: 'Setup DSP',
    description: 'Nivel de ruido para datos simulados y flip de signo Nyquist.',
    dirty: false,
    access: 'MANT',
    available: false,
  },
  {
    id: 'config-profiles',
    code: 'E11',
    title: 'Config Profiles (F/S/R)',
    family: 'Setup DSP',
    description: 'Comparación y transferencia entre ajustes Current, Saved y Factory.',
    dirty: false,
    access: 'MANT',
    available: false,
  },
  {
    id: 'dsp-internal-status',
    code: 'E12',
    title: 'DSP Internal Status (V/Vz)',
    family: 'Setup DSP',
    description: 'Diagnósticos, prioridades de proceso, TrigRAM, contadores y registros GPARM.',
    dirty: false,
    access: 'MANT',
    available: false,
  },
  {
    id: 'pb-plot',
    code: 'F1',
    title: 'Burst Pulse Timing (Pb)',
    family: 'Ajuste',
    description: 'Plot en vivo para captura y centrado del pulso de transmisión.',
    dirty: false,
    access: 'MANT',
    available: true,
  },
  {
    id: 'ps-plot',
    code: 'F2',
    title: 'Burst Spectra & Matched Filter (Ps)',
    family: 'Ajuste',
    description: 'Espectro del burst, diseño de filtro adaptado y lazo de seguimiento AFC.',
    dirty: false,
    access: 'MANT',
    available: false,
  },
  {
    id: 'pr-plot',
    code: 'F3',
    title: 'Receiver Waveforms (Pr)',
    family: 'Ajuste',
    description: 'Formas de onda en IF y potencia LOG para verificación de sensibilidad.',
    dirty: false,
    access: 'MANT',
    available: false,
  },
  {
    id: 'pa-plot',
    code: 'F4',
    title: 'Tx Waveform Ambiguity (Pa)',
    family: 'Ajuste',
    description: 'Diagrama de ambigüedad para verificación de lóbulos laterales en pulso comprimido.',
    dirty: false,
    access: 'MANT',
    available: false,
  },
])

const dirtyCount = computed(() => hubItems.value.filter((i) => i.dirty).length)
const hasDirty = computed(() => dirtyCount.value > 0)

function handleSelect(itemId: string) {
  emit('navigate', itemId)
}

function handleApplyAll() {
  // Simulación del comando TTY / guardar
  hubItems.value.forEach((item) => {
    item.dirty = false
  })
}

function handleRevertAll() {
  // Simulación de restaurar desde saved
  hubItems.value.forEach((item) => {
    item.dirty = false
  })
}
</script>

<template>
  <div class="flex h-full flex-col gap-3 p-4 overflow-y-auto bg-background text-foreground">
    <!-- Encabezado de la vista E1 -->
    <div class="flex flex-wrap items-center justify-between gap-3 border-b pb-3">
      <div>
        <div class="flex items-center gap-2">
          <h2 class="text-base font-bold tracking-tight">E1 — DSP Setup Hub</h2>
          <Badge v-if="hasDirty" variant="destructive" class="text-xs">
            {{ dirtyCount }} grupo(s) modificado(s) respecto a saved
          </Badge>
          <Badge v-else variant="outline" class="text-xs text-muted-foreground">
            Sincronizado con saved
          </Badge>
        </div>
        <p class="text-xs text-muted-foreground mt-0.5">
          Hub de navegación y gestión de parámetros para el procesador de señal (DSP / RVP900).
        </p>
      </div>

      <div class="flex items-center gap-2">
        <ExportConfigButton />
        <Button
          v-if="hasDirty"
          size="sm"
          variant="default"
          class="h-8 text-xs"
          @click="handleApplyAll"
        >
          Guardar cambios en NVRAM (S)
        </Button>
        <Button
          v-if="hasDirty"
          size="sm"
          variant="outline"
          class="h-8 text-xs"
          @click="handleRevertAll"
        >
          Restaurar de saved (R)
        </Button>
      </div>
    </div>

    <!-- Banner informativo si hay cambios pendientes -->
    <div
      v-if="hasDirty"
      class="flex items-center justify-between rounded-md border border-amber-500/40 bg-amber-500/10 p-2.5 text-xs text-amber-700 dark:text-amber-400"
    >
      <div class="flex items-center gap-2">
        <span class="font-bold">⚠️ Atención:</span>
        <span>
          Hay ajustes modificados en memoria volátil respecto a la NVRAM. Salir o reiniciar sin guardar revertirá los cambios.
        </span>
      </div>
    </div>

    <!-- Grilla de navegación SetupHubGrid -->
    <SetupHubGrid :items="hubItems" @select="handleSelect" />
  </div>
</template>
