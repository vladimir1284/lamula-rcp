import type { Meta, StoryObj } from '@storybook/vue3-vite'
import AscopeView from './AscopeView.vue'

// D2. Datos sintéticos locales (lib/mockRadar.ts) -- no hay stream de
// momentos RCP<->MMI todavía, ver src/core/contracts/mmi.py. "Camino 1"
// acordado: iterar sobre diseño con mock antes de encarar ese contrato.
const meta: Meta<typeof AscopeView> = {
  title: 'Views/AscopeView (D2)',
  component: AscopeView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  render: () => ({
    components: { AscopeView },
    template: '<div style="height: 480px; width: 960px"><AscopeView /></div>',
  }),
}

export const Frozen: Story = {
  render: () => ({
    components: { AscopeView },
    template: '<div style="height: 480px; width: 960px"><AscopeView :frozen="true" /></div>',
  }),
}
