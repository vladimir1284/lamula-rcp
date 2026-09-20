<!--
  StepWidthSetup.vue: Modal para configurar el tamaño de paso en azimut y elevación (C2).
  Gap documentado: Sin persistencia entre reinicios del gateway — mismo criterio
  que el resto del estado de control, en memoria del gateway.
-->
<script setup lang="ts">
import { ref, watch } from 'vue'
import {
  DialogClose,
  DialogContent,
  DialogOverlay,
  DialogPortal,
  DialogRoot,
  DialogTitle,
} from 'reka-ui'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useGateway } from '@/composables/useGateway'
import type { AntennaStepConfig } from '@/types/mmi'

const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'saved', config: AntennaStepConfig): void
}>()

const { fetchStepConfig, setStepConfig } = useGateway()

const azStep = ref<number>(1.0)
const elStep = ref<number>(1.0)
const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)

async function loadConfig() {
  loading.value = true
  error.value = null
  try {
    const cfg = await fetchStepConfig()
    azStep.value = cfg.azimuth_step_deg
    elStep.value = cfg.elevation_step_deg
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      loadConfig()
    }
  },
  { immediate: true },
)

async function handleSave() {
  saving.value = true
  error.value = null
  try {
    const updated = await setStepConfig({
      azimuth_step_deg: azStep.value,
      elevation_step_deg: elStep.value,
    })
    emit('saved', updated)
    emit('update:open', false)
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <DialogRoot :open="open" @update:open="(v) => emit('update:open', v)">
    <DialogPortal>
      <DialogOverlay class="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs" />
      <DialogContent
        class="fixed top-[50%] left-[50%] z-50 w-full max-w-md translate-x-[-50%] translate-y-[-50%] rounded-lg border bg-background p-6 shadow-lg sm:max-w-lg"
      >
        <DialogTitle class="text-lg font-semibold text-foreground">
          Configurar Paso de Posicionamiento
        </DialogTitle>
        <p class="mt-1 text-xs text-muted-foreground">
          Ajuste la amplitud de paso angular en grados para azimut y elevación (mínimo 0.1°, máximo 1.0°).
        </p>

        <div class="mt-4 flex flex-col gap-4">
          <div v-if="loading" class="text-xs text-muted-foreground">Cargando configuración...</div>
          <template v-else>
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-medium text-foreground" for="azimuth-step">
                Paso Azimut (deg) [0.1 – 1.0]
              </label>
              <Input
                id="azimuth-step"
                v-model.number="azStep"
                type="number"
                min="0.1"
                max="1.0"
                step="0.1"
                class="w-full"
              />
            </div>

            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-medium text-foreground" for="elevation-step">
                Paso Elevación (deg) [0.1 – 1.0]
              </label>
              <Input
                id="elevation-step"
                v-model.number="elStep"
                type="number"
                min="0.1"
                max="1.0"
                step="0.1"
                class="w-full"
              />
            </div>
          </template>

          <p v-if="error" class="text-xs font-medium text-destructive">
            {{ error }}
          </p>

          <div class="mt-2 flex justify-end gap-2">
            <DialogClose as-child>
              <Button variant="outline" type="button" :disabled="saving">Cancelar</Button>
            </DialogClose>
            <Button type="button" :disabled="loading || saving" @click="handleSave">
              {{ saving ? 'Guardando...' : 'Guardar' }}
            </Button>
          </div>
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
