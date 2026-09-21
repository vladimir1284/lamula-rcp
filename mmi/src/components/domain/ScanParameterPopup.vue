<script setup lang="ts">
// D8 — Scan Parameter Popup (docs/diseno/inventario-ui.md)
//
// Muestra un snapshot congelado de los parámetros de escaneo vigentes (Worksheet).
//
// Regla clave de congelación de estado:
// Al abrir el popup / solicitar datos, se obtiene una copia local congelada
// (snapshot) en ese instante en lugar de mantener una suscripción en vivo.
import { ref } from 'vue'
import KeyValueTable, { type KeyValueItem } from '@/components/domain/KeyValueTable.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useGateway } from '@/composables/useGateway'
import type { ScanCut } from '@/types/scan'

const { fetchScanWorksheet } = useGateway()

const isOpen = ref(false)
const isLoading = ref(false)
const errorMsg = ref<string | null>(null)

// Copia local congelada (snapshot) + marca de tiempo
const frozenSnapshot = ref<ScanCut[] | null>(null)
const capturedAt = ref<string | null>(null)

async function loadFrozenSnapshot() {
  isLoading.value = true
  errorMsg.value = null
  try {
    const cuts = await fetchScanWorksheet()
    // Copia congelada
    frozenSnapshot.value = JSON.parse(JSON.stringify(cuts)) as ScanCut[]
    capturedAt.value = new Date().toLocaleTimeString()
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : String(e)
  } finally {
    isLoading.value = false
  }
}

function openPopup() {
  isOpen.value = true
  loadFrozenSnapshot()
}

function closePopup() {
  isOpen.value = false
}

function formatCutItems(cuts: ScanCut[]): KeyValueItem[] {
  if (cuts.length === 0) {
    return [
      {
        key: 'empty',
        label: 'Estado del Worksheet',
        value: 'Sin cortes configurados en el worksheet',
      },
    ]
  }

  const items: KeyValueItem[] = [
    {
      key: 'cut_count',
      label: 'Cortes Totales',
      value: `${cuts.length} corte(s)`,
    },
  ]

  cuts.forEach((cut, idx) => {
    const prefix = `cut_${idx + 1}`
    const labelPrefix = `Corte #${idx + 1}`

    items.push({
      key: `${prefix}_mode`,
      label: `${labelPrefix} Modo`,
      value: cut.mode.toUpperCase(),
    })

    if (cut.mode === 'ppi') {
      items.push({
        key: `${prefix}_elevation`,
        label: `${labelPrefix} Elevación`,
        value: `${cut.elevation_deg}°`,
      })
      items.push({
        key: `${prefix}_azimuth_sweep`,
        label: `${labelPrefix} Barrido Azimut`,
        value: `${cut.azimuth_start_deg}° → ${cut.azimuth_end_deg}°`,
      })
    } else {
      items.push({
        key: `${prefix}_azimuth`,
        label: `${labelPrefix} Azimut`,
        value: `${cut.azimuth_deg}°`,
      })
      items.push({
        key: `${prefix}_elevation_sweep`,
        label: `${labelPrefix} Barrido Elevación`,
        value: `${cut.elevation_start_deg}° → ${cut.elevation_end_deg}°`,
      })
    }

    items.push({
      key: `${prefix}_prf`,
      label: `${labelPrefix} PRF`,
      value: `${cut.prf_hz} Hz`,
    })

    items.push({
      key: `${prefix}_pulse_width`,
      label: `${labelPrefix} Ancho de Pulso`,
      value: `${cut.pulse_width_us} µs`,
    })

    items.push({
      key: `${prefix}_moments`,
      label: `${labelPrefix} Momentos`,
      value: cut.moments.join(', '),
    })
  })

  return items
}
</script>

<template>
  <div class="relative inline-block">
    <Button
      size="xs"
      variant="outline"
      title="Ver parámetros de escaneo congelados (D8)"
      @click="openPopup"
    >
      Parámetros Scan
    </Button>

    <div
      v-if="isOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs"
      @click.self="closePopup"
    >
      <div
        class="flex max-h-[85vh] w-full max-w-lg flex-col rounded-lg border border-border bg-card p-4 shadow-xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="scan-param-title"
      >
        <div class="flex items-center justify-between border-b border-border pb-2">
          <div class="flex items-center gap-2">
            <h3 id="scan-param-title" class="text-sm font-semibold text-foreground">
              Parámetros de Scan (D8)
            </h3>
            <Badge v-if="capturedAt" variant="outline" class="text-[10px] text-sky-400 border-sky-500/40">
              Congelado: {{ capturedAt }}
            </Badge>
          </div>
          <Button size="xs" variant="ghost" class="h-6 w-6 p-0" @click="closePopup">
            ✕
          </Button>
        </div>

        <div class="my-3 flex-1 overflow-auto pr-1">
          <div v-if="isLoading" class="py-6 text-center text-xs text-muted-foreground">
            Cargando snapshot de parámetros...
          </div>
          <div v-else-if="errorMsg" class="py-4 text-xs text-destructive">
            Error al obtener snapshot: {{ errorMsg }}
          </div>
          <KeyValueTable
            v-else-if="frozenSnapshot !== null"
            :items="formatCutItems(frozenSnapshot)"
          />
        </div>

        <div class="flex items-center justify-between border-t border-border pt-2 text-xs text-muted-foreground">
          <span class="text-[10px]">Copia local congelada · Sin suscripción en vivo</span>
          <div class="flex gap-2">
            <Button size="xs" variant="secondary" :disabled="isLoading" @click="loadFrozenSnapshot">
              Actualizar
            </Button>
            <Button size="xs" variant="outline" @click="closePopup">
              Cerrar
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
