import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ConnectionView from './ConnectionView.vue'

// A2. El doble de useGateway.mock.ts empieza en OPEN; los botones
// Conectar/Desconectar de la propia vista dejan ver los 3 estados reales
// (CONNECTING/OPEN/CLOSED) de forma interactiva sin backend real.
const meta: Meta<typeof ConnectionView> = {
  title: 'Views/ConnectionView (A2)',
  component: ConnectionView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
