<script setup lang="ts">
defineProps<{
  saved: boolean
}>()

const emit = defineEmits<{
  (e: 'save'): void
}>()
</script>

<template>
  <div
    v-if="!saved"
    class="flex items-center justify-between rounded-md bg-amber-50 p-4 border border-amber-200 text-amber-800 dark:bg-amber-950/40 dark:border-amber-800 dark:text-amber-200"
  >
    <div class="flex items-center space-x-3">
      <span class="font-bold text-xs uppercase px-2 py-0.5 rounded bg-amber-200 dark:bg-amber-800 text-amber-900 dark:text-amber-100">
        RESULTADO VOLÁTIL
      </span>
      <span class="text-sm">
        Los nuevos parámetros de calibración han sido obtenidos pero aún no están guardados en la memoria persistente.
      </span>
    </div>
    <button
      type="button"
      class="rounded bg-amber-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-amber-700 shadow-sm"
      @click="emit('save')"
    >
      Guardar Parámetros
    </button>
  </div>
  <div
    v-else
    class="flex items-center space-x-3 rounded-md bg-emerald-50 p-4 border border-emerald-200 text-emerald-800 dark:bg-emerald-950/40 dark:border-emerald-800 dark:text-emerald-200"
  >
    <span class="font-bold text-xs uppercase px-2 py-0.5 rounded bg-emerald-200 dark:bg-emerald-800 text-emerald-900 dark:text-emerald-100">
      GUARDADO
    </span>
    <span class="text-sm">
      Parámetros de calibración persistidos correctamente en el sistema.
    </span>
  </div>
</template>
