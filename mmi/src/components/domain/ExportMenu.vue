<script setup lang="ts">
import { ref } from 'vue'
import { Button } from '@/components/ui/button'
import {
  captureElementAsPng,
  copyToClipboard,
  exportToCsv,
  exportToJson,
} from '@/lib/exportUtils'

const props = withDefaults(
  defineProps<{
    targetEl?: HTMLElement | null
    exportData?: unknown
    filename?: string
    title?: string
    size?: 'icon-xs' | 'xs' | 'sm' | 'default'
    variant?: 'ghost' | 'outline' | 'default' | 'secondary'
  }>(),
  {
    targetEl: null,
    exportData: undefined,
    filename: 'export',
    title: 'Exportar / Snapshot (I6)',
    size: 'icon-xs',
    variant: 'ghost',
  },
)

const emit = defineEmits<{
  export: [payload: { format: 'png' | 'json' | 'csv' | 'clipboard'; success: boolean }]
}>()

const isOpen = ref(false)
const rootRef = ref<HTMLDivElement | null>(null)
const capturing = ref(false)
const copied = ref(false)

function toggleMenu() {
  isOpen.value = !isOpen.value
}

function closeMenu() {
  isOpen.value = false
}

function getFilenameWithTimestamp(ext: string): string {
  const ts = new Date().toISOString().replace(/[:.]/g, '-')
  return `${props.filename}_${ts}.${ext}`
}

async function handleSnapshot() {
  if (capturing.value) return
  capturing.value = true
  try {
    let elementToCapture = props.targetEl
    if (!elementToCapture && rootRef.value) {
      elementToCapture =
        rootRef.value.closest('.flex.h-full.min-h-0.flex-col') as HTMLElement ||
        rootRef.value.closest('[data-panel-frame]') as HTMLElement ||
        rootRef.value.parentElement as HTMLElement
    }
    if (!elementToCapture) elementToCapture = document.body

    const fn = getFilenameWithTimestamp('png')
    await captureElementAsPng(elementToCapture, fn)
    emit('export', { format: 'png', success: true })
  } catch {
    emit('export', { format: 'png', success: false })
  } finally {
    capturing.value = false
    closeMenu()
  }
}

function handleExportJson() {
  try {
    const data = props.exportData ?? { timestamp: new Date().toISOString(), info: 'Panel Export' }
    const fn = getFilenameWithTimestamp('json')
    exportToJson(data, fn)
    emit('export', { format: 'json', success: true })
  } catch {
    emit('export', { format: 'json', success: false })
  } finally {
    closeMenu()
  }
}

function handleExportCsv() {
  try {
    const data = props.exportData ?? { timestamp: new Date().toISOString(), info: 'Panel Export' }
    const fn = getFilenameWithTimestamp('csv')
    const formattedData = Array.isArray(data)
      ? (data as Record<string, unknown>[])
      : typeof data === 'object' && data !== null
        ? (data as Record<string, unknown>)
        : { value: data }
    exportToCsv(formattedData, fn)
    emit('export', { format: 'csv', success: true })
  } catch {
    emit('export', { format: 'csv', success: false })
  } finally {
    closeMenu()
  }
}

async function handleCopyToClipboard() {
  try {
    const data = props.exportData ?? { timestamp: new Date().toISOString() }
    const text = typeof data === 'string' ? data : JSON.stringify(data, null, 2)
    const ok = await copyToClipboard(text)
    copied.value = ok
    setTimeout(() => {
      copied.value = false
    }, 1500)
    emit('export', { format: 'clipboard', success: ok })
  } catch {
    emit('export', { format: 'clipboard', success: false })
  } finally {
    closeMenu()
  }
}
</script>

<template>
  <div ref="rootRef" class="relative inline-block text-left">
    <Button
      :size="size"
      :variant="variant"
      :title="title"
      aria-label="Exportar panel"
      :aria-expanded="isOpen"
      @click="toggleMenu"
    >
      <span class="text-xs">📥</span>
    </Button>

    <div
      v-if="isOpen"
      class="fixed inset-0 z-40"
      @click="closeMenu"
    />

    <div
      v-if="isOpen"
      class="absolute right-0 top-full z-50 mt-1 w-44 rounded-md border border-border bg-popover p-1 text-popover-foreground shadow-md text-xs"
    >
      <button
        class="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 hover:bg-accent text-left"
        :disabled="capturing"
        @click="handleSnapshot"
      >
        <span>📷</span>
        <span>Snapshot (PNG)</span>
      </button>
      <button
        class="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 hover:bg-accent text-left"
        @click="handleExportCsv"
      >
        <span>📊</span>
        <span>Exportar CSV</span>
      </button>
      <button
        class="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 hover:bg-accent text-left"
        @click="handleExportJson"
      >
        <span>📄</span>
        <span>Exportar JSON</span>
      </button>
      <button
        class="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 hover:bg-accent text-left"
        @click="handleCopyToClipboard"
      >
        <span>📋</span>
        <span>{{ copied ? '¡Copiado!' : 'Copiar Portapapeles' }}</span>
      </button>
    </div>
  </div>
</template>
