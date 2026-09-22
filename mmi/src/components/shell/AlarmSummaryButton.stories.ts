import type { Meta, StoryObj } from '@storybook/vue3-vite'
import AlarmSummaryButton from './AlarmSummaryButton.vue'
import type { LampState } from '@/types/shell'

const meta: Meta<typeof AlarmSummaryButton> = {
  title: 'Shell/AlarmSummaryButton',
  component: AlarmSummaryButton,
}
export default meta

type Story = StoryObj<typeof meta>

export const Normal: Story = {
  args: {
    worst: 'ok' as LampState,
    count: 0,
  },
}

export const ActiveFaults: Story = {
  args: {
    worst: 'fault' as LampState,
    count: 3,
  },
}

export const DisabledOrNoData: Story = {
  args: {
    worst: 'neutral' as LampState,
    count: 0,
  },
}
