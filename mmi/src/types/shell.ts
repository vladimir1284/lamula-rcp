// Tipos del shell/mosaico (docs/diseno/inventario-ui.md, paso 2 "Shell y
// mosaico"). No son contrato RCP: son estado de presentación del propio MMI,
// así que viven aquí y no en contracts/.

export type LampState = 'ok' | 'neutral' | 'fault'

export type IndicatorId = 'SI' | 'SR' | 'SD' | 'RD'

export interface IndicatorState {
  id: IndicatorId
  state: LampState
  detail?: string
}

export type MosaicLayout = 'single' | 'split-h' | 'split-v' | 'triple-left' | 'quad'

export const PANEL_COUNT: Record<MosaicLayout, number> = {
  single: 1,
  'split-h': 2,
  'split-v': 2,
  'triple-left': 3,
  quad: 4,
}

export interface ViewOption {
  id: string
  label: string
  // false = el preset referencia una vista que no aplica en este contexto
  // (docs/diseno/inventario-ui.md, decisión abierta #1: "preset que
  // referencia una vista no aplicable").
  available: boolean
}

export interface PanelState {
  id: string
  viewId: string | null
  frozen: boolean
}

export interface MosaicPreset {
  id: string
  label: string
  layout: MosaicLayout
  // Vista por defecto de cada panel, en el orden de PANEL_COUNT[layout].
  viewIds: (string | null)[]
  builtin: boolean
}
