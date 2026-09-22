import type { Meta, StoryObj } from '@storybook/vue3-vite'
import PlotTransportControls from './PlotTransportControls.vue'

const meta: Meta<typeof PlotTransportControls> = {
  title: 'Domain/PlotTransportControls (B4)',
  component: PlotTransportControls,
}
export default meta

type Story = StoryObj<typeof meta>

export const Idle: Story = {
  args: {
    running: false,
    hasData: false,
    canStart: true,
    disabled: false,
  },
}

export const Running: Story = {
  args: {
    running: true,
    hasData: true,
    canStart: true,
    disabled: false,
  },
}

export const PausedWithData: Story = {
  args: {
    running: false,
    hasData: true,
    canStart: true,
    disabled: false,
  },
}

export const Disabled: Story = {
  args: {
    running: false,
    hasData: false,
    canStart: false,
    disabled: true,
  },
}
