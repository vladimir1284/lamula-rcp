import type { Meta, StoryObj } from '@storybook/vue3-vite'
import SinglePointCalibrationView from './SinglePointCalibrationView.vue'

const meta: Meta<typeof SinglePointCalibrationView> = {
  title: 'Views/SinglePointCalibrationView (G4)',
  component: SinglePointCalibrationView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
