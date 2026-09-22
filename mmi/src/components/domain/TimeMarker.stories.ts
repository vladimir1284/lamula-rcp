import type { Meta, StoryObj } from '@storybook/vue3-vite'
import TimeMarker from './TimeMarker.vue'
import type { MarkerInfo } from './TimeMarker.vue'

const meta: Meta<typeof TimeMarker> = {
  title: 'Domain/TimeMarker',
  component: TimeMarker,
  decorators: [
    () => ({
      template:
        '<svg viewBox="0 0 800 200" style="width: 100%; height: 200px; background: rgba(0,0,0,0.9);"><story /></svg>',
    }),
  ],
}
export default meta

type Story = StoryObj<typeof meta>

const mockMarkers: MarkerInfo[] = [
  { x: 250, timeStr: '14:23:00', gapDurationS: 2.5 },
  { x: 550, timeStr: '14:25:12', gapDurationS: 10.0 },
]

export const Default: Story = {
  args: {
    markers: mockMarkers,
    height: 180,
  },
}

export const NoMarkers: Story = {
  args: {
    markers: [],
    height: 180,
  },
}
