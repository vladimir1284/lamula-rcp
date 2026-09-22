<script setup lang="ts">
import { Badge } from '@/components/ui/badge'

export type TernaryOption = 'never' | 'user' | 'always'

const props = withDefaults(
  defineProps<{
    modelValue: TernaryOption
    label: string
    description?: string
    disabled?: boolean
    supported?: boolean
  }>(),
  {
    disabled: false,
    supported: true,
  }
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: TernaryOption): void
}>()

const options: { value: TernaryOption; label: string }[] = [
  { value: 'never', label: 'Never' },
  { value: 'user', label: 'User' },
  { value: 'always', label: 'Always' },
]

function select(val: TernaryOption) {
  if (props.disabled) return
  emit('update:modelValue', val)
}
</script>

<template>
  <div class="flex items-center justify-between gap-4 py-2 border-b border-border/40 last:border-0">
    <div class="space-y-0.5">
      <div class="flex items-center gap-2">
        <span class="text-xs font-medium text-foreground">{{ label }}</span>
        <Badge
          v-if="supported === false"
          variant="outline"
          class="border-amber-500/50 bg-amber-500/10 text-amber-500 text-[9px] px-1.5 py-0 font-mono"
        >
          Sin backend
        </Badge>
      </div>
      <p v-if="description" class="text-[11px] text-muted-foreground">
        {{ description }}
      </p>
    </div>

    <div class="flex items-center rounded-md border border-border/80 bg-muted/40 p-0.5">
      <button
        v-for="opt in options"
        :key="opt.value"
        type="button"
        :disabled="disabled"
        class="px-2.5 py-1 text-[11px] font-medium transition-all rounded"
        :class="[
          modelValue === opt.value
            ? 'bg-background text-foreground shadow-xs'
            : 'text-muted-foreground hover:text-foreground',
          disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
        ]"
        @click="select(opt.value)"
      >
        {{ opt.label }}
      </button>
    </div>
  </div>
</template>
