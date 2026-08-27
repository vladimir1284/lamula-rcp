import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ConnectionStatusBadge from './ConnectionStatusBadge.vue'

const meta: Meta<typeof ConnectionStatusBadge> = {
  title: 'Domain/ConnectionStatusBadge',
  component: ConnectionStatusBadge,
}
export default meta

type Story = StoryObj<typeof meta>

export const Open: Story = { args: { status: 'OPEN' } }
export const Connecting: Story = { args: { status: 'CONNECTING' } }
export const Closed: Story = { args: { status: 'CLOSED' } }
export const CustomLabel: Story = { args: { status: 'OPEN', label: 'DSP' } }
