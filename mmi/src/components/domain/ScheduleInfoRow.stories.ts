import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ScheduleInfoRow from './ScheduleInfoRow.vue'

const meta: Meta<typeof ScheduleInfoRow> = {
  title: 'Domain/ScheduleInfoRow',
  component: ScheduleInfoRow,
}
export default meta

type Story = StoryObj<typeof meta>

export const Active: Story = {
  args: {
    intervalS: 3600,
    enabled: true,
    lastRunAtWall: new Date(Date.now() - 15 * 60_000).toISOString(),
    nextRunAtWall: new Date(Date.now() + 45 * 60_000).toISOString(),
  },
}

export const Initial: Story = {
  args: {
    intervalS: 3600,
    enabled: true,
    lastRunAtWall: null,
    nextRunAtWall: null,
  },
}
