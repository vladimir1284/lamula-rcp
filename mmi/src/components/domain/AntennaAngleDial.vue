<script setup lang="ts">
// Visualización angular en vivo de un eje de antena (AZ o EL), Rutina 05/06
// de AntennaControlView.vue. Sin arco de límites de software: PEND-RCP no
// tiene esa señal configurada todavía (ni backend ni config) -- se agrega el
// día que exista, no se inventa un rango aquí.
import { computed } from 'vue'
import { polarToCartesian } from '@/lib/polar'

const props = withDefaults(
  defineProps<{
    axis: 'azimuth' | 'elevation'
    valueDeg: number
    targetDeg?: number | null
    rateDegS?: number | null
    // Reservado para cuando exista la señal (PEND-RCP-20) -- nunca se
    // calcula ni se infiere acá, sólo se muestra si alguna vez llega.
    accelDegS2?: number | null
    toleranceDeg?: number | null
    valid?: boolean
  }>(),
  {
    targetDeg: null,
    rateDegS: null,
    accelDegS2: null,
    toleranceDeg: null,
    valid: true,
  },
)

const divergenceDeg = computed(() =>
  props.targetDeg === null ? null : Math.abs(props.valueDeg - props.targetDeg),
)

const diverged = computed(
  () =>
    divergenceDeg.value !== null &&
    props.toleranceDeg !== null &&
    divergenceDeg.value > props.toleranceDeg,
)

const needleToneClass = computed(() => {
  if (!props.valid) return 'text-state-fault'
  if (diverged.value) return 'text-state-warn'
  return 'text-telemetry-live'
})

// AZ: círculo completo, misma convención de ticks que AzimuthSectorDial
// (N/E/S/W, ángulo 0 = arriba, horario). EL: cuarto de círculo, 0° =
// horizonte (derecha), 90° = cenit (arriba) -- se reusa polarToCartesian
// mapeando el ángulo real de elevación a `90 - elDeg`.
const CX = 150
const CY = 150
const R_NEEDLE = 118
const R_TARGET = 118

const azTicks = [
  { label: 'N', x: 150, y: 20 },
  { label: 'E', x: 280, y: 150 },
  { label: 'S', x: 150, y: 280 },
  { label: 'W', x: 20, y: 150 },
]

function azPoint(deg: number) {
  return polarToCartesian(CX, CY, R_NEEDLE, deg)
}

function elPoint(deg: number) {
  return polarToCartesian(CX, CY, R_NEEDLE, 90 - deg)
}

const needleEnd = computed(() =>
  props.axis === 'azimuth' ? azPoint(props.valueDeg) : elPoint(props.valueDeg),
)
const targetEnd = computed(() => {
  if (props.targetDeg === null) return null
  return props.axis === 'azimuth' ? azPoint(props.targetDeg) : elPoint(props.targetDeg)
})
</script>

<template>
  <div class="flex flex-col items-center gap-1">
    <div class="relative">
      <!-- Glow decorativo detrás del dial -- mismo tono que el vector real,
           sin texto/dato propio, sólo da sensación de "scope encendido". -->
      <div
        class="pointer-events-none absolute inset-6 rounded-full blur-xl @xl:inset-8 @3xl:inset-10"
        :class="needleToneClass"
        style="background: currentColor; opacity: 0.08;"
      />
    <svg viewBox="0 0 300 300" class="relative h-40 w-40 select-none @xl:h-48 @xl:w-48 @3xl:h-56 @3xl:w-56">
      <template v-if="axis === 'azimuth'">
        <circle :cx="CX" :cy="CY" r="125" class="fill-muted/10 stroke-border" stroke-width="1.5" />
        <circle :cx="CX" :cy="CY" r="60" class="fill-background stroke-border" stroke-width="1.5" />
        <line :x1="CX - 118" :y1="CY" :x2="CX + 118" :y2="CY" class="stroke-border" stroke-width="1" />
        <line :x1="CX" :y1="CY - 118" :x2="CX" :y2="CY + 118" class="stroke-border" stroke-width="1" />
        <text
          v-for="t in azTicks"
          :key="t.label"
          :x="t.x"
          :y="t.y"
          text-anchor="middle"
          dominant-baseline="central"
          class="fill-muted-foreground text-[10px] font-bold"
        >
          {{ t.label }}
        </text>
      </template>
      <template v-else>
        <!-- Cuarto de círculo horizonte -> cenit. Sin sombreado de rango: no
             hay límite real confirmado para elevación todavía. -->
        <path
          d="M 32 150 A 118 118 0 0 1 150 32"
          fill="none"
          class="stroke-border"
          stroke-width="1.5"
        />
        <line :x1="32" :y1="150" :x2="150" :y2="150" class="stroke-border" stroke-dasharray="2 2" stroke-width="1" />
        <line :x1="150" :y1="32" :x2="150" :y2="150" class="stroke-border" stroke-dasharray="2 2" stroke-width="1" />
        <text x="26" y="166" text-anchor="start" class="fill-muted-foreground text-[9px]">0° HORIZONTE</text>
        <text x="150" y="20" text-anchor="middle" class="fill-muted-foreground text-[9px]">90° CENIT</text>
      </template>

      <!-- Setpoint fantasma (nominal) -->
      <line
        v-if="targetEnd"
        :x1="CX"
        :y1="CY"
        :x2="targetEnd.x"
        :y2="targetEnd.y"
        class="text-muted-foreground"
        stroke="currentColor"
        stroke-dasharray="3 3"
        stroke-width="1.5"
      />
      <circle v-if="targetEnd" :cx="targetEnd.x" :cy="targetEnd.y" r="3" class="fill-muted-foreground" />

      <!-- Vector real (actual) -->
      <line
        :x1="CX"
        :y1="CY"
        :x2="needleEnd.x"
        :y2="needleEnd.y"
        :class="needleToneClass"
        stroke="currentColor"
        stroke-width="2.5"
      />
      <circle
        :cx="needleEnd.x"
        :cy="needleEnd.y"
        r="4.5"
        :class="needleToneClass"
        fill="currentColor"
        class="drop-shadow-[0_0_4px_currentColor]"
      />
      <circle :cx="CX" :cy="CY" r="5" class="fill-foreground/70" />
    </svg>
    </div>

    <div class="flex flex-col items-center gap-0.5">
      <span
        class="font-mono text-2xl font-bold tracking-tight tabular-nums drop-shadow-[0_0_6px_currentColor]"
        :class="needleToneClass"
      >
        {{ valueDeg.toFixed(2) }}°
      </span>
      <div class="mt-1 grid w-full max-w-[220px] grid-cols-2 gap-1.5">
        <div class="rounded-md bg-muted/40 px-2 py-1">
          <span class="block text-[9px] uppercase tracking-wide text-muted-foreground">Vel. angular</span>
          <span v-if="rateDegS !== null" class="font-mono text-sm font-bold tabular-nums text-foreground">
            {{ rateDegS.toFixed(3) }}<span class="text-[10px] font-normal text-muted-foreground"> °/s</span>
          </span>
          <span v-else class="text-xs text-muted-foreground">sin señal</span>
        </div>
        <div class="rounded-md bg-muted/40 px-2 py-1" title="PEND-RCP-20 -- no existe señal de aceleración en ningún punto del sistema">
          <span class="block text-[9px] uppercase tracking-wide text-muted-foreground">Aceleración</span>
          <span v-if="accelDegS2 !== null" class="font-mono text-sm font-bold tabular-nums text-foreground">
            {{ accelDegS2.toFixed(3) }}<span class="text-[10px] font-normal text-muted-foreground"> °/s²</span>
          </span>
          <span v-else class="text-xs italic text-muted-foreground">sin señal</span>
        </div>
      </div>
      <span v-if="!valid" class="text-[10px] font-semibold text-state-fault">SIN DATO VÁLIDO</span>
      <span
        v-else-if="targetEnd"
        class="rounded-full px-2 py-0.5 text-[10px] font-semibold"
        :class="diverged ? 'bg-state-warn/10 text-state-warn' : 'bg-muted text-muted-foreground'"
      >
        <template v-if="diverged">Δ {{ divergenceDeg?.toFixed(2) }}° fuera de tolerancia</template>
        <template v-else>SETPOINT {{ targetDeg?.toFixed(2) }}°</template>
      </span>
    </div>
  </div>
</template>
