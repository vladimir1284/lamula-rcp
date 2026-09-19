import type { Meta, StoryObj } from '@storybook/vue3-vite'
import SubsystemDetailView from './SubsystemDetailView.vue'

// B2. El doble de useGateway.mock.ts trae una falla activa en tx
// (`tx.interlock_ok_status`) -- suficiente para ver lámpara roja + agregado
// "falla(s)" en el subsistema Transmisor sin backend real.
const meta: Meta<typeof SubsystemDetailView> = {
  title: 'Views/SubsystemDetailView (B2)',
  component: SubsystemDetailView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
