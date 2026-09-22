import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ChannelSelector from './ChannelSelector.vue'

const meta: Meta<typeof ChannelSelector> = {
  title: 'Domain/ChannelSelector (B4)',
  component: ChannelSelector,
}
export default meta

type Story = StoryObj<typeof meta>

const mockChannels = [
  'tx.power_fwd',
  'tx.power_rev',
  'rv.temperature',
  'rx.noise_level',
  'azimuth.encoder_angle',
  'elevation.encoder_angle',
]

export const Default: Story = {
  args: {
    channels: mockChannels,
    selected: ['tx.power_fwd', 'tx.power_rev'],
    disabled: false,
  },
}

export const Disabled: Story = {
  args: {
    channels: mockChannels,
    selected: ['tx.power_fwd', 'tx.power_rev'],
    disabled: true,
  },
}

export const AllSelected: Story = {
  args: {
    channels: mockChannels,
    selected: mockChannels,
    disabled: false,
  },
}

export const NoneSelected: Story = {
  args: {
    channels: mockChannels,
    selected: [],
    disabled: false,
  },
}
