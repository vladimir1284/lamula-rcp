<script setup lang="ts">
// Barra de herramientas de D2/D3 (docs/diseno/inventario-ui.md) -- compartida
// entre ASCOPE/PPI/RHI porque las tres piden los mismos controles (freeze
// queda afuera a propósito, ver nota abajo). `refresh-rate` solo aplica a
// D2 (PPI/RHI no lo piden). `axis-unit` solo aplica a D2 (km/µsec).
//
// El freeze de "congela esta vista sin afectar a las demás" ya existe en
// PanelFrame (❄ en el encabezado de panel, paso 2) y es genuinamente por
// instancia de panel -- duplicar un segundo botón de freeze acá sería el
// mismo control dos veces. Las vistas D2/D3/D4 reciben `frozen` como prop
// (ver App.vue) y lo usan para pausar su propio loop de datos.
//
// D6: Botón Color Composer integrado como drawer / modal en la barra de herramientas.
import { ref } from 'vue'
import ColorComposer from '@/components/domain/ColorComposer.vue'
import ScanParameterPopup from '@/components/domain/ScanParameterPopup.vue'
import { Button } from '@/components/ui/button'
import { DATA_KINDS, type DataKind } from '@/lib/mockRadar'

withDefaults(
  defineProps<{
    dataType: DataKind
    resolution: number
    zoom: number
    source: 'radar' | 'file'
    showRefreshRate?: boolean
    refreshRate?: number
    showAxisUnit?: boolean
    axisUnit?: 'km' | 'us'
  }>(),
  { showRefreshRate: false, refreshRate: 1, showAxisUnit: false, axisUnit: 'km' },
)

const emit = defineEmits<{
  'update:dataType': [value: DataKind]
  'update:resolution': [value: number]
  'update:zoom': [value: number]
  'update:source': [value: 'radar' | 'file']
  'update:refreshRate': [value: number]
  'update:axisUnit': [value: 'km' | 'us']
  'color-composer-updated': []
}>()

const RESOLUTIONS = [16, 64, 256]
const ZOOMS = [1, 2, 4]

const showComposer = ref(false)

function onComposerKindUpdate(newKind: DataKind) {
  emit('update:dataType', newKind)
}

function onPaletteChanged() {
  emit('color-composer-updated')
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-1.5 border-b border-border pb-1.5 text-xs">
    <div class="flex gap-1" role="tablist" aria-label="Tipo de dato">
      <Button
        v-for="k in DATA_KINDS"
        :key="k.id"
        size="xs"
        :variant="dataType === k.id ? 'secondary' : 'ghost'"
        role="tab"
        :aria-selected="dataType === k.id"
        @click="$emit('update:dataType', k.id)"
      >
        {{ k.label }}
      </Button>
    </div>

    <label class="flex items-center gap-1 text-muted-foreground">
      Resolución
      <select
        class="rounded-sm border border-border bg-background px-1 py-0.5 text-xs"
        :value="resolution"
        @change="$emit('update:resolution', Number(($event.target as HTMLSelectElement).value))"
      >
        <option v-for="r in RESOLUTIONS" :key="r" :value="r">{{ r }}</option>
      </select>
    </label>

    <label class="flex items-center gap-1 text-muted-foreground">
      Zoom
      <select
        class="rounded-sm border border-border bg-background px-1 py-0.5 text-xs"
        :value="zoom"
        @change="$emit('update:zoom', Number(($event.target as HTMLSelectElement).value))"
      >
        <option v-for="z in ZOOMS" :key="z" :value="z">{{ z }}x</option>
      </select>
    </label>

    <label v-if="showRefreshRate" class="flex items-center gap-1 text-muted-foreground">
      Refresh
      <select
        class="rounded-sm border border-border bg-background px-1 py-0.5 text-xs"
        :value="refreshRate"
        @change="$emit('update:refreshRate', Number(($event.target as HTMLSelectElement).value))"
      >
        <option v-for="n in [1, 2, 5, 10]" :key="n" :value="n">1/{{ n }}</option>
      </select>
    </label>

    <label v-if="showAxisUnit" class="flex items-center gap-1 text-muted-foreground">
      Eje
      <select
        class="rounded-sm border border-border bg-background px-1 py-0.5 text-xs"
        :value="axisUnit"
        @change="$emit('update:axisUnit', ($event.target as HTMLSelectElement).value as 'km' | 'us')"
      >
        <option value="km">km</option>
        <option value="us">µsec</option>
      </select>
    </label>

    <div class="ml-auto flex items-center gap-1">
      <Button
        size="xs"
        variant="outline"
        title="Editar paleta de color (D6)"
        @click="showComposer = true"
      >
        🎨 Color
      </Button>

      <div class="flex gap-1" role="radiogroup" aria-label="Fuente de datos">
        <Button
          size="xs"
          :variant="source === 'radar' ? 'secondary' : 'outline'"
          title="Radar en vivo"
          @click="$emit('update:source', 'radar')"
        >
          Radar
        </Button>
        <Button
          size="xs"
          :variant="source === 'file' ? 'secondary' : 'outline'"
          title="Fichero (no implementado, mock)"
          @click="$emit('update:source', 'file')"
        >
          Fichero
        </Button>
      </div>
      <ScanParameterPopup />
    </div>

    <!-- Drawer / Popup Modal de Color Composer -->
    <div
      v-if="showComposer"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs"
      @click.self="showComposer = false"
    >
      <div class="relative max-h-[90vh] w-full max-w-lg overflow-y-auto">
        <ColorComposer
          :initial-kind="dataType"
          @update:kind="onComposerKindUpdate"
          @palette-changed="onPaletteChanged"
        />
        <Button
          size="xs"
          variant="ghost"
          class="absolute right-3 top-3 h-6 w-6 p-0 text-muted-foreground hover:text-foreground"
          @click="showComposer = false"
        >
          ✕
        </Button>
      </div>
    </div>
  </div>
</template>
