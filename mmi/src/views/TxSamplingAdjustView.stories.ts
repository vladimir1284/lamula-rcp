import type { Meta, StoryObj } from '@storybook/vue3-vite'
import TxSamplingAdjustView from './TxSamplingAdjustView.vue'

const meta: Meta<typeof TxSamplingAdjustView> = {
  title: 'Views/TxSamplingAdjustView (G2)',
  component: TxSamplingAdjustView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
