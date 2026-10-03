import type { Meta, StoryObj } from '@storybook/vue3-vite'
import LevelBar from './LevelBar.vue'

const meta: Meta<typeof LevelBar> = {
  title: 'Domain/LevelBar',
  component: LevelBar,
}
export default meta

type Story = StoryObj<typeof meta>

export const DentroDeTolerancia: Story = {
  args: {
    label: 'Distancia a setpoint',
    value: 0.02,
    min: 0,
    max: 0.1,
    tone: 'ok',
    unit: '°',
  },
}

export const FueraDeTolerancia: Story = {
  args: {
    label: 'Distancia a setpoint',
    value: 0.09,
    min: 0,
    max: 0.1,
    tone: 'warn',
    unit: '°',
  },
}

export const Neutral: Story = {
  args: {
    label: 'Paso configurado',
    value: 1,
    min: 0,
    max: 10,
    tone: 'neutral',
    unit: '°',
  },
}
