<script setup lang="ts">
// Tarjeta de autoridad de control (badge + actor + since_wall) -- antes
// duplicada en ControlCenterView.vue (con edición) y SystemInformationView.vue
// (solo lectura). `editable` decide si se muestran los controles de edición;
// el badge ahora siempre se muestra (con '...' si `control` es null todavía),
// mismo criterio que ya tenía la variante editable -- pequeña mejora visual
// para la variante de solo lectura, que antes colapsaba a puro texto muted.
import { computed } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import type { ControlAuthorityState } from '@/types/mmi'

const props = withDefaults(
  defineProps<{
    control: ControlAuthorityState | null
    editable?: boolean
    actor?: string
    busy?: boolean
  }>(),
  { editable: false, actor: '', busy: false },
)

defineEmits<{
  'update:actor': [value: string]
  toggle: []
}>()

const variant = computed(() => (props.control?.mode === 'active' ? 'default' : 'secondary'))
</script>

<template>
  <div class="flex flex-wrap items-center gap-3">
    <Badge :variant="variant">{{ control?.mode ?? '...' }}</Badge>
    <span v-if="control" class="text-sm text-muted-foreground">
      {{ control.actor }} desde {{ new Date(control.since_wall).toLocaleTimeString() }}
    </span>
    <template v-if="editable">
      <Separator orientation="vertical" class="h-6" />
      <Input
        :model-value="actor"
        placeholder="actor"
        class="w-40"
        @update:model-value="$emit('update:actor', String($event))"
      />
      <Button :disabled="!control || busy" @click="$emit('toggle')">
        {{ control?.mode === 'active' ? 'Ceder control' : 'Tomar control' }}
      </Button>
    </template>
  </div>
</template>
