<!--
  ThresholdMatrixView.vue: Vista E3 — Thresholds Matrix (Vp).
  Gaps / decisiones documentadas:
  1. La vista es de solo lectura (decisión 2026-09-19): los umbrales provienen del DSP.
  2. El contrato actual del DSP expone umbrales globales (sqi_threshold, log_threshold, ccor_threshold, sig_threshold).
  3. Las celdas o parámetros que no existen per-parámetro en el contrato actual se muestran explícitamente como "N/D" (no disponible).
  4. La columna de patrón TCF se omite por no existir en el contrato actual.
-->
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useGateway } from '@/composables/useGateway'
import type { ThresholdMatrixSnapshot } from '@/types/mmi'

const { fetchThresholdsMatrix } = useGateway()

const snapshot = ref<ThresholdMatrixSnapshot | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

async function refresh() {
  loading.value = true
  error.value = null
  try {
    snapshot.value = await fetchThresholdsMatrix()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  refresh()
})

function formatValue(val: number | null, unit: string = ''): string {
  if (val === null || val === undefined) return 'N/D'
  return `${val}${unit ? ' ' + unit : ''}`
}
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 overflow-auto p-3">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold text-foreground">E3 Thresholds Matrix (Vp)</h2>
        <p class="text-xs text-muted-foreground">
          Matriz de umbrales del procesador de señal (solo lectura).
        </p>
      </div>
      <Button size="sm" :disabled="loading" @click="refresh">
        {{ loading ? 'Actualizando...' : 'Actualizar' }}
      </Button>
    </div>

    <p v-if="error" class="text-xs font-medium text-destructive">
      {{ error }}
    </p>

    <!-- Sección 1: Umbrales Globales Configurados -->
    <Card>
      <CardHeader>
        <CardTitle>Umbrales Globales (Configuración DSP)</CardTitle>
      </CardHeader>
      <CardContent>
        <div v-if="!snapshot" class="text-xs text-muted-foreground">
          Sin datos de umbrales.
        </div>
        <div v-else class="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div class="rounded-md border p-2.5">
            <span class="text-xs text-muted-foreground">LOG Threshold</span>
            <div class="mt-1 font-mono text-sm font-semibold text-foreground">
              {{ formatValue(snapshot.globals.log_threshold, 'dB') }}
            </div>
          </div>
          <div class="rounded-md border p-2.5">
            <span class="text-xs text-muted-foreground">CCOR Threshold</span>
            <div class="mt-1 font-mono text-sm font-semibold text-foreground">
              {{ formatValue(snapshot.globals.ccor_threshold, 'dB') }}
            </div>
          </div>
          <div class="rounded-md border p-2.5">
            <span class="text-xs text-muted-foreground">SIG Threshold</span>
            <div class="mt-1 font-mono text-sm font-semibold text-foreground">
              {{ formatValue(snapshot.globals.sig_threshold, 'dB') }}
            </div>
          </div>
          <div class="rounded-md border p-2.5">
            <span class="text-xs text-muted-foreground">SQI Threshold</span>
            <div class="mt-1 font-mono text-sm font-semibold text-foreground">
              {{ formatValue(snapshot.globals.sqi_threshold) }}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Sección 2: Matriz de Umbrales por Parámetro -->
    <Card>
      <CardHeader>
        <CardTitle class="flex items-center justify-between">
          <span>Matriz por Parámetro de Dato</span>
          <span v-if="snapshot" class="text-xs font-normal text-muted-foreground">
            {{ snapshot.rows.length }} parámetros
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div v-if="!snapshot" class="text-xs text-muted-foreground">
          Sin datos de matriz de umbrales.
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="border-b bg-muted/50 text-muted-foreground">
              <tr>
                <th class="p-2 font-medium">Parámetro</th>
                <th class="p-2 font-medium">LOG (dB)</th>
                <th class="p-2 font-medium">CCOR (dB)</th>
                <th class="p-2 font-medium">SIG (dB)</th>
                <th class="p-2 font-medium">SQI</th>
                <th class="p-2 font-medium">PMI</th>
              </tr>
            </thead>
            <tbody class="divide-y">
              <tr v-for="row in snapshot.rows" :key="row.parameter">
                <td class="p-2 font-mono font-bold text-foreground">{{ row.parameter }}</td>
                <td class="p-2 font-mono">
                  <span v-if="row.log_db !== null">{{ row.log_db }} dB</span>
                  <Badge v-else variant="outline" class="text-[10px] text-muted-foreground">N/D</Badge>
                </td>
                <td class="p-2 font-mono">
                  <span v-if="row.ccor_db !== null">{{ row.ccor_db }} dB</span>
                  <Badge v-else variant="outline" class="text-[10px] text-muted-foreground">N/D</Badge>
                </td>
                <td class="p-2 font-mono">
                  <span v-if="row.sig_db !== null">{{ row.sig_db }} dB</span>
                  <Badge v-else variant="outline" class="text-[10px] text-muted-foreground">N/D</Badge>
                </td>
                <td class="p-2 font-mono">
                  <span v-if="row.sqi !== null">{{ row.sqi }}</span>
                  <Badge v-else variant="outline" class="text-[10px] text-muted-foreground">N/D</Badge>
                </td>
                <td class="p-2 font-mono">
                  <span v-if="row.pmi !== null">{{ row.pmi }}</span>
                  <Badge v-else variant="outline" class="text-[10px] text-muted-foreground">N/D</Badge>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
