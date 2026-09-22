import type { Meta, StoryObj } from '@storybook/vue3-vite'
import TriggerSetupPwView from './TriggerSetupPwView.vue'

const meta: Meta<typeof TriggerSetupPwView> = {
  title: 'Views/TriggerSetupPwView (E6)',
  component: TriggerSetupPwView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}

export const MosaicQuadrant: Story = {
  render: () => ({
    components: { TriggerSetupPwView },
    template: '<div style="width: 960px; height: 480px;" class="border overflow-hidden"><TriggerSetupPwView /></div>',
  }),
}
