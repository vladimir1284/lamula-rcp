import type { Meta, StoryObj } from '@storybook/vue3-vite'
import OperatorPromptDialog from './OperatorPromptDialog.vue'

const meta: Meta<typeof OperatorPromptDialog> = {
  title: 'Domain/OperatorPromptDialog',
  component: OperatorPromptDialog,
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof OperatorPromptDialog>

export const Default: Story = {
  args: {
    open: true,
    title: 'Intervención del Operador Requerida',
    prompt: 'Por favor, inyecte una señal de calibración externa y confirme el nivel de potencia.',
    inputLabel: 'Potencia Inyectada (dBm)',
    defaultValue: -30.0,
  },
}

export const ConfirmationOnly: Story = {
  args: {
    open: true,
    title: 'Confirmar Paso de Calibración',
    prompt: 'Asegúrese de retirar la señal externa antes de continuar con la medición.',
  },
}
