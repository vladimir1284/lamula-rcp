import type { Meta, StoryObj } from '@storybook/vue3-vite'
import SinglePointCalibrationView from './SinglePointCalibrationView.vue'

const meta: Meta<typeof SinglePointCalibrationView> = {
  title: 'Views/SinglePointCalibrationView',
  component: SinglePointCalibrationView,
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof SinglePointCalibrationView>

export const Default: Story = {
  args: {
    hasActiveControl: true,
    isMaintenanceUnlocked: true,
  },
}
