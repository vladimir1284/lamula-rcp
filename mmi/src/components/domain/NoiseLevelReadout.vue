<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

defineProps<{
  noiseHighDbm?: number | null
  noiseLowDbm?: number | null
  lastRunAtWall?: string | null
}>()

function formatNoise(val?: number | null): string {
  if (val === null || val === undefined) return '—'
  return `${val.toFixed(2)} dBm`
}

function formatDate(isoStr?: string | null): string {
  if (!isoStr) return 'Sin mediciones'
  try {
    return new Date(isoStr).toLocaleString()
  } catch {
    return isoStr
  }
}
</script>

<template>
  <Card>
    <CardHeader class="pb-2">
      <div class="flex items-center justify-between">
        <CardTitle class="text-base font-semibold">Muestreo de Piso de Ruido (Noise Levels)</CardTitle>
        <span class="text-xs text-muted-foreground">Última actualización: {{ formatDate(lastRunAtWall) }}</span>
      </div>
    </CardHeader>
    <CardContent>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div class="flex flex-col gap-1 rounded-lg border p-3 bg-card">
          <span class="text-xs font-medium text-muted-foreground">Canal Alto (High Channel)</span>
          <div class="flex items-baseline justify-between">
            <span class="text-2xl font-bold tracking-tight">
              {{ formatNoise(noiseHighDbm) }}
            </span>
            <Badge :variant="noiseHighDbm !== null && noiseHighDbm !== undefined ? 'default' : 'secondary'">
              {{ noiseHighDbm !== null && noiseHighDbm !== undefined ? 'OK' : 'Sin Dato' }}
            </Badge>
          </div>
        </div>

        <div class="flex flex-col gap-1 rounded-lg border p-3 bg-card">
          <span class="text-xs font-medium text-muted-foreground">Canal Bajo (Low Channel)</span>
          <div class="flex items-baseline justify-between">
            <span class="text-2xl font-bold tracking-tight">
              {{ formatNoise(noiseLowDbm) }}
            </span>
            <Badge :variant="noiseLowDbm !== null && noiseLowDbm !== undefined ? 'default' : 'secondary'">
              {{ noiseLowDbm !== null && noiseLowDbm !== undefined ? 'OK' : 'Sin Dato' }}
            </Badge>
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>
