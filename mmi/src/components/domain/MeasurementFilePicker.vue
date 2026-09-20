<script setup lang="ts">
import { ref } from 'vue'
import { Button } from '@/components/ui/button'
import { parseJsonFile } from '@/lib/exportUtils'

withDefaults(
  defineProps<{
    loadedFileName?: string | null
    totalRecords?: number
    accept?: string
    disabled?: boolean
    canSave?: boolean
    saveLabel?: string
    loadLabel?: string
  }>(),
  {
    loadedFileName: null,
    totalRecords: 0,
    accept: '.json,.csv',
    disabled: false,
    canSave: true,
    saveLabel: 'Guardar conjunto',
    loadLabel: 'Cargar archivo',
  },
)

const emit = defineEmits<{
  load: [payload: { data: unknown; fileName: string; fileType: 'json' | 'csv' }]
  save: []
  clear: []
  error: [message: string]
}>()

const parseError = ref<string | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)

function triggerFileSelect() {
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
    fileInputRef.value.click()
  }
}

async function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  parseError.value = null

  if (file.name.endsWith('.json')) {
    const result = await parseJsonFile<unknown>(file)
    if (result.error || result.data === null) {
      parseError.value = result.error || 'Error al procesar JSON'
      emit('error', parseError.value)
    } else {
      emit('load', { data: result.data, fileName: result.fileName, fileType: 'json' })
    }
  } else if (file.name.endsWith('.csv')) {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string
        const lines = text.split(/\r?\n/).filter((l) => l.trim() !== '')
        if (lines.length === 0) {
          parseError.value = 'El archivo CSV está vacío'
          emit('error', parseError.value)
          return
        }
        const headers = lines[0]!.split(',').map((h) => h.trim().replace(/^"|"$/g, ''))
        const records = lines.slice(1).map((line) => {
          const cells = line.split(',').map((c) => c.trim().replace(/^"|"$/g, ''))
          const obj: Record<string, string> = {}
          headers.forEach((h, idx) => {
            obj[h] = cells[idx] ?? ''
          })
          return obj
        })
        emit('load', { data: records, fileName: file.name, fileType: 'csv' })
      } catch {
        parseError.value = 'Error al decodificar el archivo CSV'
        emit('error', parseError.value)
      }
    }
    reader.readAsText(file)
  } else {
    parseError.value = 'Formato no soportado (sólo .json o .csv)'
    emit('error', parseError.value)
  }
}

function handleClear() {
  parseError.value = null
  emit('clear')
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-2 rounded-md border border-border bg-card p-2 text-xs">
    <div class="flex items-center gap-1.5">
      <Button
        size="sm"
        variant="outline"
        :disabled="disabled"
        @click="triggerFileSelect"
      >
        📂 {{ loadLabel }}
      </Button>
      <input
        ref="fileInputRef"
        type="file"
        :accept="accept"
        class="hidden"
        @change="handleFileChange"
      />

      <Button
        v-if="canSave"
        size="sm"
        variant="outline"
        :disabled="disabled"
        @click="$emit('save')"
      >
        💾 {{ saveLabel }}
      </Button>

      <Button
        v-if="loadedFileName"
        size="sm"
        variant="ghost"
        :disabled="disabled"
        @click="handleClear"
      >
        ✕ Limpiar
      </Button>
    </div>

    <div v-if="loadedFileName" class="ml-auto flex items-center gap-2 text-muted-foreground">
      <span class="font-medium text-foreground">📄 {{ loadedFileName }}</span>
      <span v-if="totalRecords > 0" class="rounded bg-muted px-1.5 py-0.5 text-[10px]">
        {{ totalRecords }} registros
      </span>
    </div>

    <p v-if="parseError" class="w-full text-xs font-medium text-destructive">
      {{ parseError }}
    </p>
  </div>
</template>
