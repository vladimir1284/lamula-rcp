import type { Meta, StoryObj } from '@storybook/vue3-vite'
import FaultBadgeRow from './FaultBadgeRow.vue'
import type { BiteFaultSummary } from '@/types/mmi'

const meta: Meta<typeof FaultBadgeRow> = {
  title: 'Domain/FaultBadgeRow',
  component: FaultBadgeRow,
}
export default meta

type Story = StoryObj<typeof meta>

const fault: BiteFaultSummary = {
  signal_id: 'tx.interlock_ok_status',
  detail: 'interlock abierto',
  since_wall: new Date().toISOString(),
}

// System Visualization: agrupado por subsistema, signal_id en texto plano.
export const Grouped: Story = { args: { fault } }
// System Status: lista plana, signal_id como Badge + timestamp.
export const FlatWithTimestamp: Story = { args: { fault, asBadge: true, showTimestamp: true } }
