import type { Meta, StoryObj } from '@storybook/vue3-vite'
import AxisSelector from './AxisSelector.vue'

const meta: Meta<typeof AxisSelector> = {
  title: 'Domain/AxisSelector',
  component: AxisSelector,
}
export default meta

type Story = StoryObj<typeof meta>

export const Azimuth: Story = { args: { modelValue: 'azimuth' } }
export const Elevation: Story = { args: { modelValue: 'elevation' } }
