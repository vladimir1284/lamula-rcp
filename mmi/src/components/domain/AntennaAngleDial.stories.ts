import type { Meta, StoryObj } from '@storybook/vue3-vite'
import AntennaAngleDial from './AntennaAngleDial.vue'

const meta: Meta<typeof AntennaAngleDial> = {
  title: 'Domain/AntennaAngleDial',
  component: AntennaAngleDial,
}
export default meta

type Story = StoryObj<typeof meta>

export const Azimuth: Story = {
  args: {
    axis: 'azimuth',
    valueDeg: 123.4,
    targetDeg: 135,
    rateDegS: 6.0,
    toleranceDeg: 0.05,
    valid: true,
  },
}

export const AzimuthEnTolerancia: Story = {
  args: {
    axis: 'azimuth',
    valueDeg: 134.98,
    targetDeg: 135,
    rateDegS: 0,
    toleranceDeg: 0.05,
    valid: true,
  },
}

export const Elevacion: Story = {
  args: {
    axis: 'elevation',
    valueDeg: 12.3,
    targetDeg: 35,
    rateDegS: 0,
    toleranceDeg: 0.05,
    valid: true,
  },
}

export const EncoderInvalido: Story = {
  args: {
    axis: 'azimuth',
    valueDeg: 0,
    targetDeg: null,
    rateDegS: null,
    valid: false,
  },
}
