import type { Meta, StoryObj } from '@storybook/vue3-vite'
import RadarConstantView from './RadarConstantView.vue'

const meta: Meta<typeof RadarConstantView> = {
  title: 'Views/RadarConstantView (G7)',
  component: RadarConstantView,
  parameters: {
    layout: 'fullscreen',
  },
}

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {}
