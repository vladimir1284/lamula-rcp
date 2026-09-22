import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ConfirmDangerDialog from './ConfirmDangerDialog.vue'

const meta: Meta<typeof ConfirmDangerDialog> = {
  title: 'Domain/ConfirmDangerDialog (E12)',
  component: ConfirmDangerDialog,
}
export default meta

type Story = StoryObj<typeof meta>

export const RequireTyping: Story = {
  args: {
    open: true,
    title: 'Reiniciar Contadores de Trigger (Vz)',
    description:
      'Esta acción reiniciará los contadores acumulados de radiales y triggers en el procesador DSP.',
    actionLabel: 'Reiniciar Contadores',
    requireTyping: 'REINICIAR',
    loading: false,
    consequences: [
      'Los contadores de radiales de entrada, salida y descartados volverán a 0.',
      'Se enviará el mandato de control RESET_COUNTERS (Vz) al hardware DSP.',
    ],
  },
}

export const LoadingState: Story = {
  args: {
    open: true,
    title: 'Reiniciar Contadores de Trigger (Vz)',
    description:
      'Esta acción reiniciará los contadores acumulados de radiales y triggers en el procesador DSP.',
    actionLabel: 'Reiniciar Contadores',
    requireTyping: 'REINICIAR',
    loading: true,
    consequences: [
      'Los contadores de radiales de entrada, salida y descartados volverán a 0.',
      'Se enviará el mandato de control RESET_COUNTERS (Vz) al hardware DSP.',
    ],
  },
}

export const BasicDialog: Story = {
  args: {
    open: true,
    title: 'Eliminar Configuración Seleccionada',
    description: '¿Está seguro de que desea eliminar este perfil permanentemente?',
    actionLabel: 'Eliminar',
    loading: false,
  },
}
