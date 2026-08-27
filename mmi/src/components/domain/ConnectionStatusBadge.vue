<script setup lang="ts">
// Badge de estado de conexión WS al gateway -- mismo `wsStatusVariant`
// duplicado antes en ControlCenterView.vue y SystemStatusView.vue.
import { computed } from 'vue'
import { Badge } from '@/components/ui/badge'

const props = withDefaults(
  defineProps<{
    status: string
    label?: string
  }>(),
  { label: 'WS' },
)

const variant = computed(() => {
  if (props.status === 'OPEN') return 'default'
  if (props.status === 'CONNECTING') return 'secondary'
  return 'destructive'
})
</script>

<template>
  <Badge :variant="variant">{{ label }} {{ status }}</Badge>
</template>
