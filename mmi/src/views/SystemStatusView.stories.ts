import type { Meta, StoryObj } from '@storybook/vue3-vite'
import SystemStatusView from './SystemStatusView.vue'

// B10. Mismo doble de gateway que el resto de Views/* -- ver useGateway.mock.ts.
const meta: Meta<typeof SystemStatusView> = {
  title: 'Views/SystemStatusView (B10)',
  component: SystemStatusView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
