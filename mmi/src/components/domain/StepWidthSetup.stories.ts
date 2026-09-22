import type { Meta, StoryObj } from '@storybook/vue3-vite'
import StepWidthSetup from './StepWidthSetup.vue'

const meta: Meta<typeof StepWidthSetup> = {
  title: 'Domain/StepWidthSetup (C1)',
  component: StepWidthSetup,
}
export default meta

type Story = StoryObj<typeof meta>

export const Open: Story = {
  args: {
    open: true,
  },
}

export const Closed: Story = {
  args: {
    open: false,
  },
}
