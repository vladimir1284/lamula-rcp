import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ProcessingOptionsView from './ProcessingOptionsView.vue'

const meta: Meta<typeof ProcessingOptionsView> = {
  title: 'Views/ProcessingOptionsView (E2)',
  component: ProcessingOptionsView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}

export const MosaicQuadrant: Story = {
  render: () => ({
    components: { ProcessingOptionsView },
    template: '<div style="width: 960px; height: 480px;" class="border overflow-hidden"><ProcessingOptionsView /></div>',
  }),
}
