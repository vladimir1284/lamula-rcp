import type { Meta, StoryObj } from '@storybook/vue3-vite'
import SystemInformationView from './SystemInformationView.vue'

// A7. sessionInfo/control sembrados en useGateway.mock.ts.
const meta: Meta<typeof SystemInformationView> = {
  title: 'Views/SystemInformationView (A7)',
  component: SystemInformationView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
