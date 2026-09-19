import type { Meta, StoryObj } from '@storybook/vue3-vite'
import EventLogView from './EventLogView.vue'

// A5. useGateway.mock.ts siembra eventos con kinds variados
// (control_mode_changed, *_started, *_failed, *_cancelled) para que se vean
// los tres niveles de `severityOf` (info/warn/error) sin backend real.
const meta: Meta<typeof EventLogView> = {
  title: 'Views/EventLogView (A5)',
  component: EventLogView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
