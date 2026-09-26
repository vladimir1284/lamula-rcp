import type { Meta, StoryObj } from '@storybook/vue3-vite'
import BurstSpectraView from './BurstSpectraView.vue'

const meta: Meta<typeof BurstSpectraView> = {
  title: 'Views/BurstSpectraView (F2)',
  component: BurstSpectraView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}

export const MosaicQuadrant: Story = {
  render: () => ({
    components: { BurstSpectraView },
    template: '<div style="width: 960px; height: 480px;" class="border overflow-hidden"><BurstSpectraView /></div>',
  }),
}
