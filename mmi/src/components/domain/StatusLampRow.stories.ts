import type { Meta, StoryObj } from '@storybook/vue3-vite'
import StatusLampRow from './StatusLampRow.vue'

const meta: Meta<typeof StatusLampRow> = {
  title: 'Domain/StatusLampRow',
  component: StatusLampRow,
}
export default meta

type Story = StoryObj<typeof meta>

export const Healthy: Story = {
  args: {
    label: 'Interlock Enclavamiento TX',
    signalId: 'tx.interlock_ok_status',
    fault: false,
    stale: false,
  },
}

export const FaultWithDetail: Story = {
  args: {
    label: 'Interlock Enclavamiento TX',
    signalId: 'tx.interlock_ok_status',
    fault: true,
    stale: false,
    detail: 'interlock abierto',
  },
}

export const Stale: Story = {
  args: {
    label: 'Interlock Enclavamiento TX',
    signalId: 'tx.interlock_ok_status',
    fault: false,
    stale: true,
  },
}
