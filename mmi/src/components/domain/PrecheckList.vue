<script setup lang="ts">
// C4: "botón de ejecución deshabilitado con la causa visible si alguna
// precondición falla" -- una lista, no sólo un botón gris. Antes de esto,
// JobActionPanel sólo exponía `runDisabled` como booleano opaco; esta lista
// es lo que hace visible el *por qué*.
export interface Precheck {
  label: string
  ok: boolean
}

defineProps<{
  checks: Precheck[]
}>()
</script>

<template>
  <ul class="flex flex-col gap-0.5 text-xs">
    <li v-for="c in checks" :key="c.label" class="flex items-center gap-1.5">
      <span :class="c.ok ? 'text-state-ok' : 'text-state-fault'">{{ c.ok ? '✓' : '✗' }}</span>
      <span :class="c.ok ? 'text-muted-foreground' : 'text-foreground'">{{ c.label }}</span>
    </li>
  </ul>
</template>
