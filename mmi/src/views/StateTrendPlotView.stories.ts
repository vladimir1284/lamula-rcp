import type { Meta, StoryObj } from '@storybook/vue3-vite'
import StateTrendPlotView from './StateTrendPlotView.vue'

const meta: Meta<typeof StateTrendPlotView> = {
  title: 'Views/StateTrendPlotView (B4)',
  component: StateTrendPlotView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
