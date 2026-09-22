import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ParameterField from './ParameterField.vue'

const meta: Meta<typeof ParameterField> = {
  title: 'Domain/ParameterField',
  component: ParameterField,
}
export default meta

type Story = StoryObj<typeof meta>

export const Accepted: Story = {
  args: {
    label: 'TX Frequency',
    modelValue: 30.0,
    unit: 'MHz',
    readOnlyValue: 30.0,
    accepted: true,
    helpText: 'Frecuencia intermedia del transmisor',
  },
}

export const NotAccepted: Story = {
  args: {
    label: 'Commanded LO Freq.',
    modelValue: 5600.0,
    unit: 'MHz',
    readOnlyValue: 5580.0,
    accepted: false,
    helpText: 'Frecuencia desalineada respecto a lectura HAL',
  },
}

export const WithoutReadValue: Story = {
  args: {
    label: 'TX Start Sample',
    modelValue: 10,
    unit: '29 ns',
    readOnlyValue: null,
    accepted: false,
    helpText: 'Inicio de ventana de muestreo',
  },
}

export const Disabled: Story = {
  args: {
    label: 'TX Sample Count',
    modelValue: 16,
    unit: 'pulsos',
    readOnlyValue: 16,
    accepted: true,
    disabled: true,
  },
}
