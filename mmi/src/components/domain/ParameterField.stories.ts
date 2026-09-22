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
    modelValue: 2800,
    readout: 2800,
    unit: 'MHz',
    accepted: true,
  },
}

export const Pending: Story = {
  args: {
    label: 'Commanded LO Freq.',
    modelValue: 2770,
    readout: 2750,
    unit: 'MHz',
    accepted: false,
  },
}

export const NoReadout: Story = {
  args: {
    label: 'TX Start Sample',
    modelValue: 32,
    readout: null,
    unit: 'samples',
    accepted: false,
  },
}

export const Disabled: Story = {
  args: {
    label: 'TX Sample',
    modelValue: 128,
    readout: 128,
    unit: 'samples',
    accepted: true,
    disabled: true,
  },
}
