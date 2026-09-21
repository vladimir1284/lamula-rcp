<script setup lang="ts">
// ColorComposer.vue (mmi/src/components/domain/) -- D6
// Contenedor principal de Color Management / Color Composer.
//
// Une ColorTableEditor + Vista previa de gradiente continuo + Selector de magnitud
// (reflectividad / velocidad / width) + Informe de validación ΔE/CVD en tiempo real
// + Botón de reseteo a valores default CSS (main.css).
//
// Persistencia:
// Carga y guarda automáticamente los stops editados en `localStorage` con la clave
// namespaced `rcp.colorComposer.<kind>` (único punto de decisión para almacenamiento de paletas).

import { computed, ref, watch } from 'vue'
import ColorTableEditor from '@/components/domain/ColorTableEditor.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { buildDivergentScale, buildSequentialScale } from '@/lib/colorScales'
import {
  getActiveStops,
  removeStoredStops,
  resolvePalette,
  setStoredStops,
} from '@/lib/dataPalette'
import { DATA_KINDS, type DataKind } from '@/lib/mockRadar'
import { validatePaletteScale } from '@/lib/validatePalette'

const props = withDefaults(
  defineProps<{
    initialKind?: DataKind
  }>(),
  { initialKind: 'reflectivity' },
)

const emit = defineEmits<{
  'update:kind': [kind: DataKind]
  'palette-changed': [kind: DataKind]
}>()

const activeKind = ref<DataKind>(props.initialKind)
const currentStops = ref<string[]>(getActiveStops(props.initialKind))

// Reconstruir la escala continua de 256 escalones en tiempo real
const generatedScale = computed<string[]>(() => {
  if (activeKind.value === 'velocity') {
    return buildDivergentScale(currentStops.value, 256)
  }
  return buildSequentialScale(currentStops.value, 256)
})

// CSS linear gradient string a partir de la escala interpolada
const gradientCSS = computed<string>(() => {
  const colors = generatedScale.value
  if (colors.length === 0) return 'none'
  return `linear-gradient(to right, ${colors.join(', ')})`
})

// Informe de validación de contraste y ΔE / CVD
const validationReport = computed(() => {
  return validatePaletteScale(generatedScale.value)
})

function onKindChange(kind: DataKind) {
  activeKind.value = kind
  currentStops.value = getActiveStops(kind)
  emit('update:kind', kind)
}

function onStopsUpdate(newStops: string[]) {
  currentStops.value = newStops
  setStoredStops(activeKind.value, newStops)
  emit('palette-changed', activeKind.value)
}

function resetToDefault() {
  removeStoredStops(activeKind.value)
  currentStops.value = resolvePalette(activeKind.value)
  emit('palette-changed', activeKind.value)
}

watch(
  () => props.initialKind,
  (newKind) => {
    if (newKind !== activeKind.value) {
      onKindChange(newKind)
    }
  },
)
</script>

<template>
  <div class="flex flex-col gap-4 rounded-lg border border-border bg-card p-4 shadow-lg text-foreground">
    <div class="flex items-center justify-between border-b border-border pb-2">
      <div class="flex items-center gap-2">
        <h3 class="text-sm font-semibold">Color Composer (D6)</h3>
        <Badge variant="outline" class="text-[10px]">OKLCH Continuous</Badge>
      </div>
      <Button size="xs" variant="outline" @click="resetToDefault" title="Restaurar paleta de main.css">
        Reset Default
      </Button>
    </div>

    <!-- Selector de Magnitud -->
    <div class="flex items-center gap-2 text-xs">
      <span class="text-muted-foreground font-medium">Magnitud:</span>
      <div class="flex gap-1" role="tablist" aria-label="Magnitud de datos">
        <Button
          v-for="k in DATA_KINDS"
          :key="k.id"
          size="xs"
          :variant="activeKind === k.id ? 'secondary' : 'ghost'"
          role="tab"
          :aria-selected="activeKind === k.id"
          @click="onKindChange(k.id)"
        >
          {{ k.label }}
        </Button>
      </div>
    </div>

    <!-- Preview de Gradiente Continuo Interpolado -->
    <div class="space-y-1">
      <div class="flex justify-between text-[10px] text-muted-foreground">
        <span>{{ activeKind === 'velocity' ? 'Away (−)' : 'Min' }}</span>
        <span>Vista previa Rampa Continua (256 niveles)</span>
        <span>{{ activeKind === 'velocity' ? 'Toward (+)' : 'Max' }}</span>
      </div>
      <div
        class="h-8 w-full rounded-md border border-border shadow-xs"
        :style="{ background: gradientCSS }"
      />
    </div>

    <!-- Tabla Editable de Control Points / Stops -->
    <ColorTableEditor :stops="currentStops" @update:stops="onStopsUpdate" />

    <!-- Panel de Validación ΔE / CVD -->
    <div
      class="rounded-md border p-2.5 text-xs"
      :class="
        validationReport.valid
          ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
          : 'border-amber-500/30 bg-amber-500/10 text-amber-300'
      "
    >
      <div class="flex items-center justify-between font-medium">
        <span>Validación ΔE / CVD:</span>
        <span class="font-mono text-[11px]">ΔE Mín: {{ validationReport.minDeltaE }}</span>
      </div>
      <p v-if="validationReport.valid" class="mt-1 text-[11px] opacity-90">
        ✓ Rampa interpolada continua válida sin rupturas de contraste ni colapso CVD.
      </p>
      <ul v-else class="mt-1 list-disc pl-4 text-[10px] space-y-0.5 opacity-90">
        <li v-for="(issue, idx) in validationReport.adjacentIssues" :key="idx">
          {{ issue }}
        </li>
      </ul>
    </div>
  </div>
</template>
