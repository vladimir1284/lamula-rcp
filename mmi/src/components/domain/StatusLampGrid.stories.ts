import type { Meta, StoryObj } from '@storybook/vue3-vite'
import StatusLampGrid from './StatusLampGrid.vue'

const meta: Meta<typeof StatusLampGrid> = {
  title: 'Domain/StatusLampGrid (B2)',
  component: StatusLampGrid,
}
export default meta

type Story = StoryObj<typeof meta>

const sampleItems = [
  {
    signalId: 'tx.interlock_ok_status',
    label: 'Interlock Enclavamiento TX',
    fault: false,
    stale: false,
  },
  {
    signalId: 'tx.high_voltage_ready',
    label: 'Alta Tensión Lista',
    fault: false,
    stale: false,
  },
  {
    signalId: 'tx.filament_warmup_done',
    label: 'Caldeo Filamento Completado',
    fault: false,
    stale: false,
  },
  {
    signalId: 'tx.waveguide_pressure_ok',
    label: 'Presión Guía de Onda OK',
    fault: false,
    stale: false,
  },
]

export const HealthyGrid: Story = {
  args: {
    items: sampleItems,
  },
}

export const MixedFaultsAndStale: Story = {
  args: {
    items: [
      {
        signalId: 'tx.interlock_ok_status',
        label: 'Interlock Enclavamiento TX',
        fault: true,
        stale: false,
        detail: 'interlock abierto',
      },
      {
        signalId: 'tx.high_voltage_ready',
        label: 'Alta Tensión Lista',
        fault: false,
        stale: true,
      },
      {
        signalId: 'tx.filament_warmup_done',
        label: 'Caldeo Filamento Completado',
        fault: false,
        stale: false,
      },
      {
        signalId: 'tx.waveguide_pressure_ok',
        label: 'Presión Guía de Onda OK',
        fault: true,
        stale: true,
        detail: 'presión baja',
      },
    ],
  },
}
