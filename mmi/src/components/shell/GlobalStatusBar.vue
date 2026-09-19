<script setup lang="ts">
// A1: la barra que nunca se cubre. Compone identidad de sitio, autoridad de
// control (reutiliza ControlAuthorityCard, no lo reinventa), nivel de
// acceso, SI/SR/SD/RD, resumen de alarma y el par de relojes -- en ese
// orden, izquierda a derecha, porque es el orden de "qué tan grave es si
// esto está mal" que recomienda el propio inventario para la vigilancia
// permanente (A6).
import { Badge } from '@/components/ui/badge'
import ControlAuthorityCard from '@/components/domain/ControlAuthorityCard.vue'
import EnvironmentBadge from './EnvironmentBadge.vue'
import IndicatorBar from './IndicatorBar.vue'
import AlarmSummaryButton from './AlarmSummaryButton.vue'
import ClockPair from './ClockPair.vue'
import type { ControlAuthorityState } from '@/types/mmi'
import type { IndicatorState, LampState } from '@/types/shell'

defineProps<{
  siteName: string
  host: string
  simulated: boolean
  control: ControlAuthorityState | null
  accessLevel: 'OP' | 'MANT'
  indicators: IndicatorState[]
  alarmWorst: LampState
  alarmCount: number
}>()

defineEmits<{ 'open-alarms': [] }>()
</script>

<template>
  <div
    class="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-border bg-card px-3 py-2 text-sm"
  >
    <div class="flex items-center gap-2">
      <span class="font-semibold">{{ siteName }}</span>
      <span class="text-xs text-muted-foreground">{{ host }}</span>
      <EnvironmentBadge :simulated="simulated" />
    </div>

    <div class="h-5 w-px bg-border" />

    <ControlAuthorityCard :control="control" />
    <Badge variant="outline">{{ accessLevel }}</Badge>

    <div class="ml-auto flex items-center gap-3">
      <IndicatorBar :indicators="indicators" />
      <AlarmSummaryButton :worst="alarmWorst" :count="alarmCount" @open="$emit('open-alarms')" />
      <ClockPair />
    </div>
  </div>
</template>
