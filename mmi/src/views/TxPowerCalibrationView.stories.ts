import type { Meta, StoryObj } from '@storybook/vue3-vite'
import TxPowerCalibrationView from './TxPowerCalibrationView.vue'

const meta: Meta<typeof TxPowerCalibrationView> = {
  title: 'Views/TxPowerCalibrationView (G3)',
  component: TxPowerCalibrationView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
