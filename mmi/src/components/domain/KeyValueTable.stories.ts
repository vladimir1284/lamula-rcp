import type { Meta, StoryObj } from '@storybook/vue3-vite'
import KeyValueTable, { type KeyValueItem } from './KeyValueTable.vue'

const sampleItems: KeyValueItem[] = [
  { key: 'version', label: 'Versión del RCP', value: '1.2.0' },
  { key: 'simulated', label: 'Simulado', value: true },
  { key: 'count', label: 'Cortes Totales', value: 4 },
  { key: 'status', label: 'Estado', value: null },
]

const gapItems: KeyValueItem[] = [
  { key: 'location', label: 'Coordenadas Radar', value: 'No configurado', gap: 'sin backend de coordenadas GPS' },
  { key: 'comp_status', label: 'Estado Subsistemas', value: 'Pendiente', gap: 'sin backend de telemetría' },
]

const meta: Meta<typeof KeyValueTable> = {
  title: 'Domain/KeyValueTable',
  component: KeyValueTable,
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    items: sampleItems,
  },
}

export const WithGapNotices: Story = {
  args: {
    items: gapItems,
  },
}
