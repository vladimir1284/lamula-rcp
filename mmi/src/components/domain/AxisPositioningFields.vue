<script setup lang="ts">
// Grupo de 4 campos de posicionamiento de eje (gain_v_per_deg, max_voltage,
// tolerance_deg, timeout_s) -- antes duplicado en el panel Posicionar de
// AntennaControlView.vue y dos veces (az/el) en el panel Ejecutar de
// ScanWorksheetView.vue. Mismo shape que AxisPositioningParams
// (core/contracts/scan.py) -- por eso el prop usa ese tipo directo, no uno
// nuevo. Ninguno lleva default: sin valores confirmados todavía
// (PEND-RCP-07/09), el operador tiene que traerlos.
import { Input } from '@/components/ui/input'
import type { AxisPositioningParams } from '@/types/scan'

export type PartialAxisPositioningParams = {
  [K in keyof AxisPositioningParams]: AxisPositioningParams[K] | undefined
}

withDefaults(
  defineProps<{
    modelValue: PartialAxisPositioningParams
    axisLabel?: string | null
  }>(),
  { axisLabel: null },
)

defineEmits<{
  'update:modelValue': [value: PartialAxisPositioningParams]
}>()

function update<K extends keyof AxisPositioningParams>(
  modelValue: PartialAxisPositioningParams,
  key: K,
  raw: string | number,
) {
  const value = raw === '' ? undefined : Number(raw)
  return { ...modelValue, [key]: value }
}
</script>

<template>
  <div class="flex flex-col gap-2">
    <span v-if="axisLabel" class="text-xs font-medium text-muted-foreground">{{ axisLabel }}</span>
    <label class="flex flex-col gap-1 text-xs">
      gain_v_per_deg
      <Input
        type="number"
        step="0.01"
        :model-value="modelValue.gain_v_per_deg"
        @update:model-value="$emit('update:modelValue', update(modelValue, 'gain_v_per_deg', $event))"
      />
    </label>
    <label class="flex flex-col gap-1 text-xs">
      max_voltage
      <Input
        type="number"
        step="0.1"
        :model-value="modelValue.max_voltage"
        @update:model-value="$emit('update:modelValue', update(modelValue, 'max_voltage', $event))"
      />
    </label>
    <label class="flex flex-col gap-1 text-xs">
      tolerance_deg
      <Input
        type="number"
        step="0.1"
        :model-value="modelValue.tolerance_deg"
        @update:model-value="$emit('update:modelValue', update(modelValue, 'tolerance_deg', $event))"
      />
    </label>
    <label class="flex flex-col gap-1 text-xs">
      timeout_s
      <Input
        type="number"
        step="1"
        :model-value="modelValue.timeout_s"
        @update:model-value="$emit('update:modelValue', update(modelValue, 'timeout_s', $event))"
      />
    </label>
  </div>
</template>
