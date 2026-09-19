<script setup lang="ts">
// Encabezado común de panel (pendiente #1 de las decisiones abiertas: "el
// encabezado común de panel"). Selector nativo <select> a propósito: ui/ no
// tiene todavía un primitivo Select de shadcn-vue y añadirlo era alcance
// fuera de este paso -- la API (viewId/@update:viewId) no cambia el día que
// se reemplace por uno.
//
// `frozen` cubre "cada uno se congela independientemente" (varios
// ASCOPE/PPI/RHI a la vez, docs/diseno/inventario-ui.md, Requisitos de
// concurrencia). Cuando `viewId` no está entre `viewOptions` (o su opción
// tiene `available:false`) se pinta el hueco "vista no aplicable" en vez del
// contenido -- ese es el caso de preset que el pendiente #1 deja abierto.
import { computed } from 'vue'
import { Button } from '@/components/ui/button'
import type { ViewOption } from '@/types/shell'

const props = withDefaults(
  defineProps<{
    viewId: string | null
    viewOptions: ViewOption[]
    frozen?: boolean
    closable?: boolean
  }>(),
  { frozen: false, closable: false },
)

defineEmits<{
  'update:viewId': [value: string]
  'toggle-freeze': []
  close: []
}>()

const selected = computed(() => props.viewOptions.find((v) => v.id === props.viewId))
const isApplicable = computed(() => !!selected.value?.available)
</script>

<template>
  <div class="flex h-full min-h-0 flex-col overflow-hidden rounded-md border border-border">
    <div class="flex items-center gap-2 border-b border-border bg-card px-2 py-1">
      <select
        class="min-w-0 flex-1 rounded-sm border border-border bg-background px-1.5 py-1 text-xs"
        :value="viewId ?? ''"
        @change="$emit('update:viewId', ($event.target as HTMLSelectElement).value)"
      >
        <option v-for="opt in viewOptions" :key="opt.id" :value="opt.id" :disabled="!opt.available">
          {{ opt.label }}{{ opt.available ? '' : ' (no aplicable)' }}
        </option>
      </select>
      <Button
        size="icon-xs"
        variant="ghost"
        :aria-pressed="frozen"
        :class="frozen ? 'text-state-simulated' : ''"
        title="Congelar panel"
        @click="$emit('toggle-freeze')"
      >
        ❄
      </Button>
      <Button v-if="closable" size="icon-xs" variant="ghost" title="Cerrar panel" @click="$emit('close')">
        ✕
      </Button>
    </div>
    <div class="min-h-0 flex-1 overflow-auto p-2">
      <div v-if="!isApplicable" class="flex h-full items-center justify-center text-xs text-muted-foreground">
        Vista no aplicable en este preset
      </div>
      <slot v-else />
    </div>
  </div>
</template>
