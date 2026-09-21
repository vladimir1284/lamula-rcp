<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const props = withDefaults(
  defineProps<{
    radiating: boolean
    requiredSeconds?: number
    initialElapsedSeconds?: number
  }>(),
  {
    requiredSeconds: 1200,
    initialElapsedSeconds: 0,
  },
)

const emit = defineEmits<{
  (e: 'warmupChange', complete: boolean, elapsedSeconds: number): void
}>()

const elapsedSeconds = ref(props.initialElapsedSeconds)
let timer: ReturnType<typeof setInterval> | null = null

const isComplete = computed(() => elapsedSeconds.value >= props.requiredSeconds)
const progressPercent = computed(() =>
  Math.min(100, Math.round((elapsedSeconds.value / props.requiredSeconds) * 100)),
)

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

function startTimer() {
  if (timer) clearInterval(timer)
  timer = setInterval(() => {
    if (props.radiating) {
      if (elapsedSeconds.value < props.requiredSeconds) {
        elapsedSeconds.value += 1
      }
    }
  }, 1000)
}

watch(
  () => props.radiating,
  (isRadiating) => {
    if (!isRadiating) {
      // Si deja de radiar, se congela/reinicia según especificación
      elapsedSeconds.value = 0
    }
    emit('warmupChange', isComplete.value, elapsedSeconds.value)
  },
)

watch(elapsedSeconds, (newVal) => {
  emit('warmupChange', newVal >= props.requiredSeconds, newVal)
})

onMounted(() => {
  startTimer()
  emit('warmupChange', isComplete.value, elapsedSeconds.value)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <Card>
    <CardHeader class="pb-2">
      <div class="flex items-center justify-between">
        <CardTitle class="text-base font-semibold">Temporizador de Caldeo (20 min Radiación)</CardTitle>
        <Badge :variant="radiating ? 'default' : 'secondary'">
          {{ radiating ? '● RADIANDO' : '○ INACTIVO' }}
        </Badge>
      </div>
    </CardHeader>
    <CardContent class="flex flex-col gap-3">
      <div class="flex items-center justify-between text-sm font-medium">
        <span>Tiempo Transcurrido: {{ formatTime(elapsedSeconds) }} / {{ formatTime(requiredSeconds) }}</span>
        <span :class="isComplete ? 'text-state-ok font-bold' : 'text-muted-foreground'">
          {{ isComplete ? '✓ Caldeo Completo' : `${progressPercent}%` }}
        </span>
      </div>

      <!-- Barra de progreso -->
      <div class="h-2.5 w-full overflow-hidden rounded-full bg-secondary">
        <div
          class="h-full transition-all duration-300"
          :class="isComplete ? 'bg-state-ok' : radiating ? 'bg-primary' : 'bg-muted-foreground'"
          :style="{ width: `${progressPercent}%` }"
        />
      </div>

      <p class="text-xs text-muted-foreground">
        <template v-if="!radiating">
          El transmisor no está radiando. El temporizador requiere 20 minutos contíduos de radiación activa para habilitar la calibración.
        </template>
        <template v-else-if="!isComplete">
          Caldeo en progreso... Mantenga la radiación activa durante {{ formatTime(requiredSeconds - elapsedSeconds) }} adicionales.
        </template>
        <template v-else>
          El transmisor ha alcanzado la estabilidad térmica requerida. El inicio del procedimiento de calibración está habilitado.
        </template>
      </p>
    </CardContent>
  </Card>
</template>
