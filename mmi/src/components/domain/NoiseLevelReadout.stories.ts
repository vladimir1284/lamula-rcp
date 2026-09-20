import type { Meta, StoryObj } from '@storybook/vue3-vite'
import NoiseLevelReadout from './NoiseLevelReadout.vue'

const meta: Meta<typeof NoiseLevelReadout> = {
  title: 'Domain/NoiseLevelReadout',
  component: NoiseLevelReadout,
}
export default meta

type Story = StoryObj<typeof meta>

export const Measured: Story = {
  args: {
    noiseHighDbm: -105.2,
    noiseLowDbm: -102.8,
    lastRunAtWall: new Date(Date.now() - 15 * 60_000).toISOString(),
  },
}

export const Empty: Story = {
  args: {
    noiseHighDbm: null,
    noiseLowDbm: null,
    lastRunAtWall: null,
  },
}
