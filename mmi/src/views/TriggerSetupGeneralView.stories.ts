import type { Meta, StoryObj } from '@storybook/vue3-vite'
import TriggerSetupGeneralView from './TriggerSetupGeneralView.vue'

const meta: Meta<typeof TriggerSetupGeneralView> = {
  title: 'Views/TriggerSetupGeneralView (E5)',
  component: TriggerSetupGeneralView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}

export const MosaicQuadrant: Story = {
  render: () => ({
    components: { TriggerSetupGeneralView },
    template: '<div style="width: 960px; height: 480px;" class="border overflow-hidden"><TriggerSetupGeneralView /></div>',
  }),
}
