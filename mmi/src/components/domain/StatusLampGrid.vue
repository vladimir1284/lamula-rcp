<script setup lang="ts">
// B2 Subsystem Detail: grilla densa de StatusLampRow, "denso" per inventario.
import StatusLampRow from './StatusLampRow.vue'

defineProps<{
  items: {
    signalId: string
    label: string
    fault: boolean
    stale: boolean
    detail?: string
  }[]
}>()
</script>

<template>
  <div class="grid grid-cols-1 gap-x-4 sm:grid-cols-2">
    <StatusLampRow
      v-for="item in items"
      :key="item.signalId"
      :signal-id="item.signalId"
      :label="item.label"
      :fault="item.fault"
      :stale="item.stale"
      :detail="item.detail"
    />
  </div>
</template>
