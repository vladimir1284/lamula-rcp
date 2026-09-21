import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ThresholdsMatrixView from './ThresholdsMatrixView.vue'

const meta: Meta<typeof ThresholdsMatrixView> = {
  title: 'Views/ThresholdsMatrixView (E3)',
  component: ThresholdsMatrixView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}

export const MosaicQuadrant: Story = {
  render: () => ({
    components: { ThresholdsMatrixView },
    template: '<div style="width: 960px; height: 480px;" class="border overflow-hidden"><ThresholdsMatrixView /></div>',
  }),
}
