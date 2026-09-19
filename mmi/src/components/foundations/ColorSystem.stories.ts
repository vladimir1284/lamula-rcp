import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ColorSystem from './ColorSystem.vue'

const meta: Meta<typeof ColorSystem> = {
  title: 'Foundations/Color System',
  component: ColorSystem,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

// Puesto de radar: el oscuro es el modo principal, no una preferencia (inventario-ui.md §3).
export const Dark: Story = { decorators: [() => ({ template: '<div class="dark"><story /></div>' })] }
export const Light: Story = {}
