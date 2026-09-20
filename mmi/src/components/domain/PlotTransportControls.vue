<script setup lang="ts">
import { Button } from '@/components/ui/button'

defineProps<{
  running: boolean
  hasData: boolean
  canStart: boolean
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'start'): void
  (e: 'stop'): void
  (e: 'continue'): void
  (e: 'clear'): void
}>()
</script>

<template>
  <div class="flex flex-wrap items-center gap-2">
    <!-- Iniciar (Start) -- sólo cuando NO está corriendo y NO hay datos congelados en buffer -->
    <Button
      v-if="!running && !hasData"
      size="sm"
      :disabled="disabled || !canStart"
      @click="emit('start')"
    >
      Iniciar Captura
    </Button>

    <!-- Detener (Stop) -- sólo cuando está corriendo -->
    <Button
      v-if="running"
      variant="destructive"
      size="sm"
      :disabled="disabled"
      @click="emit('stop')"
    >
      Detener
    </Button>

    <!-- Reanudar (Continue) -- cuando NO está corriendo pero hay datos en buffer -->
    <Button
      v-if="!running && hasData"
      variant="default"
      size="sm"
      :disabled="disabled"
      @click="emit('continue')"
    >
      Reanudar Captura
    </Button>

    <!-- Borrar (Clear) -- cuando hay datos o está configurado -->
    <Button
      v-if="hasData || !running"
      variant="outline"
      size="sm"
      :disabled="disabled || (!hasData && !canStart)"
      @click="emit('clear')"
    >
      Limpiar
    </Button>
  </div>
</template>
