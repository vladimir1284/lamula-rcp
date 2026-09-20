import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ScanParameterPopup from './ScanParameterPopup.vue'

const meta: Meta<typeof ScanParameterPopup> = {
  title: 'Domain/ScanParameterPopup (D8)',
  component: ScanParameterPopup,
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
