import type { Meta, StoryObj } from '@storybook/vue3-vite'
import PpiView from './PpiView.vue'

// D3. Mismo límite que AscopeView.stories.ts: datos sintéticos, sin backend.
const meta: Meta<typeof PpiView> = {
  title: 'Views/PpiView (D3)',
  component: PpiView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  render: () => ({
    components: { PpiView },
    template: '<div style="height: 480px; width: 960px"><PpiView /></div>',
  }),
}

export const Frozen: Story = {
  render: () => ({
    components: { PpiView },
    template: '<div style="height: 480px; width: 960px"><PpiView :frozen="true" /></div>',
  }),
}
