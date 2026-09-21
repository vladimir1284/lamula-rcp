<script setup lang="ts">
import { Button } from '@/components/ui/button'

defineProps<{
  dirty: boolean
  canSave?: boolean
  saveBlockedReason?: string
  busy?: boolean
}>()

const emit = defineEmits<{
  set: []
  save: []
  reset: []
}>()
</script>

<template>
  <div class="flex flex-wrap items-center justify-between gap-3 rounded-md border border-border bg-card/60 p-3 shadow-xs">
    <div class="flex items-center gap-2">
      <span
        class="inline-block h-2.5 w-2.5 rounded-full"
        :class="dirty ? 'bg-amber-500 animate-pulse' : 'bg-emerald-500'"
      />
      <span class="text-xs font-medium text-foreground">
        {{ dirty ? 'Cambios sin aplicar / no persistidos' : 'Parámetros sincronizados' }}
      </span>
    </div>

    <div class="flex items-center gap-2">
      <Button
        variant="outline"
        size="sm"
        :disabled="!dirty || busy"
        @click="emit('reset')"
      >
        Descartar
      </Button>

      <Button
        variant="secondary"
        size="sm"
        :disabled="!dirty || busy"
        class="font-semibold text-blue-400 hover:text-blue-300"
        @click="emit('set')"
      >
        Set (Volátil)
      </Button>

      <Button
        variant="default"
        size="sm"
        :disabled="canSave === false || busy"
        :title="canSave === false ? saveBlockedReason : 'Guardar en disco como predeterminado'"
        class="bg-emerald-600 font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
        @click="emit('save')"
      >
        Save (Persistente)
      </Button>
    </div>
  </div>
</template>
