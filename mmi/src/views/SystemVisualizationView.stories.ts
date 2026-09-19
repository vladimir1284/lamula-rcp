import type { Meta, StoryObj } from '@storybook/vue3-vite'
import SystemVisualizationView from './SystemVisualizationView.vue'

// B1. Datos vía useGateway.mock.ts (alias de Storybook, ver .storybook/main.ts)
// -- una falla activa sembrada en tx.* para ver el estado "con falla" del
// agrupado por subsistema sin backend real.
const meta: Meta<typeof SystemVisualizationView> = {
  title: 'Views/SystemVisualizationView (B1)',
  component: SystemVisualizationView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
