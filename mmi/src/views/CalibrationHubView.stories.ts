import type { Meta, StoryObj } from '@storybook/vue3-vite'
import CalibrationHubView from './CalibrationHubView.vue'

const meta: Meta<typeof CalibrationHubView> = {
  title: 'Views/CalibrationHubView (G1)',
  component: CalibrationHubView,
}

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  render: () => ({
    components: { CalibrationHubView },
    template: `
      <div style="height: 600px;" class="bg-background text-foreground">
        <CalibrationHubView />
      </div>
    `,
  }),
}
