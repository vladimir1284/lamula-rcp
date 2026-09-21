import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ColorComposer from './ColorComposer.vue'

const meta: Meta<typeof ColorComposer> = {
  title: 'Domain/ColorComposer',
  component: ColorComposer,
}

export default meta
type Story = StoryObj<typeof meta>

export const Reflectivity: Story = {
  render: () => ({
    components: { ColorComposer },
    template: `
      <div class="p-4 bg-background max-w-xl">
        <ColorComposer initial-kind="reflectivity" />
      </div>
    `,
  }),
}

export const VelocityDivergent: Story = {
  render: () => ({
    components: { ColorComposer },
    template: `
      <div class="p-4 bg-background max-w-xl">
        <ColorComposer initial-kind="velocity" />
      </div>
    `,
  }),
}

export const WidthSequential: Story = {
  render: () => ({
    components: { ColorComposer },
    template: `
      <div class="p-4 bg-background max-w-xl">
        <ColorComposer initial-kind="width" />
      </div>
    `,
  }),
}
