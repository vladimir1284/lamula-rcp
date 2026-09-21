<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const props = withDefaults(
  defineProps<{
    intervalS?: number
    enabled?: boolean
    lastRunAtWall?: string | null
    nextRunAtWall?: string | null
  }>(),
  {
    intervalS: 3600,
    enabled: true,
    lastRunAtWall: null,
    nextRunAtWall: null,
  },
)

function formatInterval(seconds: number): string {
  if (seconds >= 3600) {
    const hours = (seconds / 3600).toFixed(1).replace(/\.0$/, '')
    return `${seconds} s (${hours} h)`
  }
  if (seconds >= 60) {
    const mins = (seconds / 60).toFixed(1).replace(/\.0$/, '')
    return `${seconds} s (${mins} min)`
  }
  return `${seconds} s`
}

function formatDate(isoStr?: string | null): string {
  if (!isoStr) return '—'
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
        <CardTitle class="text-base font-semibold">Planificación de Ejecución Periódica</CardTitle>
        <Badge :variant="props.enabled ? 'default' : 'secondary'">
          {{ props.enabled ? 'Automático (Boot + Periódico)' : 'Desactivado' }}
        </Badge>
      </div>
    </CardHeader>
    <CardContent>
      <div class="grid grid-cols-1 gap-4 text-sm sm:grid-cols-3">
        <div class="flex flex-col gap-0.5">
          <span class="text-xs font-medium text-muted-foreground">Intervalo de Muestreo</span>
          <span class="font-medium">{{ formatInterval(props.intervalS) }}</span>
        </div>
        <div class="flex flex-col gap-0.5">
          <span class="text-xs font-medium text-muted-foreground">Última Ejecución</span>
          <span class="font-medium">{{ formatDate(props.lastRunAtWall) }}</span>
        </div>
        <div class="flex flex-col gap-0.5">
          <span class="text-xs font-medium text-muted-foreground">Próxima Ejecución Programada</span>
          <span class="font-medium">{{ formatDate(props.nextRunAtWall) }}</span>
        </div>
      </div>
    </CardContent>
  </Card>
</template>
