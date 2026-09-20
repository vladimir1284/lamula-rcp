import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ProcessMonitorView from './ProcessMonitorView.vue'

const meta: Meta<typeof ProcessMonitorView> = {
  title: 'Views/ProcessMonitorView (B5)',
  component: ProcessMonitorView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
