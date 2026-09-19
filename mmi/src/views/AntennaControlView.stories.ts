import type { Meta, StoryObj } from '@storybook/vue3-vite'
import AntennaControlView from './AntennaControlView.vue'

// C1. useGateway.mock.ts sirve control=activo, así que Jog/Posicionar
// aparecen habilitados (salvo por los campos numéricos sin valor, que el
// propio diseño deja en blanco a propósito -- ver PEND-RCP-07 en
// AntennaControlView.vue).
const meta: Meta<typeof AntennaControlView> = {
  title: 'Views/AntennaControlView (C1)',
  component: AntennaControlView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
