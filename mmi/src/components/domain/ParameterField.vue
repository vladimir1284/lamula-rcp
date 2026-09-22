<script setup lang="ts">
import { computed } from 'vue'
import { Input } from '@/components/ui/input'

const props = withDefaults(
  defineProps<{
    label: string
    modelValue: number | string
    unit?: string
    accepted?: boolean
    readOnlyValue?: number | string | null
    step?: number | string
    min?: number
    max?: number
    disabled?: boolean
    helpText?: string
  }>(),
  {
    unit: '',
    accepted: false,
    readOnlyValue: null,
    step: 'any',
    disabled: false,
    helpText: '',
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: number | string]
}>()

function onInput(val: string | number) {
  if (typeof props.modelValue === 'number') {
    const num = Number(val)
    emit('update:modelValue', isNaN(num) ? val : num)
  } else {
    emit('update:modelValue', val)
  }
}

const displayReadValue = computed(() => {
  if (props.readOnlyValue === null || props.readOnlyValue === undefined) return '—'
  if (typeof props.readOnlyValue === 'number') return props.readOnlyValue.toFixed(1)
  return String(props.readOnlyValue)
})
</script>

<template>
  <div
    class="flex flex-col gap-1.5 rounded-md border p-2.5 transition-colors"
    :class="
      accepted
        ? 'border-emerald-500/60 bg-emerald-500/10 text-emerald-950 dark:text-emerald-100'
        : 'border-border bg-card text-card-foreground'
    "
  >
    <div class="flex items-center justify-between gap-2">
      <span class="text-xs font-semibold tracking-tight">
        {{ label }}
        <span v-if="unit" class="text-[11px] font-normal text-muted-foreground">({{ unit }})</span>
      </span>
      <span
        v-if="accepted"
        class="inline-flex items-center gap-1 rounded-full bg-emerald-600/20 px-2 py-0.5 text-[10px] font-medium text-emerald-600 dark:text-emerald-400"
      >
        <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
        </svg>
        Aceptado
      </span>
    </div>

    <div class="flex items-center gap-2">
      <Input
        :type="typeof modelValue === 'number' ? 'number' : 'text'"
        :step="step"
        :min="min"
        :max="max"
        :disabled="disabled"
        :model-value="modelValue"
        class="h-8 text-xs font-mono"
        :class="accepted ? 'border-emerald-500/80 focus-visible:ring-emerald-500' : ''"
        @update:model-value="onInput"
      />
    </div>

    <div class="flex items-center justify-between text-[11px] text-muted-foreground">
      <span v-if="readOnlyValue !== null && readOnlyValue !== undefined">
        Leído: <strong class="font-mono text-foreground">{{ displayReadValue }}</strong>
        <span v-if="unit"> {{ unit }}</span>
      </span>
      <span v-else class="text-[10px] italic">Sin lectura HAL</span>

      <span v-if="helpText" class="text-[10px] text-muted-foreground">{{ helpText }}</span>
    </div>
  </div>
</template>
