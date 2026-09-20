import type { Meta, StoryObj } from '@storybook/vue3-vite'
import PowerMonitorView from './PowerMonitorView.vue'

const meta: Meta<typeof PowerMonitorView> = {
  title: 'Views/PowerMonitorView (B7)',
  component: PowerMonitorView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
