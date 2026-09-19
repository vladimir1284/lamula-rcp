<script setup lang="ts">
// Gestión de presets (pendiente #1: "crear, renombrar, restablecer").
// Panel inline, no diálogo modal: ui/ no tiene todavía un primitivo Dialog
// de shadcn-vue y añadirlo era alcance fuera de este paso. El padre decide
// cuándo mostrarlo (v-if), igual que haría con un modal real el día que
// exista -- este componente no sabe nada de overlays.
import { ref } from 'vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { MosaicPreset } from '@/types/shell'

const props = defineProps<{
  presets: MosaicPreset[]
}>()

defineEmits<{
  rename: [id: string, label: string]
  reset: [id: string]
  remove: [id: string]
  duplicateCurrent: []
  close: []
}>()

const draft = ref<Record<string, string>>(
  Object.fromEntries(props.presets.map((p) => [p.id, p.label])),
)
</script>

<template>
  <div class="w-80 rounded-md border border-border bg-card p-3 shadow-md">
    <div class="mb-2 flex items-center justify-between">
      <h3 class="text-sm font-semibold">Presets</h3>
      <Button size="icon-xs" variant="ghost" @click="$emit('close')">✕</Button>
    </div>
    <ul class="space-y-1.5">
      <li v-for="p in presets" :key="p.id" class="flex items-center gap-1.5">
        <Input v-model="draft[p.id]" class="h-7 flex-1 text-xs" @change="$emit('rename', p.id, draft[p.id]!)" />
        <Button size="icon-xs" variant="ghost" :disabled="p.builtin" title="Restablecer" @click="$emit('reset', p.id)">
          ↺
        </Button>
        <Button size="icon-xs" variant="ghost" :disabled="p.builtin" title="Eliminar" @click="$emit('remove', p.id)">
          ✕
        </Button>
      </li>
    </ul>
    <Button size="sm" variant="outline" class="mt-3 w-full" @click="$emit('duplicateCurrent')">
      Nuevo preset desde el mosaico actual
    </Button>
  </div>
</template>
