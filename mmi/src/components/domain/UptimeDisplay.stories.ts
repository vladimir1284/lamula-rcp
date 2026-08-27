import type { Meta, StoryObj } from '@storybook/vue3-vite'
import UptimeDisplay from './UptimeDisplay.vue'

const meta: Meta<typeof UptimeDisplay> = {
  title: 'Domain/UptimeDisplay',
  component: UptimeDisplay,
}
export default meta

type Story = StoryObj<typeof meta>

// Arrancado hace ~2h5m -- el timer interno sigue tickeando solo en la story,
// sin mocks: no es llamada de red ni de store.
export const Default: Story = {
  args: { startedAtWall: new Date(Date.now() - (2 * 3600 + 5 * 60) * 1000).toISOString() },
}
