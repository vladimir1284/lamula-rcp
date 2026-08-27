import type { Meta, StoryObj } from '@storybook/vue3-vite'
import AxisPositioningFields, { type PartialAxisPositioningParams } from './AxisPositioningFields.vue'

const meta: Meta<typeof AxisPositioningFields> = {
  title: 'Domain/AxisPositioningFields',
  component: AxisPositioningFields,
}
export default meta

type Story = StoryObj<typeof meta>

const empty: PartialAxisPositioningParams = {
  gain_v_per_deg: undefined,
  max_voltage: undefined,
  tolerance_deg: undefined,
  timeout_s: undefined,
}

const filled: PartialAxisPositioningParams = {
  gain_v_per_deg: 0.5,
  max_voltage: 10,
  tolerance_deg: 0.2,
  timeout_s: 30,
}

export const Empty: Story = { args: { modelValue: empty, axisLabel: 'azimuth_positioning (sin confirmar)' } }
export const Filled: Story = { args: { modelValue: filled, axisLabel: 'azimuth_positioning (sin confirmar)' } }
export const NoLabel: Story = { args: { modelValue: filled } }
