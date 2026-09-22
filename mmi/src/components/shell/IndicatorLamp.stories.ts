import type { Meta, StoryObj } from '@storybook/vue3-vite'
import IndicatorLamp from './IndicatorLamp.vue'
import type { LampState } from '@/types/shell'

const meta: Meta<typeof IndicatorLamp> = {
  title: 'Shell/IndicatorLamp',
  component: IndicatorLamp,
}
export default meta

type Story = StoryObj<typeof meta>

export const Ok: Story = {
  args: {
    label: 'SR',
    state: 'ok' as LampState,
    detail: 'Scan en ejecución',
  },
}

export const Neutral: Story = {
  args: {
    label: 'SD',
    state: 'neutral' as LampState,
    detail: 'Sin datos de estado hace 6 s',
  },
}

export const Fault: Story = {
  args: {
    label: 'SI',
    state: 'fault' as LampState,
    detail: 'Falla de comunicación con DSP',
  },
}
