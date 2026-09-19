import type { Meta, StoryObj } from '@storybook/vue3-vite'
import CursorReadout from './CursorReadout.vue'

const meta: Meta<typeof CursorReadout> = {
  title: 'Domain/CursorReadout',
  component: CursorReadout,
}
export default meta

type Story = StoryObj<typeof meta>

export const Empty: Story = { args: { cursor: null } }

export const Ascope: Story = {
  args: { cursor: { rangeKm: 42.3, azimuthDeg: 127.4, elevationDeg: 0.5, value: 0.62, kind: 'reflectivity' } },
}

export const Rhi: Story = {
  args: { cursor: { rangeKm: 30.1, azimuthDeg: 45, elevationDeg: 12.4, heightKm: 6.47, value: -0.31, kind: 'velocity' } },
}
