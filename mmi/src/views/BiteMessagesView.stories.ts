import type { Meta, StoryObj } from '@storybook/vue3-vite'
import BiteMessagesView from './BiteMessagesView.vue'

// B8. useGateway.mock.ts siembra 1 falla activa (tx.interlock_ok_status) y
// un par fault/cleared histórico (ant.servo_ok_status) -- alterna "Mostrar
// resueltas" en el propio Storybook para ver ambos casos sin backend real.
const meta: Meta<typeof BiteMessagesView> = {
  title: 'Views/BiteMessagesView (B8)',
  component: BiteMessagesView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
