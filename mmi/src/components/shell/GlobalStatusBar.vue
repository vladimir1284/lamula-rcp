<script setup lang="ts">
// A1: la barra que nunca se cubre. Compone identidad de sitio, autoridad de
// control (reutiliza ControlAuthorityCard, no lo reinventa), nivel de
// acceso (evidente y persistente en MANT con tooltip y temporizador),
// SI/SR/SD/RD, resumen de alarma y el par de relojes.
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import ControlAuthorityCard from '@/components/domain/ControlAuthorityCard.vue'
import EnvironmentBadge from './EnvironmentBadge.vue'
import IndicatorBar from './IndicatorBar.vue'
import AlarmSummaryButton from './AlarmSummaryButton.vue'
import ClockPair from './ClockPair.vue'
import type { ControlAuthorityState, MaintenanceState } from '@/types/mmi'
import type { IndicatorState, LampState } from '@/types/shell'

const props = defineProps<{
  siteName: string
  host: string
  simulated: boolean
  control: ControlAuthorityState | null
  accessLevel: 'OP' | 'MANT'
  maintenance?: MaintenanceState | null
  indicators: IndicatorState[]
  alarmWorst: LampState
  alarmCount: number
}>()

defineEmits<{ 'open-alarms': [] }>()

const now = ref(Date.now())
let timer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  timer = setInterval(() => {
    now.value = Date.now()
  }, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

const currentLevel = computed(() => props.maintenance?.level ?? props.accessLevel)
const isMant = computed(() => currentLevel.value === 'MANT')

const mantTooltip = computed(() => {
  if (!isMant.value || !props.maintenance) {
    return 'Nivel de acceso: Operador (OP)'
  }
  const actorStr = props.maintenance.actor ? `Actor: ${props.maintenance.actor}` : 'Actor desconocido'
  if (!props.maintenance.expires_wall) {
    return `Modo Mantenimiento (MANT) · ${actorStr}`
  }
  const expMs = new Date(props.maintenance.expires_wall).getTime()
  const remSec = Math.max(0, Math.floor((expMs - now.value) / 1000))
  const m = Math.floor(remSec / 60)
  const s = remSec % 60
  return `Modo Mantenimiento (MANT) · ${actorStr} · Expira en ${m}m ${s.toString().padStart(2, '0')}s`
})
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
    <Badge
      :variant="isMant ? 'destructive' : 'outline'"
      :class="isMant ? 'animate-pulse font-bold' : ''"
      :title="mantTooltip"
    >
      {{ currentLevel }}
    </Badge>

    <div class="ml-auto flex items-center gap-3">
      <IndicatorBar :indicators="indicators" />
      <AlarmSummaryButton :worst="alarmWorst" :count="alarmCount" @open="$emit('open-alarms')" />
      <ClockPair />
    </div>
  </div>
</template>
