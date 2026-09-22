import type { Meta, StoryObj } from '@storybook/vue3-vite'
import EquationPanel from './EquationPanel.vue'

const meta: Meta<typeof EquationPanel> = {
  title: 'Domain/EquationPanel (G7)',
  component: EquationPanel,
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    activeField: null,
  },
}

export const HighlightedGain: Story = {
  args: {
    activeField: 'antenna_gain_db',
  },
}

export const HighlightedWavelength: Story = {
  args: {
    activeField: 'wavelength_cm',
  },
}
