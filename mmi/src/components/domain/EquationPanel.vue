<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  activeField?: string | null
}>()

function isHighlighted(fields: string[]): boolean {
  if (!props.activeField) return false
  return fields.includes(props.activeField)
}
</script>

<template>
  <div class="rounded-lg border border-border bg-slate-950 p-4 font-mono text-sm shadow-inner">
    <div class="mb-3 flex items-center justify-between border-b border-slate-800 pb-2">
      <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">
        Ecuación de la Constante del Radar (C_r)
      </span>
      <span class="text-xs text-slate-500">
        RAVIS §14.3.4
      </span>
    </div>

    <!-- Ecuación principal en LaTeX-style HTML -->
    <div class="my-3 flex flex-wrap items-center justify-center gap-2 text-base text-slate-200">
      <span class="font-bold text-emerald-400">C_r</span>
      <span>=</span>

      <!-- Fracción Principal -->
      <div class="inline-flex flex-col items-center px-1">
        <!-- Numerador -->
        <div class="border-b border-slate-600 pb-1 text-center font-medium">
          <span>π³ · |K|² · </span>
          <span
            class="rounded px-1.5 py-0.5 transition-colors"
            :class="isHighlighted(['antenna_gain_db']) ? 'bg-amber-500/30 text-amber-300 ring-1 ring-amber-400' : 'text-slate-200'"
          >
            G²
          </span>
          <span> · </span>
          <span
            class="rounded px-1.5 py-0.5 transition-colors"
            :class="isHighlighted(['horizontal_beam_width_deg']) ? 'bg-amber-500/30 text-amber-300 ring-1 ring-amber-400' : 'text-slate-200'"
          >
            θ
          </span>
          <span> · </span>
          <span
            class="rounded px-1.5 py-0.5 transition-colors"
            :class="isHighlighted(['vertical_beam_width_deg']) ? 'bg-amber-500/30 text-amber-300 ring-1 ring-amber-400' : 'text-slate-200'"
          >
            φ
          </span>
          <span> · c · </span>
          <span
            class="rounded px-1.5 py-0.5 transition-colors"
            :class="isHighlighted(['pulse_width_us']) ? 'bg-amber-500/30 text-amber-300 ring-1 ring-amber-400' : 'text-slate-200'"
          >
            τ
          </span>
        </div>

        <!-- Denominador -->
        <div class="pt-1 text-center font-medium">
          <span>1024 · ln(2) · </span>
          <span
            class="rounded px-1.5 py-0.5 transition-colors"
            :class="isHighlighted(['wavelength_cm']) ? 'bg-amber-500/30 text-amber-300 ring-1 ring-amber-400' : 'text-slate-200'"
          >
            λ²
          </span>
          <span> · </span>
          <span
            class="rounded px-1.5 py-0.5 transition-colors"
            :class="isHighlighted(['tx_losses_db', 'rx_losses_db', 'radome_losses_db']) ? 'bg-amber-500/30 text-amber-300 ring-1 ring-amber-400' : 'text-slate-200'"
          >
            L_total
          </span>
        </div>
      </div>
    </div>

    <!-- Leyenda de Términos -->
    <div class="mt-4 grid grid-cols-2 gap-2 border-t border-slate-800/80 pt-3 text-xs text-slate-400 sm:grid-cols-4">
      <div
        class="flex items-center gap-1.5 rounded p-1 transition-colors"
        :class="isHighlighted(['antenna_gain_db']) ? 'bg-amber-500/20 text-amber-300 font-semibold' : ''"
      >
        <span class="font-mono text-slate-200">G:</span> Ganancia Antena (dB)
      </div>
      <div
        class="flex items-center gap-1.5 rounded p-1 transition-colors"
        :class="isHighlighted(['horizontal_beam_width_deg']) ? 'bg-amber-500/20 text-amber-300 font-semibold' : ''"
      >
        <span class="font-mono text-slate-200">θ:</span> Ancho Azimut (°)
      </div>
      <div
        class="flex items-center gap-1.5 rounded p-1 transition-colors"
        :class="isHighlighted(['vertical_beam_width_deg']) ? 'bg-amber-500/20 text-amber-300 font-semibold' : ''"
      >
        <span class="font-mono text-slate-200">φ:</span> Ancho Elevación (°)
      </div>
      <div
        class="flex items-center gap-1.5 rounded p-1 transition-colors"
        :class="isHighlighted(['pulse_width_us']) ? 'bg-amber-500/20 text-amber-300 font-semibold' : ''"
      >
        <span class="font-mono text-slate-200">τ:</span> Ancho Pulso (µs)
      </div>
      <div
        class="flex items-center gap-1.5 rounded p-1 transition-colors"
        :class="isHighlighted(['wavelength_cm']) ? 'bg-amber-500/20 text-amber-300 font-semibold' : ''"
      >
        <span class="font-mono text-slate-200">λ:</span> Longitud de onda (cm)
      </div>
      <div
        class="flex items-center gap-1.5 rounded p-1 transition-colors"
        :class="isHighlighted(['tx_losses_db', 'rx_losses_db', 'radome_losses_db']) ? 'bg-amber-500/20 text-amber-300 font-semibold' : ''"
      >
        <span class="font-mono text-slate-200">L_total:</span> Pérdidas TX+RX+Radoma
      </div>
      <div class="flex items-center gap-1.5 rounded p-1">
        <span class="font-mono text-slate-200">|K|²:</span> 0.93 (Agua líquida)
      </div>
    </div>
  </div>
</template>
