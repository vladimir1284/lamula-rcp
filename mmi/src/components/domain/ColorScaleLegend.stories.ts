import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ColorScaleLegend from './ColorScaleLegend.vue'

const meta: Meta<typeof ColorScaleLegend> = {
  title: 'Domain/ColorScaleLegend',
  component: ColorScaleLegend,
  render: (args) => ({
    components: { ColorScaleLegend },
    setup: () => ({ args }),
    template: '<div style="height: 220px"><ColorScaleLegend v-bind="args" /></div>',
  }),
}
export default meta

type Story = StoryObj<typeof meta>

export const Reflectivity: Story = { args: { kind: 'reflectivity' } }
export const Velocity: Story = { args: { kind: 'velocity' } }
export const Width: Story = { args: { kind: 'width' } }
