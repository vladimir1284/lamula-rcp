<script setup lang="ts">
import { Button } from '@/components/ui/button'

const props = defineProps<{
  channels: string[]
  selected: string[]
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:selected', value: string[]): void
}>()

function toggleChannel(ch: string) {
  if (props.disabled) return
  if (props.selected.includes(ch)) {
    emit(
      'update:selected',
      props.selected.filter((c) => c !== ch),
    )
  } else {
    emit('update:selected', [...props.selected, ch])
  }
}

function selectAll() {
  if (props.disabled) return
  emit('update:selected', [...props.channels])
}

function deselectAll() {
  if (props.disabled) return
  emit('update:selected', [])
}
</script>

<template>
  <div class="flex flex-col gap-2 rounded-md border p-3 bg-card">
    <div class="flex items-center justify-between">
      <span class="text-xs font-semibold text-foreground">Canales AI Disponibles</span>
      <div class="flex items-center gap-1.5">
        <Button variant="ghost" size="xs" :disabled="disabled" @click="selectAll">
          Todos
        </Button>
        <Button variant="ghost" size="xs" :disabled="disabled" @click="deselectAll">
          Ninguno
        </Button>
      </div>
    </div>
    <div class="grid grid-cols-1 gap-1.5 sm:grid-cols-2 md:grid-cols-3 text-xs">
      <label
        v-for="ch in channels"
        :key="ch"
        class="flex items-center gap-2 cursor-pointer select-none rounded p-1 hover:bg-accent/50"
        :class="{ 'opacity-50 cursor-not-allowed': disabled }"
      >
        <input
          type="checkbox"
          :checked="selected.includes(ch)"
          :disabled="disabled"
          class="rounded border-muted-foreground/30 accent-primary"
          @change="toggleChannel(ch)"
        />
        <span class="font-mono text-muted-foreground truncate">{{ ch }}</span>
      </label>
    </div>
  </div>
</template>
