import type { Meta, StoryObj } from '@storybook/vue3-vite'
import JobActionPanel from './JobActionPanel.vue'
import type { RoutineResult } from '@/types/mmi'

const meta: Meta<typeof JobActionPanel> = {
  title: 'Domain/JobActionPanel',
  component: JobActionPanel,
}
export default meta

type Story = StoryObj<typeof meta>

const successResult: RoutineResult = {
  routine: 'general-power-on',
  outcome: 'success',
  steps: [
    { signal_id: 'sys.standby_system_ok_status', ok: true, detail: 'ok' },
    { signal_id: 'sys.line_parameters_ok_status', ok: true, detail: 'ok' },
  ],
  at_us: 0,
}

const failedResult: RoutineResult = {
  routine: 'general-power-on',
  outcome: 'failed',
  steps: [{ signal_id: 'sys.standby_system_ok_status', ok: false, detail: 'precondición no cumplida' }],
  at_us: 0,
}

export const Idle: Story = { args: { busy: false, runLabel: 'General power-on' } }
export const RunDisabled: Story = { args: { busy: false, runLabel: 'General power-on', runDisabled: true } }
export const Busy: Story = {
  args: { busy: true, jobId: 'job-123', runLabel: 'General power-on', busyText: 'en curso...' },
}
export const Success: Story = { args: { busy: false, runLabel: 'General power-on', result: successResult } }
export const Failed: Story = { args: { busy: false, runLabel: 'General power-on', result: failedResult } }
export const WithError: Story = {
  args: { busy: false, runLabel: 'General power-on', error: 'POST /api/control/general-power-on: HTTP 500' },
}
