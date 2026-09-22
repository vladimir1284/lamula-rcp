import type { Meta, StoryObj } from '@storybook/vue3-vite'
import BitmaskStatusList, { type BitmaskBitDef } from './BitmaskStatusList.vue'

const meta: Meta<typeof BitmaskStatusList> = {
  title: 'Domain/BitmaskStatusList',
  component: BitmaskStatusList,
}
export default meta

type Story = StoryObj<typeof meta>

const sampleBits: BitmaskBitDef[] = [
  { bit: 1, label: 'INGEST_DROP', description: 'Pérdida de datos de entrada', severity: 'fault' },
  { bit: 2, label: 'QUEUE_OVERFLOW', description: 'Desbordamiento de cola', severity: 'fault' },
  { bit: 4, label: 'DRX_LINK_DOWN', description: 'Enlace DRX caído', severity: 'fault' },
  { bit: 8, label: 'DRX_CONFIG_REJECTED', description: 'Configuración DRX rechazada', severity: 'warn' },
  { bit: 16, label: 'TRIGGER_DRIFT', description: 'Deriva de periodo de trigger', severity: 'warn' },
]

export const ActiveConditions: Story = {
  args: {
    value: 1 | 8,
    bits: sampleBits,
  },
}

export const Empty: Story = {
  args: {
    value: 0,
    bits: sampleBits,
    emptyText: 'Sin condiciones activas (0x00000000)',
  },
}
