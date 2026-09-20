import type { Meta, StoryObj } from '@storybook/vue3'
import CalibrationLogView from './CalibrationLogView.vue'

const meta: Meta<typeof CalibrationLogView> = {
  title: 'Views/CalibrationLogView',
  component: CalibrationLogView,
}

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  render: () => ({
    components: { CalibrationLogView },
    template: `
      <div class="h-[500px] w-[800px] border border-border bg-background p-2">
        <CalibrationLogView />
      </div>
    `,
  }),
}

export const Empty: Story = {
  render: () => ({
    components: { CalibrationLogView },
    template: `
      <div class="h-[500px] w-[800px] border border-border bg-background p-2">
        <CalibrationLogView :entries="[]" />
      </div>
    `,
  }),
}
