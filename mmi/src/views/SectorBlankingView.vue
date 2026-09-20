<!--
  SectorBlankingView.vue: Vista C5 — Sector Blanking Editor (Fase Local).
  Muestra 8 sectores con InUse, rango AZ y rango EL, el marcador grafico
  AzimuthSectorDial y persistencia local en el backend RCP.
  Incluye el badge explicativo visible "No aplicado al hardware".
-->
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import AzimuthSectorDial from '@/components/domain/AzimuthSectorDial.vue'
import SectorBlankingEditor from '@/components/domain/SectorBlankingEditor.vue'
import { useGateway } from '@/composables/useGateway'
import type { SectorBlankingProfile } from '@/types/mmi'

const { fetchSectorBlanking, setSectorBlanking, saveSectorBlanking } = useGateway()

const profile = ref<SectorBlankingProfile>({
  enabled: false,
  sectors: Array.from({ length: 8 }, () => ({
    in_use: false,
    az_start_deg: 0,
    az_end_deg: 45,
    el_start_deg: -90,
    el_end_deg: 90,
  })),
})

const busy = ref(false)
const error = ref<string | null>(null)
const successMessage = ref<string | null>(null)
const selectedSectorIndex = ref<number | null>(null)

async function refresh() {
  try {
    profile.value = await fetchSectorBlanking()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

async function handleSet(updated: SectorBlankingProfile) {
  busy.value = true
  error.value = null
  successMessage.value = null
  try {
    profile.value = await setSectorBlanking(updated)
    successMessage.value = 'Perfil aplicado localmente en memoria (volátil).'
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    busy.value = false
  }
}

async function handleSave(updated: SectorBlankingProfile) {
  busy.value = true
  error.value = null
  successMessage.value = null
  try {
    await handleSet(updated)
    profile.value = await saveSectorBlanking()
    successMessage.value = 'Perfil de sectores guardado en la persistencia local del RCP.'
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    busy.value = false
  }
}

onMounted(() => {
  refresh()
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 overflow-auto p-3">
    <!-- Header with Title & Hardware Status Badge -->
    <div class="flex flex-wrap items-center justify-between gap-2 border-b pb-2">
      <div>
        <h2 class="text-lg font-semibold text-foreground">C5 Sector Blanking Editor</h2>
        <p class="text-xs text-muted-foreground">
          Edición de sectores de inhibición de radiación / adquisición.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <Badge variant="outline" class="border-amber-500/50 bg-amber-500/10 text-amber-500 font-semibold px-2.5 py-1 text-xs">
          ⚠️ No aplicado al hardware
        </Badge>
      </div>
    </div>

    <!-- Explanatory Callout Banner -->
    <Card class="border-amber-500/30 bg-amber-500/10">
      <CardContent class="p-3 text-xs text-amber-900 dark:text-amber-200 leading-relaxed">
        <strong class="font-semibold text-amber-700 dark:text-amber-400">Aviso de Fase Local:</strong>
        El hardware DSP está bloqueado en esta fase. Los cambios se guardan y gestionan únicamente en la persistencia local del RCP (<code class="font-mono text-[11px]">data/sector_blanking.json</code>) y no afectan la transmisión real del radar.
      </CardContent>
    </Card>

    <!-- Error & Success Banners -->
    <p v-if="error" class="text-xs font-medium text-destructive bg-destructive/10 border border-destructive/20 rounded p-2">
      {{ error }}
    </p>
    <p v-if="successMessage" class="text-xs font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded p-2">
      {{ successMessage }}
    </p>

    <!-- Main Grid Layout -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
      <!-- Azimuth Sector Dial Diagram -->
      <div class="lg:col-span-4 flex flex-col items-center justify-center rounded-lg border bg-card p-3">
        <AzimuthSectorDial
          :sectors="profile.sectors"
          :enabled="profile.enabled"
          :selected-index="selectedSectorIndex"
          @select-sector="(idx) => selectedSectorIndex = idx"
        />
        <p class="text-[11px] text-muted-foreground text-center mt-1">
          Haga clic en un sector del diagrama para seleccionarlo en la tabla.
        </p>
      </div>

      <!-- Sector Blanking Form Editor -->
      <div class="lg:col-span-8">
        <SectorBlankingEditor
          :profile="profile"
          :busy="busy"
          :selected-index="selectedSectorIndex"
          @update:profile="(p) => profile = p"
          @set="handleSet"
          @save="handleSave"
          @select-sector="(idx) => selectedSectorIndex = idx"
        />
      </div>
    </div>
  </div>
</template>
