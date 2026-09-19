import type { Meta, StoryObj } from '@storybook/vue3-vite'
import TrafficLight from './TrafficLight.vue'

const meta: Meta<typeof TrafficLight> = {
  title: 'Domain/TrafficLight',
  component: TrafficLight,
}
export default meta

type Story = StoryObj<typeof meta>

export const Ok: Story = { args: { worst: 'ok' } }
export const Neutral: Story = { args: { worst: 'neutral' } }
export const Fault: Story = { args: { worst: 'fault' } }
// B8: clicable -- reconocer una falla (baja el semáforo hasta la próxima nueva).
export const Clickable: Story = { args: { worst: 'fault', clickable: true } }
