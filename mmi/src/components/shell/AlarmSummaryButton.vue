<script setup lang="ts">
// A1 "Resumen de alarma": semáforo BiTE agregado, clicable hacia B8/B9.
// `worst` decide el color del semáforo; `count` es cuántas fallas activas
// resume (0 con worst='ok' se pinta igual, en verde, sin número).
import { computed } from 'vue'
import type { LampState } from '@/types/shell'

const props = defineProps<{
  worst: LampState
  count: number
}>()

defineEmits<{ open: [] }>()

const dotClass = computed(() => ({
  'bg-state-ok': props.worst === 'ok',
  'bg-state-disabled': props.worst === 'neutral',
  'bg-state-fault': props.worst === 'fault',
}))
</script>

<template>
  <button
    type="button"
    class="inline-flex items-center gap-1.5 rounded-md border border-border px-2 py-1 text-xs hover:bg-muted"
    @click="$emit('open')"
  >
    <span class="size-2.5 rounded-full" :class="dotClass" />
    <span>BITE</span>
    <span v-if="count > 0" class="tabular-nums font-semibold">{{ count }}</span>
  </button>
</template>
