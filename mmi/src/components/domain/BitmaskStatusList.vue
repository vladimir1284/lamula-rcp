<script setup lang="ts">
import { computed } from 'vue'
import { Badge } from '@/components/ui/badge'

export interface BitmaskBitDef {
  bit: number // bitmask value (e.g. 1, 2, 4...) or bit index (0..31)
  label: string
  description?: string
  severity?: 'ok' | 'info' | 'warn' | 'fault'
}

const props = withDefaults(
  defineProps<{
    value: number
    bits: BitmaskBitDef[]
    emptyText?: string
  }>(),
  { emptyText: 'Sin condiciones activas' },
)

function isBitSet(mask: number, b: number): boolean {
  if (b === 0) return false
  // Check both bit index (e.g. 0..31) or bitmask (1, 2, 4, 8...)
  if ((b & (b - 1)) === 0 && b > 0) {
    return (mask & b) !== 0
  }
  return (mask & (1 << b)) !== 0
}

const activeBits = computed(() =>
  props.bits.filter((def) => isBitSet(props.value, def.bit)),
)

function variantForSeverity(sev?: 'ok' | 'info' | 'warn' | 'fault') {
  switch (sev) {
    case 'fault':
      return 'destructive'
    case 'warn':
      return 'secondary'
    case 'info':
      return 'outline'
    default:
      return 'default'
  }
}
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <div v-if="activeBits.length === 0" class="text-xs text-muted-foreground">
      {{ emptyText }}
    </div>
    <div v-else class="flex flex-wrap gap-1.5">
      <div
        v-for="item in activeBits"
        :key="item.bit"
        class="inline-flex items-center gap-1.5 text-xs"
      >
        <Badge :variant="variantForSeverity(item.severity)">
          {{ item.label }}
        </Badge>
        <span v-if="item.description" class="text-muted-foreground">
          ({{ item.description }})
        </span>
      </div>
    </div>
  </div>
</template>
