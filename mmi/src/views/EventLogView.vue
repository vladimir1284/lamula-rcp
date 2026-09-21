<script setup lang="ts">
// A5 Event Log (docs/diseno/inventario-ui.md) -- distinto de B8 (BiteMessagesView):
// aquí van las acciones del propio MMI y del RCP (OperatorEventMessage sobre
// el WS, `type: 'event'`), no los mensajes de test del radar.
//
// El backend no adjunta severidad a OperatorEventMessage (sólo kind/actor/
// payload) -- `severityOf` es una heurística sobre el nombre del kind, no un
// campo real. Documentado en vez de fabricar un campo que no existe.
//
// Sin control de autoscroll: el propio inventario pide "más reciente
// arriba", así que los eventos nuevos no empujan la vista hacia abajo -- no
// hay nada que pausar. Si el orden se invierte más adelante, este es el
// lugar para añadirlo.
import { computed, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useGateway } from '@/composables/useGateway'
import { providePanelExportData } from '@/composables/usePanelExport'
import { copyToClipboard, exportToJson } from '@/lib/exportUtils'
import type { OperatorEventMessage } from '@/types/mmi'

const { messages } = useGateway()

type Severity = 'info' | 'warn' | 'error'

function severityOf(kind: string): Severity {
  const k = kind.toLowerCase()
  if (k.includes('fail') || k.includes('error') || k.includes('denied') || k.includes('denegad')) return 'error'
  if (k.includes('warn') || k.includes('cancel')) return 'warn'
  return 'info'
}

const SEVERITY_VARIANT: Record<Severity, 'default' | 'secondary' | 'destructive'> = {
  info: 'secondary',
  warn: 'default',
  error: 'destructive',
}

// Un panel congelado (PanelFrame) puede mostrar Event Log más de una vez a
// la vez -- cada instancia lleva su propio punto de corte de "limpiar" y su
// propio autoscroll, igual que cada panel se congela independientemente
// (ver AppShell, paso 2).
const clearedBeforeSeq = ref(0)
const search = ref('')
const severityFilter = ref<Set<Severity>>(new Set(['info', 'warn', 'error']))

function toggleSeverity(s: Severity) {
  const next = new Set(severityFilter.value)
  if (next.has(s)) next.delete(s)
  else next.add(s)
  severityFilter.value = next
}

const events = computed<(OperatorEventMessage & { severity: Severity })[]>(() =>
  messages.value
    .filter((m): m is OperatorEventMessage => m.type === 'event')
    .filter((m) => m.seq > clearedBeforeSeq.value)
    .map((m) => ({ ...m, severity: severityOf(m.kind) }))
    .filter((m) => severityFilter.value.has(m.severity))
    .filter((m) => !search.value || `${m.kind} ${m.actor}`.toLowerCase().includes(search.value.toLowerCase()))
    .reverse(),
)

providePanelExportData(() => events.value)

function clear() {
  const last = messages.value.filter((m) => m.type === 'event').at(-1)
  clearedBeforeSeq.value = last?.type === 'event' ? last.seq : clearedBeforeSeq.value
}

async function copyAll() {
  const text = events.value
    .map((e) => `${e.at_wall}\t${e.severity}\t${e.kind}\t${e.actor}\t${JSON.stringify(e.payload)}`)
    .join('\n')
  await copyToClipboard(text)
}

function exportAll() {
  exportToJson(events.value, `event-log-${new Date().toISOString()}`)
}
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-2">
    <div class="flex flex-wrap items-center gap-2">
      <Button
        v-for="s in (['info', 'warn', 'error'] as const)"
        :key="s"
        size="sm"
        :variant="severityFilter.has(s) ? SEVERITY_VARIANT[s] : 'outline'"
        @click="toggleSeverity(s)"
      >
        {{ s }}
      </Button>
      <Input v-model="search" placeholder="buscar..." class="h-8 w-40 text-xs" />
      <div class="ml-auto flex gap-1">
        <Button size="sm" variant="outline" @click="copyAll">Copiar</Button>
        <Button size="sm" variant="outline" @click="exportAll">Exportar</Button>
        <Button size="sm" variant="outline" @click="clear">Limpiar</Button>
      </div>
    </div>

    <p v-if="events.length === 0" class="text-sm text-muted-foreground">Sin eventos.</p>
    <ScrollArea v-else class="min-h-0 flex-1">
      <ul class="flex flex-col gap-1 text-xs">
        <li v-for="e in events" :key="e.seq" class="flex flex-wrap items-center gap-2 border-b border-border pb-1">
          <Badge :variant="SEVERITY_VARIANT[e.severity]" class="shrink-0">{{ e.severity }}</Badge>
          <span class="text-muted-foreground">{{ new Date(e.at_wall).toLocaleTimeString() }}</span>
          <span class="font-medium">{{ e.kind }}</span>
          <span class="text-muted-foreground">{{ e.actor }}</span>
        </li>
      </ul>
    </ScrollArea>
  </div>
</template>
