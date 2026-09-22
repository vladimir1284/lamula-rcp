import type { Meta, StoryObj } from '@storybook/vue3-vite'
import IndicatorBar from './IndicatorBar.vue'
import type { IndicatorState } from '@/types/shell'

const meta: Meta<typeof IndicatorBar> = {
  title: 'Shell/IndicatorBar',
  component: IndicatorBar,
}
export default meta

type Story = StoryObj<typeof meta>

const normalIndicators: IndicatorState[] = [
  { id: 'SI', state: 'ok', detail: 'Tarea recibida, esperando inicio' },
  { id: 'SR', state: 'ok', detail: 'Scan en ejecución' },
  { id: 'SD', state: 'ok', detail: 'Enlace de datos activo' },
  { id: 'RD', state: 'ok', detail: '3.2 Mbps' },
]

const degradedIndicators: IndicatorState[] = [
  { id: 'SI', state: 'ok', detail: 'Tarea recibida, esperando inicio' },
  { id: 'SR', state: 'fault', detail: 'Error en ejecución de scan' },
  { id: 'SD', state: 'neutral', detail: 'Sin datos de estado hace 6 s' },
  { id: 'RD', state: 'neutral', detail: 'Sin datos de recepción' },
]

export const AllOk: Story = {
  args: {
    indicators: normalIndicators,
  },
}

export const DegradedOrStale: Story = {
  args: {
    indicators: degradedIndicators,
  },
}
