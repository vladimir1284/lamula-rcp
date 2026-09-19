import type { Meta, StoryObj } from '@storybook/vue3-vite'
import RhiView from './RhiView.vue'

// D4. Mismo límite que AscopeView.stories.ts: datos sintéticos, sin backend.
const meta: Meta<typeof RhiView> = {
  title: 'Views/RhiView (D4)',
  component: RhiView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  render: () => ({
    components: { RhiView },
    template: '<div style="height: 480px; width: 960px"><RhiView /></div>',
  }),
}

export const Frozen: Story = {
  render: () => ({
    components: { RhiView },
    template: '<div style="height: 480px; width: 960px"><RhiView :frozen="true" /></div>',
  }),
}
