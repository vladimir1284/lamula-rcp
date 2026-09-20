import type { Meta, StoryObj } from '@storybook/vue3-vite'
import SnapshotAction from './SnapshotAction.vue'

const meta: Meta<typeof SnapshotAction> = {
  title: 'Domain/SnapshotAction',
  component: SnapshotAction,
  args: {
    filename: 'panel-snapshot',
    title: 'Capturar PNG (Snapshot)',
    size: 'icon-xs',
    variant: 'ghost',
  },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}

export const WithLabel: Story = {
  args: {
    size: 'sm',
    variant: 'outline',
    label: 'Captura PNG',
  },
}
