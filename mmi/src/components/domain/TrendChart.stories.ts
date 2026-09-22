import type { Meta, StoryObj } from '@storybook/vue3-vite'
import TrendChart from './TrendChart.vue'
import type { TrendSeries } from '@/types/mmi'

const meta: Meta<typeof TrendChart> = {
  title: 'Domain/TrendChart (B4)',
  component: TrendChart,
}
export default meta

type Story = StoryObj<typeof meta>

const baseTime = new Date('2025-01-01T12:00:00Z').getTime()

const normalSeries: TrendSeries[] = [
  {
    signal_id: 'tx.power_fwd',
    samples: [
      { at_wall: new Date(baseTime).toISOString(), value: 1200 },
      { at_wall: new Date(baseTime + 1000).toISOString(), value: 1210 },
      { at_wall: new Date(baseTime + 2000).toISOString(), value: 1205 },
      { at_wall: new Date(baseTime + 3000).toISOString(), value: 1220 },
      { at_wall: new Date(baseTime + 4000).toISOString(), value: 1215 },
    ],
  },
  {
    signal_id: 'tx.power_rev',
    samples: [
      { at_wall: new Date(baseTime).toISOString(), value: 40 },
      { at_wall: new Date(baseTime + 1000).toISOString(), value: 42 },
      { at_wall: new Date(baseTime + 2000).toISOString(), value: 41 },
      { at_wall: new Date(baseTime + 3000).toISOString(), value: 45 },
      { at_wall: new Date(baseTime + 4000).toISOString(), value: 43 },
    ],
  },
]

const seriesWithGap: TrendSeries[] = [
  {
    signal_id: 'tx.power_fwd',
    samples: [
      { at_wall: new Date(baseTime).toISOString(), value: 1200 },
      { at_wall: new Date(baseTime + 1000).toISOString(), value: 1210 },
      // Gap > 1.5s
      { at_wall: new Date(baseTime + 5000).toISOString(), value: 1205 },
      { at_wall: new Date(baseTime + 6000).toISOString(), value: 1220 },
    ],
  },
]

export const Default: Story = {
  args: {
    series: normalSeries,
  },
}

export const WithGap: Story = {
  args: {
    series: seriesWithGap,
  },
}

export const Empty: Story = {
  args: {
    series: [],
  },
}
