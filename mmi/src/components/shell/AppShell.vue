<script setup lang="ts">
// A1 App Shell: compone barra global (nunca se cubre) + barra de presets +
// mosaico. Dueño del estado de presets/paneles porque son la misma pieza de
// interacción (elegir preset cambia el mosaico); las vistas reales que
// llenan cada panel las decide quien use AppShell, vía el slot con nombre
// que coincide con `panel.viewId`.
//
// Nota deliberada de alcance (paso 2, "shell y mosaico" -- antes que
// cualquier vista concreta): este componente no sabe renderizar ninguna
// vista real todavía. AppShell.stories.ts prueba la mecánica con vistas
// de relleno; cablear D1-D8, C1, C3, etc. es el paso 3 (P0 de operación /
// P0 de datos) del orden sugerido.
import { computed, ref, watch } from 'vue'
import GlobalStatusBar from './GlobalStatusBar.vue'
import PresetBar from './PresetBar.vue'
import PanelMosaic from './PanelMosaic.vue'
import PanelFrame from './PanelFrame.vue'
import PresetManager from './PresetManager.vue'
import type { ControlAuthorityState, MaintenanceState } from '@/types/mmi'
import type {
  IndicatorState,
  LampState,
  MosaicPreset,
  PanelState,
  ViewOption,
} from '@/types/shell'
import { PANEL_COUNT } from '@/types/shell'

const props = defineProps<{
  siteName: string
  host: string
  simulated: boolean
  control: ControlAuthorityState | null
  accessLevel: 'OP' | 'MANT'
  maintenance?: MaintenanceState | null
  indicators: IndicatorState[]
  alarmWorst: LampState
  alarmCount: number
  presets: MosaicPreset[]
  viewCatalog: ViewOption[]
  // Opcional: qué preset arranca activo (por defecto, el primero). Sólo
  // para bancos de pruebas/Storybook -- la app real recordará el último
  // preset usado, no algo que este componente deba decidir.
  initialPresetId?: string
}>()

const emit = defineEmits<{ 'open-alarms': [] }>()

// A1: "resumen de alarma ... clicable hacia B8" -- el inventario lo fija a
// BiTE Messages, no es un destino configurable por instancia de AppShell.
const ALARM_TARGET_VIEW_ID = 'bite-messages'

// No usa structuredClone: los props llegan como proxies reactivos de Vue y
// structuredClone lanza DataCloneError sobre ellos en algunos motores. Los
// datos son JSON-planos (sin funciones ni fechas), así que el round-trip
// JSON clona igual de bien sin ese problema.
function clonePreset(p: MosaicPreset): MosaicPreset {
  return JSON.parse(JSON.stringify(p))
}

const presets = ref<MosaicPreset[]>(props.presets.map(clonePreset))
const activePresetId = ref<string>(props.initialPresetId ?? presets.value[0]?.id ?? '')
const managerOpen = ref(false)

function panelsFromPreset(preset: MosaicPreset): PanelState[] {
  return Array.from({ length: PANEL_COUNT[preset.layout] }, (_, i) => ({
    id: `${preset.id}-${i}`,
    viewId: preset.viewIds[i] ?? null,
    frozen: false,
  }))
}

// AppShell requiere al menos un preset -- no tiene sentido un mosaico sin
// ninguno que elegir, así que el fallback usa `!`: es responsabilidad de
// quien lo use pasar `presets` no vacío.
const activePreset = computed(
  () => presets.value.find((p) => p.id === activePresetId.value) ?? presets.value[0]!,
)
const panels = ref<PanelState[]>(panelsFromPreset(activePreset.value))
const slotNames = ['a', 'b', 'c', 'd'] as const

watch(activePresetId, () => {
  const next = panelsFromPreset(activePreset.value)
  // Un panel congelado conserva su vista al cambiar de preset -- es la
  // semántica de "se congela independientemente" aplicada a la elección de
  // preset, no sólo a los datos que ese panel muestra.
  panels.value = next.map((p, i) => (panels.value[i]?.frozen ? { ...panels.value[i], id: p.id } : p))
})

function setPanelView(index: number, viewId: string) {
  const p = panels.value[index]
  if (p) p.viewId = viewId
}
function toggleFreeze(index: number) {
  const p = panels.value[index]
  if (p) p.frozen = !p.frozen
}

// Primer panel no congelado -- congelado significa "no me cambies la
// vista" (paso 3), así que saltar un panel congelado para abrir B8 es la
// misma regla aplicada a este caso, no una excepción nueva. Si los 4 están
// congelados no hay dónde abrir B8 sin romper esa garantía: no-op.
function openAlarms() {
  const idx = panels.value.findIndex((p) => !p.frozen)
  if (idx !== -1) setPanelView(idx, ALARM_TARGET_VIEW_ID)
  emit('open-alarms')
}

function renamePreset(id: string, label: string) {
  const p = presets.value.find((x) => x.id === id)
  if (p) p.label = label
}
function resetPreset(id: string) {
  const original = props.presets.find((x) => x.id === id)
  const idx = presets.value.findIndex((x) => x.id === id)
  if (original && idx !== -1) presets.value[idx] = clonePreset(original)
}
function removePreset(id: string) {
  presets.value = presets.value.filter((x) => x.id !== id)
  if (activePresetId.value === id) activePresetId.value = presets.value[0]?.id ?? ''
}
function duplicateCurrent() {
  const src = activePreset.value
  const id = `${src.id}-copy-${Date.now()}`
  presets.value.push({
    ...clonePreset(src),
    id,
    label: `${src.label} (copia)`,
    builtin: false,
    viewIds: panels.value.map((p) => p.viewId),
  })
  activePresetId.value = id
}
</script>

<template>
  <div class="flex h-full min-h-0 flex-col">
    <GlobalStatusBar
      :site-name="siteName"
      :host="host"
      :simulated="simulated"
      :control="control"
      :access-level="accessLevel"
      :maintenance="maintenance"
      :indicators="indicators"
      :alarm-worst="alarmWorst"
      :alarm-count="alarmCount"
      @open-alarms="openAlarms"
    />
    <PresetBar
      :presets="presets"
      :active-preset-id="activePresetId"
      @select="activePresetId = $event"
      @manage="managerOpen = !managerOpen"
    />
    <div class="relative flex min-h-0 flex-1">
      <PanelMosaic :layout="activePreset.layout">
        <template v-for="(panel, i) in panels" :key="panel.id" #[slotNames[i]]>
          <PanelFrame
            :view-id="panel.viewId"
            :view-options="viewCatalog"
            :frozen="panel.frozen"
            :closable="false"
            @update:view-id="setPanelView(i, $event)"
            @toggle-freeze="toggleFreeze(i)"
          >
            <slot
              :name="panel.viewId ?? '__empty__'"
              :panel="panel"
              :view-id="panel.viewId"
              :set-view="(id: string) => setPanelView(i, id)"
            >
              <div class="flex h-full items-center justify-center text-xs text-muted-foreground">
                (vista de relleno: {{ panel.viewId ?? 'ninguna' }})
              </div>
            </slot>
          </PanelFrame>
        </template>
      </PanelMosaic>
      <PresetManager
        v-if="managerOpen"
        class="absolute right-2 top-2 z-10"
        :presets="presets"
        @rename="renamePreset"
        @reset="resetPreset"
        @remove="removePreset"
        @duplicate-current="duplicateCurrent"
        @close="managerOpen = false"
      />
    </div>
  </div>
</template>
