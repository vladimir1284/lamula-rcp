import type { Meta, StoryObj } from '@storybook/vue3-vite'
import EnvironmentBadge from './EnvironmentBadge.vue'

const meta: Meta<typeof EnvironmentBadge> = {
  title: 'Shell/EnvironmentBadge',
  component: EnvironmentBadge,
}
export default meta

type Story = StoryObj<typeof meta>

export const Simulated: Story = {
  args: {
    simulated: true,
  },
}

export const RealHardware: Story = {
  args: {
    simulated: false,
  },
}
