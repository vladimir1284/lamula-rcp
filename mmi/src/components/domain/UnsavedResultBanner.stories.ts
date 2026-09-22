import type { Meta, StoryObj } from '@storybook/vue3-vite'
import UnsavedResultBanner from './UnsavedResultBanner.vue'

const meta: Meta<typeof UnsavedResultBanner> = {
  title: 'Domain/UnsavedResultBanner',
  component: UnsavedResultBanner,
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof UnsavedResultBanner>

export const Unsaved: Story = {
  args: {
    saved: false,
  },
}

export const Saved: Story = {
  args: {
    saved: true,
  },
}
