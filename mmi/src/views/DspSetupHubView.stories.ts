import type { Meta, StoryObj } from '@storybook/vue3-vite'
import DspSetupHubView from './DspSetupHubView.vue'

const meta: Meta<typeof DspSetupHubView> = {
  title: 'Views/DspSetupHubView (E1)',
  component: DspSetupHubView,
  parameters: { layout: 'fullscreen' },
}

export default meta
type Story = StoryObj<typeof DspSetupHubView>

export const Default: Story = {
  render: () => ({
    components: { DspSetupHubView },
    template: '<div class="h-[650px] w-full border rounded-lg overflow-hidden"><DspSetupHubView /></div>',
  }),
}
