import type { Meta, StoryObj } from '@storybook/vue3-vite'
import WizardStepper, { type WizardStepItem } from './WizardStepper.vue'

const meta: Meta<typeof WizardStepper> = {
  title: 'Domain/WizardStepper (G3)',
  component: WizardStepper,
}
export default meta

type Story = StoryObj<typeof meta>

const calibrationSteps: WizardStepItem[] = [
  {
    title: 'Verificación de Precondiciones y Caldeo',
    description: 'Requiere 20 min de radiación activa',
    status: 'completed',
  },
  {
    title: 'Entrada de Potencia de Referencia',
    description: 'Ingrese la potencia pico medida en kW',
    status: 'active',
  },
  {
    title: 'Ajuste de Desfase de Acoplador',
    description: 'Ajuste fino de atenuación (dB)',
    status: 'pending',
  },
]

export const InProgress: Story = {
  args: {
    steps: calibrationSteps,
  },
}

export const AllCompleted: Story = {
  args: {
    steps: calibrationSteps.map((step) => ({ ...step, status: 'completed' })),
  },
}

export const StepFailed: Story = {
  args: {
    steps: [
      {
        title: 'Verificación de Precondiciones y Caldeo',
        description: 'Requiere 20 min de radiación activa',
        status: 'completed',
      },
      {
        title: 'Entrada de Potencia de Referencia',
        description: 'Error al comunicarse con el medidor externo',
        status: 'failed',
      },
      {
        title: 'Ajuste de Desfase de Acoplador',
        description: 'Ajuste fino de atenuación (dB)',
        status: 'pending',
      },
    ],
  },
}
