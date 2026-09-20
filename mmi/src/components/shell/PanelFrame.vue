<script setup lang="ts">
// Encabezado común de panel (I6 Export / Snapshot integrado como acción
// de cabecera estándar de panel, disponible en todas las vistas de forma
// predeterminada).
//
// `frozen` cubre "cada uno se congela independientemente" (varios
// ASCOPE/PPI/RHI a la vez, docs/diseno/inventario-ui.md, Requisitos de
// concurrencia). Cuando `viewId` no está entre `viewOptions` (o su opción
// tiene `available:false`) se pinta el hueco "vista no aplicable" en vez del
// contenido.
import { computed, ref } from 'vue'
import { Button } from '@/components/ui/button'
import ExportMenu from '@/components/domain/ExportMenu.vue'
import { useInjectPanelExportData } from '@/composables/usePanelExport'
import type { ViewOption } from '@/types/shell'

const props = withDefaults(
  defineProps<{
    viewId: string | null
    viewOptions: ViewOption[]
    frozen?: boolean
    closable?: boolean
    exportData?: unknown
  }>(),
  { frozen: false, closable: false, exportData: undefined },
)

defineEmits<{
  'update:viewId': [value: string]
  'toggle-freeze': []
  close: []
}>()

const selected = computed(() => props.viewOptions.find((v) => v.id === props.viewId))
const isApplicable = computed(() => !!selected.value?.available)
const panelContentRef = ref<HTMLDivElement | null>(null)

const injectedData = useInjectPanelExportData()

const activeExportData = computed(() => {
  if (props.exportData !== undefined) return props.exportData
  if (injectedData !== undefined) return injectedData
  return {
    panelId: props.viewId,
    title: selected.value?.label ?? 'Panel',
    timestamp: new Date().toISOString(),
  }
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col overflow-hidden rounded-md border border-border">
    <div class="flex items-center gap-1.5 border-b border-border bg-card px-2 py-1">
      <select
        class="min-w-0 flex-1 rounded-sm border border-border bg-background px-1.5 py-1 text-xs"
        :value="viewId ?? ''"
        @change="$emit('update:viewId', ($event.target as HTMLSelectElement).value)"
      >
        <option v-for="opt in viewOptions" :key="opt.id" :value="opt.id" :disabled="!opt.available">
          {{ opt.label }}{{ opt.available ? '' : ' (no aplicable)' }}
        </option>
      </select>
      <ExportMenu
        :target-el="panelContentRef"
        :filename="viewId ?? 'panel'"
        :export-data="activeExportData"
        size="icon-xs"
        variant="ghost"
        title="Exportar / Snapshot del panel"
      />
      <Button
        size="icon-xs"
        variant="ghost"
        :aria-pressed="frozen"
        :class="frozen ? 'text-state-simulated' : ''"
        title="Congelar panel"
        @click="$emit('toggle-freeze')"
      >
        ❄
      </Button>
      <Button v-if="closable" size="icon-xs" variant="ghost" title="Cerrar panel" @click="$emit('close')">
        ✕
      </Button>
    </div>
    <div ref="panelContentRef" class="min-h-0 flex-1 overflow-auto p-2" data-panel-frame>
      <div v-if="!isApplicable" class="flex h-full items-center justify-center text-xs text-muted-foreground">
        Vista no aplicable en este preset
      </div>
      <slot v-else />
    </div>
  </div>
</template>
