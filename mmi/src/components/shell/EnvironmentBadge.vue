<script setup lang="ts">
// Requisito transversal #1: `simulated` (HAL = radar_emulator) tiene que ser
// evidente en pantalla, no un detalle de configuración -- por eso este badge
// no se oculta en un menú, vive en la barra global (A1) y no renderiza nada
// cuando es falso: lo normal (HAL real) no necesita aviso.
defineProps<{
  simulated: boolean
}>()
</script>

<template>
  <span
    v-if="simulated"
    class="inline-flex items-center gap-1 rounded-md bg-state-simulated px-1.5 py-0.5 text-xs font-medium text-white"
  >
    SIM
  </span>
</template>
