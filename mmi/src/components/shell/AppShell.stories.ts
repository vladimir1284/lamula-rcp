import type { Meta, StoryObj } from '@storybook/vue3-vite'
import AppShell from './AppShell.vue'
import type { ControlAuthorityState } from '@/types/mmi'
import type { IndicatorState, MosaicPreset, ViewOption } from '@/types/shell'

const meta: Meta<typeof AppShell> = {
  title: 'Shell/AppShell',
  component: AppShell,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

const control: ControlAuthorityState = {
  mode: 'active',
  actor: 'operador-1',
  since_wall: new Date().toISOString(),
}

const indicators: IndicatorState[] = [
  { id: 'SI', state: 'ok', detail: 'Tarea recibida, esperando inicio' },
  { id: 'SR', state: 'ok', detail: 'Scan en ejecución' },
  { id: 'SD', state: 'neutral', detail: 'Sin datos de estado hace 6 s' },
  { id: 'RD', state: 'ok', detail: '3.2 Mbps' },
]

// Catálogo de vistas referenciadas por los presets de la tabla de
// concurrencia (docs/diseno/inventario-ui.md). Ninguna existe todavía como
// vista real -- paso 3 en adelante -- así que PanelFrame sólo necesita el
// id/label/available de cada una.
const viewCatalog: ViewOption[] = [
  { id: 'scan-worksheet', label: 'C3 Scan Worksheet', available: true },
  { id: 'ascope', label: 'D2 ASCOPE', available: true },
  { id: 'rsp-tx-rx-adjust', label: 'G2 TX/RX Adjustment', available: true },
  { id: 'antenna-control', label: 'C1 Antenna Control', available: true },
  { id: 'ppi', label: 'D3 PPI', available: true },
  { id: 'sun-position', label: 'H1 Sun Position', available: true },
  { id: 'rhi', label: 'D4 RHI', available: true },
  { id: 'itsg-control', label: 'I2 ITSG Control', available: true },
  { id: 'calibration-log', label: 'G8 Calibration Log', available: true },
  { id: 'bite-messages', label: 'B8 BiTE Messages', available: true },
  { id: 'mb-setup', label: 'E7 Burst Pulse & AFC (Mb)', available: true },
  { id: 'pb-plot', label: 'F1 Burst Pulse Timing (Pb)', available: true },
]

// Cada preset es una fila de "Requisitos de concurrencia"; las de cuatro
// vistas (sun-el, fine-az-el) fijan el máximo de cuatro paneles del mosaico.
const presets: MosaicPreset[] = [
  {
    id: 'tx-pulse-sampling',
    label: 'Muestreo pulso TX',
    layout: 'triple-left',
    viewIds: ['scan-worksheet', 'ascope', 'rsp-tx-rx-adjust'],
    builtin: true,
  },
  {
    id: 'sun-az',
    label: 'Corrección az. por sol',
    layout: 'triple-left',
    viewIds: ['antenna-control', 'ppi', 'sun-position'],
    builtin: true,
  },
  {
    id: 'sun-el',
    label: 'Corrección el. por sol',
    layout: 'quad',
    viewIds: ['antenna-control', 'scan-worksheet', 'rhi', 'sun-position'],
    builtin: true,
  },
  {
    id: 'fine-az-el',
    label: 'Ajuste fino az/el',
    layout: 'quad',
    viewIds: ['antenna-control', 'scan-worksheet', 'ascope', 'sun-position'],
    builtin: true,
  },
  {
    id: 'matched-filter',
    label: 'Filtro adaptado (Mb↔Pb)',
    layout: 'split-h',
    viewIds: ['mb-setup', 'pb-plot'],
    builtin: true,
  },
  {
    id: 'itsg-adjust',
    label: 'Ajuste ITSG',
    layout: 'split-h',
    viewIds: ['itsg-control', 'ascope'],
    builtin: true,
  },
  {
    id: 'calibration-log',
    label: 'Calibración + log',
    layout: 'split-h',
    viewIds: ['rsp-tx-rx-adjust', 'calibration-log'],
    builtin: true,
  },
  {
    id: 'surveillance',
    label: 'Vigilancia (BiTE)',
    layout: 'single',
    viewIds: ['bite-messages'],
    builtin: true,
  },
]

const baseArgs = {
  siteName: 'RD100S-01',
  host: '10.0.4.12',
  simulated: false,
  control,
  accessLevel: 'OP' as const,
  indicators,
  alarmWorst: 'ok' as const,
  alarmCount: 0,
  presets,
  viewCatalog,
}

// Demo interactiva: cambiar de preset, elegir vista por panel, congelar,
// gestionar presets (renombrar/restablecer/eliminar/duplicar).
export const Interactive: Story = { args: baseArgs }

export const Simulated: Story = { args: { ...baseArgs, simulated: true, siteName: 'RD100S-EMU' } }

// Ancho de referencia estrecho: un panel de un mosaico de cuatro,
// ~960x480 px (docs/diseno/inventario-ui.md, "Densidad alta"). El propio
// AppShell no impone min-width mayor -- este contenedor es el que reproduce
// el presupuesto de espacio real.
export const ReferenceWidthNarrow: Story = {
  args: { ...baseArgs, initialPresetId: 'fine-az-el' },
  render: (args) => ({
    components: { AppShell },
    setup: () => ({ args }),
    template: `
      <div style="width:960px;height:480px;border:1px dashed var(--border);overflow:hidden">
        <AppShell v-bind="args" />
      </div>
    `,
  }),
}

// Ancho amplio: un panel a pantalla completa (layout `single`), el otro
// extremo del presupuesto de espacio frente a ReferenceWidthNarrow.
export const ReferenceWidthFull: Story = {
  args: { ...baseArgs, initialPresetId: 'surveillance' },
  render: (args) => ({
    components: { AppShell },
    setup: () => ({ args }),
    template: `
      <div style="width:1920px;height:1080px;border:1px dashed var(--border);overflow:hidden">
        <AppShell v-bind="args" />
      </div>
    `,
  }),
}

// Pendiente #1: "preset que referencia una vista no aplicable". El preset
// activo pide RHI, pero el catálogo la marca no disponible (p. ej. modo de
// escaneo que no genera corte vertical) -- el panel debe mostrar el hueco,
// no una vista rota ni un color de error.
export const ViewNotApplicable: Story = {
  args: {
    ...baseArgs,
    viewCatalog: viewCatalog.map((v) => (v.id === 'rhi' ? { ...v, available: false } : v)),
  },
}
