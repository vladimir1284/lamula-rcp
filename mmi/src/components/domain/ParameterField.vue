<script setup lang="ts">
import { computed } from 'vue'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'

const props = withDefaults(
  defineProps<{
    label: string
    modelValue: number | null
    readout: number | null
    unit?: string
    accepted: boolean
    disabled?: boolean
    readonly?: boolean
    step?: number | string
    min?: number | string
    max?: number | string
  }>(),
  {
    unit: '',
    disabled: false,
    readonly: false,
    step: 'any',
    min: undefined,
    max: undefined,
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: number | null]
}>()

function onInput(ev: Event) {
  const target = ev.target as HTMLInputElement
  if (target.value === '') {
    emit('update:modelValue', null)
  } else {
    const num = parseFloat(target.value)
    emit('update:modelValue', isNaN(num) ? null : num)
  }
}

const formattedReadout = computed(() => {
  if (props.readout === null || props.readout === undefined) {
    return '—'
  }
  return typeof props.readout === 'number' ? props.readout.toFixed(2) : String(props.readout)
})
</script>

<template>
  <div class="flex flex-col gap-1.5 rounded-md border border-border/60 bg-card/40 p-2.5 shadow-xs">
    <div class="flex items-center justify-between gap-2">
      <span class="text-xs font-medium text-foreground">
        {{ label }}
        <span v-if="unit" class="text-[11px] text-muted-foreground">[{{ unit }}]</span>
      </span>
      <Badge
        :variant="accepted ? 'default' : 'secondary'"
        class="text-[10px] uppercase font-semibold transition-colors"
        :class="
          accepted
            ? 'bg-emerald-600/20 text-emerald-400 border-emerald-500/40 hover:bg-emerald-600/30'
            : 'bg-muted/80 text-muted-foreground border-border'
        "
      >
        {{ accepted ? 'Aceptado' : 'Pendiente' }}
      </Badge>
    </div>

    <div class="grid grid-cols-2 gap-2 text-xs">
      <div class="flex flex-col gap-1">
        <label class="text-[10px] text-muted-foreground">Comandado</label>
        <Input
          :value="modelValue ?? ''"
          type="number"
          :step="step"
          :min="min"
          :max="max"
          :disabled="disabled || readonly"
          class="h-8 text-xs font-mono"
          @input="onInput"
        />
      </div>

      <div class="flex flex-col gap-1">
        <label class="text-[10px] text-muted-foreground">Leído (HAL)</label>
        <div
          class="flex h-8 items-center rounded-md border border-input/50 bg-muted/40 px-3 font-mono text-xs font-medium"
          :class="accepted ? 'text-emerald-400 font-semibold' : 'text-foreground'"
        >
          {{ formattedReadout }}
          <span v-if="unit && readout !== null" class="ml-1 text-[10px] text-muted-foreground font-sans">
            {{ unit }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
