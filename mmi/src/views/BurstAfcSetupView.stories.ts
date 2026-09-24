import type { Meta, StoryObj } from '@storybook/vue3-vite'
import BurstAfcSetupView from './BurstAfcSetupView.vue'

const meta: Meta<typeof BurstAfcSetupView> = {
  title: 'Views/BurstAfcSetupView (E7)',
  component: BurstAfcSetupView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}

export const MosaicQuadrant: Story = {
  render: () => ({
    components: { BurstAfcSetupView },
    template: '<div style="width: 960px; height: 480px;" class="border overflow-hidden"><BurstAfcSetupView /></div>',
  }),
}
