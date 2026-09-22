import type { Meta, StoryObj } from '@storybook/vue3-vite'
import SetupHubGrid, { type SetupHubItem } from './SetupHubGrid.vue'

const meta: Meta<typeof SetupHubGrid> = {
  title: 'Domain/SetupHubGrid (E1)',
  component: SetupHubGrid,
}
export default meta

type Story = StoryObj<typeof meta>

const sampleItems: SetupHubItem[] = [
  {
    id: 'mp-processing-options',
    code: 'E2',
    title: 'Processing Options (Mp)',
    family: 'Setup DSP',
    description: 'Espectros, algoritmos R2/microsupresión, series temporales, polarimetría y KDP.',
    dirty: true,
    access: 'MANT',
    available: true,
  },
  {
    id: 'thresholds-matrix',
    code: 'E3',
    title: 'Thresholds Matrix (Vp)',
    family: 'Setup DSP',
    description: 'Matriz de 19 parámetros × 5 umbrales y banderas TCF (solo lectura).',
    dirty: false,
    access: 'MANT',
    available: true,
  },
  {
    id: 'clutter-filters',
    code: 'E4',
    title: 'Clutter Filters (Mf)',
    family: 'Setup DSP',
    description: 'Filtros de clutter fijos, variables y modelo gaussiano con anchos Doppler.',
    dirty: false,
    access: 'MANT',
    available: false,
  },
  {
    id: 'pb-plot',
    code: 'F1',
    title: 'Burst Pulse Timing (Pb)',
    family: 'Ajuste',
    description: 'Plot en vivo para captura y centrado del pulso de transmisión.',
    dirty: false,
    access: 'OP',
    available: true,
  },
]

export const Default: Story = {
  args: {
    items: sampleItems,
  },
}

export const AllAvailableAndSynced: Story = {
  args: {
    items: sampleItems.map((item) => ({ ...item, dirty: false, available: true })),
  },
}

export const Empty: Story = {
  args: {
    items: [],
  },
}
