import type { Meta, StoryObj } from '@storybook/vue3-vite'
import MaintenanceUnlockView from './MaintenanceUnlockView.vue'

const meta: Meta<typeof MaintenanceUnlockView> = {
  title: 'Views/MaintenanceUnlockView (A4)',
  component: MaintenanceUnlockView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
