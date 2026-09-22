<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import ParameterGroupCard from '@/components/domain/ParameterGroupCard.vue'
import ConditionalFieldGroup from '@/components/domain/ConditionalFieldGroup.vue'
import { useGateway } from '@/composables/useGateway'
import type { ClutterFilterSettings } from '@/types/mmi'

const { fetchClutterFilters } = useGateway()

const settings = ref<ClutterFilterSettings>({
  clutter_filter: 'gmap',
  clutter_width_ms: 1.0,
  fixed_win: 0,
  fixed_width_pts: 5,
  fixed_edge_pts: 2,
  variable_hunt_pts: 3,
  secondary_sqi_slope: 0.0,
  secondary_sqi_offset: 0.0,
})

const loading = ref(false)
const message = ref<string | null>(null)
const isError = ref(false)

async function loadData() {
  loading.value = true
  message.value = null
  isError.value = false
  try {
    settings.value = await fetchClutterFilters()
  } catch (err) {
    isError.value = true
    message.value = err instanceof Error ? err.message : 'Error al cargar filtros de clutter'
  } finally {
    loading.value = false
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
          <h2 class="text-base font-bold tracking-tight">E4 — Clutter Filters (Mf)</h2>
          <Badge variant="outline" class="text-xs">Setup DSP / Solo lectura</Badge>
        </div>
        <p class="text-xs text-muted-foreground mt-0.5">
          Filtros de clutter fijos, variables y modelo gaussiano (GMAP) con anchos Doppler. Sin
          canal de escritura RCP→DSP hoy: vista de monitoreo, no de configuración.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <Button variant="outline" size="sm" :disabled="loading" @click="loadData">
          Refrescar
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
      <!-- Filtros Gaussianos (#5, #6, #7) - Real Backend -->
      <ParameterGroupCard
        title="Filtros Modelo Gaussiano (#5 - #7)"
        description="Filtro de clutter Doppler activo en el DSP (GMAP / Notch)"
      >
        <div class="space-y-4">
          <div class="space-y-1.5">
            <div class="flex items-center justify-between">
              <label class="text-xs font-medium text-foreground">Tipo de Filtro Algorítmico</label>
              <Badge variant="outline" class="border-emerald-500/50 text-emerald-500 text-[10px]">Dato real (solo lectura)</Badge>
            </div>
            <div class="flex gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled
                class="flex-1 text-xs"
                :class="settings.clutter_filter === 'gmap' ? 'border-primary bg-primary/10 text-primary font-bold' : ''"
              >
                GMAP (Gaussiano)
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled
                class="flex-1 text-xs"
                :class="settings.clutter_filter === 'notch' ? 'border-primary bg-primary/10 text-primary font-bold' : ''"
              >
                Notch
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled
                class="flex-1 text-xs"
                :class="settings.clutter_filter === 'none' ? 'border-primary bg-primary/10 text-primary font-bold' : ''"
              >
                Desactivado
              </Button>
            </div>
            <p class="text-[11px] text-muted-foreground">
              Filtro activo reportado por el DSP. El RCP no tiene hoy un canal para escribirlo
              (docs/diseno/pendientes-p1.md, familia E).
            </p>
          </div>

          <div class="space-y-1.5">
            <div class="flex items-center justify-between">
              <label class="text-xs font-medium text-foreground">Spectrum Width (clutter_width_ms)</label>
              <Badge variant="outline" class="border-emerald-500/50 text-emerald-500 text-[10px]">Dato real (solo lectura)</Badge>
            </div>
            <div class="flex items-center gap-2">
              <Input
                :model-value="settings.clutter_width_ms"
                type="number"
                disabled
                class="h-8 font-mono text-xs"
              />
              <span class="text-muted-foreground font-mono">m/s</span>
            </div>
            <p class="text-[11px] text-muted-foreground">
              Ancho espectral del modelo de clutter gaussiano en metros por segundo, reportado por
              el DSP. No editable: no existe escritura RCP→DSP para este campo hoy.
            </p>
          </div>
        </div>
      </ParameterGroupCard>

      <!-- Filtros Fijos (#1, #2, #3) - Mock -->
      <ConditionalFieldGroup
        title="Filtros Fijos #1, #2, #3 (Fixed Notch)"
        description="Filtros de muesca de ancho predeterminado en bins espectrales"
        :supported="false"
      >
        <div class="grid grid-cols-3 gap-3">
          <div class="space-y-1">
            <label class="text-[11px] text-muted-foreground">Win (Ventana)</label>
            <Input v-model.number="settings.fixed_win" type="number" disabled class="h-8 font-mono text-xs" />
          </div>
          <div class="space-y-1">
            <label class="text-[11px] text-muted-foreground">WidthPts (Pts)</label>
            <Input v-model.number="settings.fixed_width_pts" type="number" disabled class="h-8 font-mono text-xs" />
          </div>
          <div class="space-y-1">
            <label class="text-[11px] text-muted-foreground">EdgePts (Pts)</label>
            <Input v-model.number="settings.fixed_edge_pts" type="number" disabled class="h-8 font-mono text-xs" />
          </div>
        </div>
      </ConditionalFieldGroup>

      <!-- Filtro Variable (#4) - Mock -->
      <ConditionalFieldGroup
        title="Filtro Variable #4 (Adaptive Notch)"
        description="Filtro adaptativo con búsqueda activa de ancho"
        :supported="false"
      >
        <div class="grid grid-cols-2 gap-3">
          <div class="space-y-1">
            <label class="text-[11px] text-muted-foreground">HuntPts (Búsqueda)</label>
            <Input v-model.number="settings.variable_hunt_pts" type="number" disabled class="h-8 font-mono text-xs" />
          </div>
          <div class="space-y-1">
            <label class="text-[11px] text-muted-foreground">Secondary SQI Slope</label>
            <Input v-model.number="settings.secondary_sqi_slope" type="number" disabled class="h-8 font-mono text-xs" />
          </div>
        </div>
      </ConditionalFieldGroup>

      <!-- Parámetros Relacionados - Mock -->
      <ParameterGroupCard
        title="Parámetros Auxiliares RVP900"
        description="Umbrales de rechazo y errores de fase no expuestos en contrato v1.3"
      >
        <div class="space-y-2">
          <div class="flex items-center justify-between text-xs py-1 border-b border-border/40">
            <span class="text-muted-foreground">Max power mismatch across octants</span>
            <span class="font-mono text-foreground/60">— dB (no expuesto)</span>
          </div>
          <div class="flex items-center justify-between text-xs py-1 border-b border-border/40">
            <span class="text-muted-foreground">High power rejection threshold</span>
            <span class="font-mono text-foreground/60">— dB (no expuesto)</span>
          </div>
          <div class="flex items-center justify-between text-xs py-1">
            <span class="text-muted-foreground">Maximum KEY phase error</span>
            <span class="font-mono text-foreground/60">— deg (no expuesto)</span>
          </div>
        </div>
      </ParameterGroupCard>
    </div>
  </div>
</template>
