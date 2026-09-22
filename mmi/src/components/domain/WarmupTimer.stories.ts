import type { Meta, StoryObj } from '@storybook/vue3-vite'
import WarmupTimer from './WarmupTimer.vue'

const meta: Meta<typeof WarmupTimer> = {
  title: 'Domain/WarmupTimer (G3)',
  component: WarmupTimer,
}
export default meta

type Story = StoryObj<typeof meta>

export const RadiatingInProgress: Story = {
  args: {
    radiating: true,
    requiredSeconds: 1200,
    initialElapsedSeconds: 300,
  },
}

export const Completed: Story = {
  args: {
    radiating: true,
    requiredSeconds: 1200,
    initialElapsedSeconds: 1200,
  },
}

export const Inactive: Story = {
  args: {
    radiating: false,
    requiredSeconds: 1200,
    initialElapsedSeconds: 0,
  },
}
