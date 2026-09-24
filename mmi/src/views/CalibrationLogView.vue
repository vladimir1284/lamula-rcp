<script setup lang="ts">
// G8 Calibration Log (docs/diseno/inventario-ui.md)
// Registro de cada actividad individual de calibración (RAVIS §7.4).
//
// Reutiliza patrones de A5 (EventLogView), incluyendo LogStream y LogToolbar.
// Obtiene el registro de calibración en tiempo real desde el gateway vía fetchCalibrationLog().

import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useGateway } from '@/composables/useGateway'
import type { CalibrationLogEntry } from '@/types/mmi'

const props = defineProps<{
  entries?: CalibrationLogEntry[]
}>()

const { fetchCalibrationLog } = useGateway()

const fetchedEntries = ref<CalibrationLogEntry[]>([])
const error = ref<string | null>(null)
let pollTimer: ReturnType<typeof setInterval> | null = null

async function refresh() {
  try {
    fetchedEntries.value = await fetchCalibrationLog()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

const entries = computed(() => props.entries ?? fetchedEntries.value)

type Severity = 'info' | 'warn' | 'error'

const SEVERITY_VARIANT: Record<Severity, 'default' | 'secondary' | 'destructive'> = {
  info: 'secondary',
  warn: 'default',
  error: 'destructive',
}

const clearedIndex = ref(0)
const search = ref('')
const selectedProcedure = ref<string>('all')
const severityFilter = ref<Set<Severity>>(new Set(['info', 'warn', 'error']))

function toggleSeverity(s: Severity) {
  const next = new Set(severityFilter.value)
  if (next.has(s)) next.delete(s)
  else next.add(s)
  severityFilter.value = next
}

const availableProcedures = computed(() => {
  const set = new Set<string>()
  entries.value.forEach((e) => set.add(e.procedure))
  return Array.from(set)
})

const filteredEntries = computed(() =>
  entries.value
    .slice(clearedIndex.value)
    .filter((e) => severityFilter.value.has(e.severity))
    .filter((e) => selectedProcedure.value === 'all' || e.procedure === selectedProcedure.value)
    .filter(
      (e) =>
        !search.value ||
        `${e.procedure} ${e.actor} ${e.message} ${e.detail ?? ''}`
          .toLowerCase()
          .includes(search.value.toLowerCase()),
    )
    .reverse(),
)

function clear() {
  clearedIndex.value = entries.value.length
}

async function copyAll() {
  const text = filteredEntries.value
    .map((e) => `${e.at_wall}\t${e.severity}\t${e.procedure}\t${e.actor}\t${e.message}\t${e.detail ?? ''}`)
    .join('\n')
  await navigator.clipboard.writeText(text)
}

function exportAll() {
  const text = filteredEntries.value
    .map((e) => `${e.at_wall}\t${e.severity}\t${e.procedure}\t${e.actor}\t${e.message}\t${e.detail ?? ''}`)
    .join('\n')
  const blob = new Blob([text], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `calibration-log-${new Date().toISOString()}.tsv`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  if (props.entries === undefined) {
    refresh()
    pollTimer = setInterval(refresh, 2000)
  }
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-2 p-2">
    <!-- LogToolbar -->
    <div class="flex flex-wrap items-center gap-2">
      <div class="flex items-center gap-1">
        <Button
          v-for="s in (['info', 'warn', 'error'] as const)"
          :key="s"
          size="sm"
          :variant="severityFilter.has(s) ? SEVERITY_VARIANT[s] : 'outline'"
          @click="toggleSeverity(s)"
        >
          {{ s }}
        </Button>
      </div>

      <select
        v-model="selectedProcedure"
        class="h-8 rounded-md border border-input bg-background px-2 text-xs ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
      >
        <option value="all">Todas las rutinas</option>
        <option v-for="proc in availableProcedures" :key="proc" :value="proc">
          {{ proc }}
        </option>
      </select>

      <Input v-model="search" placeholder="Buscar en log..." class="h-8 w-44 text-xs" />

      <div class="ml-auto flex gap-1">
        <Button size="sm" variant="outline" @click="copyAll">Copiar</Button>
        <Button size="sm" variant="outline" @click="exportAll">Exportar</Button>
        <Button size="sm" variant="outline" @click="clear">Limpiar</Button>
      </div>
    </div>

    <!-- LogStream -->
    <p v-if="filteredEntries.length === 0" class="text-sm text-muted-foreground">
      Sin entradas en el registro de calibración.
    </p>
    <ScrollArea v-else class="min-h-0 flex-1">
      <ul class="flex flex-col gap-1.5 text-xs">
        <li
          v-for="(e, idx) in filteredEntries"
          :key="idx"
          class="flex flex-col gap-0.5 border-b border-border pb-1.5"
        >
          <div class="flex flex-wrap items-center gap-2">
            <Badge :variant="SEVERITY_VARIANT[e.severity]" class="shrink-0">{{ e.severity }}</Badge>
            <span class="text-muted-foreground">{{ new Date(e.at_wall).toLocaleTimeString() }}</span>
            <span class="font-medium text-foreground">{{ e.procedure }}</span>
            <span class="text-muted-foreground">({{ e.actor }})</span>
          </div>
          <p class="font-medium text-foreground/90 pl-1">{{ e.message }}</p>
          <p v-if="e.detail" class="text-muted-foreground pl-1 font-mono text-[11px]">{{ e.detail }}</p>
        </li>
      </ul>
    </ScrollArea>
  </div>
</template>
