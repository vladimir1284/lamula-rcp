<script setup lang="ts">
// Lectura de cursor común a D2/D3/D4: distancia, azimut, elevación e
// intensidad; RHI añade altura (docs/diseno/inventario-ui.md §D4). `null`
// = sin cursor fijado todavía (nunca se pintó antes de un primer click).
import type { DataKind } from '@/lib/mockRadar'

defineProps<{
  cursor: {
    rangeKm: number
    azimuthDeg?: number
    elevationDeg?: number
    heightKm?: number
    value: number
    kind: DataKind
  } | null
}>()

const UNIT: Record<DataKind, string> = {
  reflectivity: 'norm.',
  velocity: 'norm.',
  width: 'norm.',
}
</script>

<template>
  <div class="flex flex-wrap gap-x-3 gap-y-0.5 rounded-sm border border-border bg-card px-2 py-1 text-[11px] tabular-nums">
    <template v-if="cursor">
      <span>R <strong>{{ cursor.rangeKm.toFixed(1) }}</strong> km</span>
      <span v-if="cursor.azimuthDeg !== undefined">AZ <strong>{{ cursor.azimuthDeg.toFixed(1) }}</strong>°</span>
      <span v-if="cursor.elevationDeg !== undefined">EL <strong>{{ cursor.elevationDeg.toFixed(1) }}</strong>°</span>
      <span v-if="cursor.heightKm !== undefined">H <strong>{{ cursor.heightKm.toFixed(2) }}</strong> km</span>
      <span>{{ cursor.kind }} <strong>{{ cursor.value.toFixed(2) }}</strong> {{ UNIT[cursor.kind] }}</span>
    </template>
    <span v-else class="text-muted-foreground">Click sobre el plot para fijar cursor</span>
  </div>
</template>
