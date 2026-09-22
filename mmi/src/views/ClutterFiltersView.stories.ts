import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ClutterFiltersView from './ClutterFiltersView.vue'

const meta: Meta<typeof ClutterFiltersView> = {
  title: 'Views/ClutterFiltersView (E4)',
  component: ClutterFiltersView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}

export const MosaicQuadrant: Story = {
  render: () => ({
    components: { ClutterFiltersView },
    template: '<div style="width: 960px; height: 480px;" class="border overflow-hidden"><ClutterFiltersView /></div>',
  }),
}
