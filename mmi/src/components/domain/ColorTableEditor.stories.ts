import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ColorTableEditor from './ColorTableEditor.vue'

const sampleStops = [
  'oklch(0.35 0.15 260)',
  'oklch(0.55 0.22 140)',
  'oklch(0.75 0.18 80)',
  'oklch(0.90 0.12 40)',
]

const minimalStops = [
  'oklch(0.40 0.20 200)',
  'oklch(0.80 0.20 20)',
]

const meta: Meta<typeof ColorTableEditor> = {
  title: 'Domain/ColorTableEditor',
  component: ColorTableEditor,
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    stops: sampleStops,
  },
}

export const MinimalStops: Story = {
  args: {
    stops: minimalStops,
  },
}
