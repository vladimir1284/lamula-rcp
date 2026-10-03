import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ThemeToggle from './ThemeToggle.vue'

const meta: Meta<typeof ThemeToggle> = {
  title: 'Shell/ThemeToggle',
  component: ThemeToggle,
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
