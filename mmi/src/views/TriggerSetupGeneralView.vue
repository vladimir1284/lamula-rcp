<!--
  TriggerSetupGeneralView.vue: Vista E5 — Trigger Setup general (Mt).
  Vista de solo lectura con 4 disparadores fijos de retardo/anchura.
  Sin polaridad ni término PRT (omitidos a propósito en esta UI).
-->
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import ParameterGroupCard from '@/components/domain/ParameterGroupCard.vue'
import { useGateway } from '@/composables/useGateway'
import type { TriggerSetupGeneralSnapshot } from '@/types/mmi'

const emit = defineEmits<{
  (e: 'navigate', viewId: string): void
}>()

const { fetchTriggerSetupGeneral } = useGateway()

const snapshot = ref<TriggerSetupGeneralSnapshot | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

async function loadData() {
  loading.value = true
  error.value = null
  try {
    snapshot.value = await fetchTriggerSetupGeneral()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Error al cargar configuración general de triggers'
  } finally {
    loading.value = false
  }
}

function navigateTo(viewId: string) {
  emit('navigate', viewId)
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
          <h2 class="text-base font-bold tracking-tight">E5 — Trigger Setup general (Mt)</h2>
          <Badge variant="outline" class="text-xs">Solo Lectura</Badge>
        </div>
        <p class="text-xs text-muted-foreground mt-0.5">
          Temporizado de disparadores (retardo y anchura). Parámetros fijos de hardware (RD100S).
        </p>
      </div>

      <div class="flex items-center gap-2">
        <Button variant="outline" size="sm" :disabled="loading" @click="loadData">
          Refrescar
        </Button>
        <Button variant="secondary" size="sm" @click="navigateTo('sector-blanking')">
          Blank output triggers within AZ/EL sectors
        </Button>
      </div>
    </div>

    <!-- Error Callout -->
    <div v-if="error" class="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-xs text-destructive">
      {{ error }}
    </div>

    <!-- Read-Only Trigger Timing Table -->
    <ParameterGroupCard
      title="Temporizado de Disparadores (General)"
      description="Retardos (start_us) y anchuras (width_us) por canal de disparo (read-only)"
    >
      <div class="overflow-x-auto">
        <table class="w-full text-left font-mono text-xs border-collapse">
          <thead>
            <tr class="border-b text-muted-foreground bg-muted/30">
              <th class="py-2 px-3">Trigger</th>
              <th class="py-2 px-3 text-right">Start (µs)</th>
              <th class="py-2 px-3 text-right">Width (µs)</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="trig in snapshot?.triggers || []"
              :key="trig.trigger_index"
              class="border-b/40 text-foreground/90 hover:bg-muted/20"
            >
              <td class="py-2 px-3 font-medium font-sans">{{ trig.name }}</td>
              <td class="py-2 px-3 text-right font-mono">{{ trig.start_us.toFixed(1) }}</td>
              <td class="py-2 px-3 text-right font-mono">{{ trig.width_us.toFixed(1) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="text-[11px] text-muted-foreground mt-3 italic">
        Los 4 disparadores de retardo y anchura son fijos de lectura en esta vista.
      </p>
    </ParameterGroupCard>
  </div>
</template>
