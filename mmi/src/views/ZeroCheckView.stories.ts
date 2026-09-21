import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ZeroCheckView from './ZeroCheckView.vue'

const meta: Meta<typeof ZeroCheckView> = {
  title: 'Views/ZeroCheckView (G5)',
  component: ZeroCheckView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
