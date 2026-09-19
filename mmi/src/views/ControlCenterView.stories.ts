import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ControlCenterView from './ControlCenterView.vue'

// C4. control=activo en el doble de gateway -- las cuatro PrecheckList sólo
// marcan ✗ en el campo numérico sin valor, no en "autoridad activa". Probar
// "General power-on" dispara runControlJob() mockeado: busy ~600ms y
// resultado success, igual que contra un RCP real.
const meta: Meta<typeof ControlCenterView> = {
  title: 'Views/ControlCenterView (C4)',
  component: ControlCenterView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
