import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ClockPair from './ClockPair.vue'

const meta: Meta<typeof ClockPair> = {
  title: 'Shell/ClockPair',
  component: ClockPair,
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
