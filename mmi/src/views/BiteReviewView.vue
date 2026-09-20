<script setup lang="ts">
// B9 BiTE Review (docs/diseno/inventario-ui.md):
// 100% frontend, sin backend -- carga un JSON de historial previamente guardado
// desde B8 (Guardar lista) y lo renderiza en BiteMessageTable como snapshot estático,
// acompañado del HistoricalModeBanner obligatorio.
//
// Gap real: sin persistencia server-side — el archivo vive en el disco del
// operador. Histórico centralizado en el RCP es backend nuevo, fuera de este paso.
import { computed, ref } from 'vue'
import { Button } from '@/components/ui/button'
import BiteMessageTable from '@/components/domain/BiteMessageTable.vue'
import HistoricalModeBanner from '@/components/domain/HistoricalModeBanner.vue'
import type { BiteEventMessage } from '@/types/mmi'

const props = defineProps<{
  initialRows?: BiteEventMessage[]
  initialFileName?: string
}>()

const loadedRows = ref<BiteEventMessage[]>(props.initialRows ?? [])
const fileName = ref<string | null>(props.initialFileName ?? null)
const parseError = ref<string | null>(null)
const showResolved = ref(true)

const filteredRows = computed(() =>
  loadedRows.value
    .filter((m) => showResolved.value || m.transition === 'fault')
    .sort((a, b) => b.at_wall.localeCompare(a.at_wall)),
)

function handleFileUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  fileName.value = file.name
  parseError.value = null

  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const text = e.target?.result as string
      const parsed = JSON.parse(text)
      if (Array.isArray(parsed)) {
        loadedRows.value = parsed as BiteEventMessage[]
      } else {
        parseError.value = 'El archivo debe contener un arreglo de mensajes BiTE'
      }
    } catch {
      parseError.value = 'Error al decodificar el archivo JSON'
    }
  }
  reader.readAsText(file)
}

function clearLoaded() {
  loadedRows.value = []
  fileName.value = null
  parseError.value = null
}
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-3 p-3">
    <div class="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-2">
      <div class="flex items-center gap-2">
        <h2 class="font-semibold text-base">Revisión BiTE Histórico (B9)</h2>
        <span class="text-xs text-muted-foreground">Informe estático en disco</span>
      </div>

      <div class="flex items-center gap-2">
        <label class="cursor-pointer">
          <Button size="sm" variant="outline" as-child>
            <span>Cargar archivo JSON</span>
          </Button>
          <input type="file" accept=".json" class="hidden" @change="handleFileUpload" />
        </label>
        <Button v-if="fileName" size="sm" variant="ghost" @click="clearLoaded">
          Limpiar
        </Button>
      </div>
    </div>

    <HistoricalModeBanner v-if="fileName || loadedRows.length > 0" :file-name="fileName ?? 'Cargado de memoria'" :total-records="loadedRows.length" />

    <p v-if="parseError" class="text-xs font-medium text-destructive">
      {{ parseError }}
    </p>

    <div v-if="loadedRows.length > 0" class="flex items-center justify-between">
      <span class="text-xs text-muted-foreground">
        Mostrando {{ filteredRows.length }} de {{ loadedRows.length }} evento(s)
      </span>
      <Button size="sm" :variant="showResolved ? 'default' : 'outline'" @click="showResolved = !showResolved">
        {{ showResolved ? 'Ocultar resueltas' : 'Mostrar resueltas' }}
      </Button>
    </div>

    <BiteMessageTable v-if="loadedRows.length > 0" :rows="filteredRows" />

    <div v-else-if="!parseError" class="flex flex-1 flex-col items-center justify-center gap-2 text-center text-muted-foreground">
      <p class="text-sm">No hay ningún reporte histórico cargado.</p>
      <p class="text-xs">Seleccione un archivo JSON previamente exportado desde B8 (BiTE Messages) para analizarlo.</p>
    </div>
  </div>
</template>
