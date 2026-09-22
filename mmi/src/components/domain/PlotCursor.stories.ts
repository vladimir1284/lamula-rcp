import type { Meta, StoryObj } from '@storybook/vue3-vite'
import PlotCursor from './PlotCursor.vue'
import type { CursorChannelValue } from './PlotCursor.vue'

const meta: Meta<typeof PlotCursor> = {
  title: 'Domain/PlotCursor',
  component: PlotCursor,
  decorators: [
    () => ({
      template:
        '<svg viewBox="0 0 800 200" style="width: 100%; height: 200px; background: rgba(0,0,0,0.9);"><story /></svg>',
    }),
  ],
}
export default meta

type Story = StoryObj<typeof meta>

const mockValues: CursorChannelValue[] = [
  { signal_id: 'tx.power_fwd', color: '#3b82f6', rawValue: 1250 },
  { signal_id: 'tx.power_rev', color: '#ef4444', rawValue: 45 },
]

export const Default: Story = {
  args: {
    x: 400,
    timeStr: '14:23:05',
    values: mockValues,
    height: 180,
  },
}

export const Hidden: Story = {
  args: {
    x: null,
    timeStr: null,
    values: [],
    height: 180,
  },
}
