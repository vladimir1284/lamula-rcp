import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ThresholdMatrixView from './ThresholdMatrixView.vue'

const meta: Meta<typeof ThresholdMatrixView> = {
  title: 'Views/ThresholdMatrixView (E3)',
  component: ThresholdMatrixView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
