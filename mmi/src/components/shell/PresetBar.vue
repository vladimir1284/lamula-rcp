<script setup lang="ts">
// Barra de presets de A1. Cada preset es una fila de la tabla de
// concurrencia (docs/diseno/inventario-ui.md, "Requisitos de concurrencia");
// las de cuatro vistas fijan el máximo de paneles del mosaico.
import { Button } from '@/components/ui/button'
import type { MosaicPreset } from '@/types/shell'

defineProps<{
  presets: MosaicPreset[]
  activePresetId: string | null
}>()

defineEmits<{
  select: [id: string]
  manage: []
}>()
</script>

<template>
  <div class="flex items-center gap-1.5 overflow-x-auto border-b border-border bg-background px-2 py-1.5">
    <Button
      v-for="p in presets"
      :key="p.id"
      size="sm"
      :variant="p.id === activePresetId ? 'default' : 'outline'"
      @click="$emit('select', p.id)"
    >
      {{ p.label }}
    </Button>
    <Button size="sm" variant="ghost" class="ml-auto" @click="$emit('manage')">Gestionar presets…</Button>
  </div>
</template>
