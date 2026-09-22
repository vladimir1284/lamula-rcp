<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  open: boolean
  title: string
  prompt: string
  inputLabel?: string
  defaultValue?: number
}>()

const emit = defineEmits<{
  (e: 'confirm', value: number | null): void
  (e: 'cancel'): void
}>()

const inputValue = ref<number | null>(props.defaultValue ?? null)

watch(
  () => props.defaultValue,
  (val) => {
    inputValue.value = val ?? null
  }
)

function handleConfirm() {
  emit('confirm', inputValue.value)
}

function handleCancel() {
  emit('cancel')
}
</script>

<template>
  <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
    <div class="w-full max-w-md rounded-lg bg-white p-6 shadow-xl dark:bg-slate-800 dark:text-white">
      <h3 class="text-lg font-bold text-slate-900 dark:text-slate-100 mb-2">
        {{ title }}
      </h3>
      <p class="text-sm text-slate-600 dark:text-slate-300 mb-4">
        {{ prompt }}
      </p>

      <div v-if="inputLabel" class="mb-4">
        <label class="block text-xs font-semibold uppercase text-slate-500 dark:text-slate-400 mb-1">
          {{ inputLabel }}
        </label>
        <input
          v-model.number="inputValue"
          type="number"
          step="any"
          class="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-white"
        />
      </div>

      <div class="flex justify-end space-x-3">
        <button
          type="button"
          class="rounded px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-700"
          @click="handleCancel"
        >
          Cancelar
        </button>
        <button
          type="button"
          class="rounded bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
          @click="handleConfirm"
        >
          Confirmar
        </button>
      </div>
    </div>
  </div>
</template>
