<script setup lang="ts">
import { ref } from 'vue'
import { Button } from '@/components/ui/button'
import { captureElementAsPng } from '@/lib/exportUtils'

const props = withDefaults(
  defineProps<{
    targetEl?: HTMLElement | null
    filename?: string
    title?: string
    size?: 'icon-xs' | 'xs' | 'sm' | 'default'
    variant?: 'ghost' | 'outline' | 'default' | 'secondary'
    label?: string
  }>(),
  {
    targetEl: null,
    filename: 'snapshot',
    title: 'Capturar PNG (Snapshot)',
    size: 'icon-xs',
    variant: 'ghost',
    label: '',
  },
)

const emit = defineEmits<{
  captured: [dataUrl: string]
  error: [err: Error]
}>()

const btnRef = ref<InstanceType<typeof Button> | null>(null)
const capturing = ref(false)

async function takeSnapshot() {
  if (capturing.value) return
  capturing.value = true

  try {
    let elementToCapture = props.targetEl
    if (!elementToCapture && btnRef.value) {
      const btnEl = (btnRef.value as unknown as { $el?: HTMLElement }).$el || (btnRef.value as unknown as HTMLElement)
      // Attempt to find closest panel frame or fallback to parent container
      elementToCapture =
        btnEl.closest('.flex.h-full.min-h-0.flex-col') as HTMLElement ||
        btnEl.closest('[data-panel-frame]') as HTMLElement ||
        btnEl.parentElement as HTMLElement
    }

    if (!elementToCapture) {
      elementToCapture = document.body
    }

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const name = `${props.filename}_${timestamp}.png`
    const dataUrl = await captureElementAsPng(elementToCapture, name)
    emit('captured', dataUrl)
  } catch (err) {
    const error = err instanceof Error ? err : new Error(String(err))
    emit('error', error)
  } finally {
    capturing.value = false
  }
}
</script>

<template>
  <Button
    ref="btnRef"
    :size="size"
    :variant="variant"
    :disabled="capturing"
    :title="title"
    aria-label="Capturar PNG"
    @click="takeSnapshot"
  >
    <span v-if="capturing" class="animate-spin text-[10px]">⏳</span>
    <span v-else class="text-xs">📷</span>
    <span v-if="label" class="ml-1 text-xs">{{ label }}</span>
  </Button>
</template>
