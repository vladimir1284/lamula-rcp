<script setup lang="ts">
// Barra de nivel genérica para cualquier magnitud acotada [min, max] -- hueco
// de "analógicas" anotado en el diseño de B2 (Subsystem Detail). Primer uso
// real: distancia al setpoint vs tolerancia en Posicionar (Rutina 6,
// AntennaControlView.vue). El color es semántico (ok/warn/fault), no
// decorativo -- misma escala que Button variant="ok|warn" e IndicatorLamp.
const props = withDefaults(
  defineProps<{
    value: number
    min?: number
    max: number
    label?: string
    tone?: 'ok' | 'warn' | 'fault' | 'neutral'
    unit?: string
  }>(),
  {
    min: 0,
    tone: 'neutral',
    unit: '',
  },
)

const TONE_CLASS: Record<NonNullable<typeof props.tone>, string> = {
  ok: 'bg-state-ok',
  warn: 'bg-state-warn',
  fault: 'bg-state-fault',
  neutral: 'bg-foreground/70',
}

function pct(value: number, min: number, max: number) {
  if (max <= min) return 0
  return Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100))
}
</script>

<template>
  <div class="flex flex-col gap-1">
    <div v-if="label" class="flex items-center justify-between text-xs text-muted-foreground">
      <span>{{ label }}</span>
      <span class="font-mono tabular-nums text-foreground">{{ value.toFixed(2) }}{{ unit }}</span>
    </div>
    <div class="h-1.5 w-full overflow-hidden rounded-full bg-muted">
      <div
        class="h-full rounded-full transition-all"
        :class="TONE_CLASS[tone]"
        :style="{ width: pct(value, min, max) + '%' }"
      />
    </div>
  </div>
</template>
