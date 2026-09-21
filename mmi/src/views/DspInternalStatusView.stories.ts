import type { Meta, StoryObj } from '@storybook/vue3-vite'
import DspInternalStatusView from './DspInternalStatusView.vue'

const meta: Meta<typeof DspInternalStatusView> = {
  title: 'Views/DspInternalStatusView (E12)',
  component: DspInternalStatusView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
