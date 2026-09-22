import type { Meta, StoryObj } from '@storybook/vue3-vite'
import RawStatusWordsPanel from './RawStatusWordsPanel.vue'

const meta: Meta<typeof RawStatusWordsPanel> = {
  title: 'Domain/RawStatusWordsPanel (E12)',
  component: RawStatusWordsPanel,
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    biteFlags: 1 | 8,
    capabilityFlags: 1 | 2 | 4 | 16 | 32,
  },
}

export const NoFlags: Story = {
  args: {
    biteFlags: 0,
    capabilityFlags: 0,
  },
}
