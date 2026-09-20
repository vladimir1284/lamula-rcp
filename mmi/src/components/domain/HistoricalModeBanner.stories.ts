import type { Meta, StoryObj } from '@storybook/vue3-vite'
import HistoricalModeBanner from './HistoricalModeBanner.vue'

const meta: Meta<typeof HistoricalModeBanner> = {
  title: 'Domain/HistoricalModeBanner (B9)',
  component: HistoricalModeBanner,
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    fileName: 'bite_history_2026-09-20.json',
    totalRecords: 14,
  },
}
