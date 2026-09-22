import type { Meta, StoryObj } from '@storybook/vue3-vite'
import PanelFrame from './PanelFrame.vue'
import type { ViewOption } from '@/types/shell'

const meta: Meta<typeof PanelFrame> = {
  title: 'Shell/PanelFrame',
  component: PanelFrame,
}
export default meta

type Story = StoryObj<typeof meta>

const viewOptions: ViewOption[] = [
  { id: 'ascope', label: 'D2 ASCOPE', available: true },
  { id: 'ppi', label: 'D3 PPI', available: true },
  { id: 'rhi', label: 'D4 RHI', available: false },
]

export const Default: Story = {
  args: {
    viewId: 'ascope',
    viewOptions,
    frozen: false,
    closable: false,
  },
  render: (args) => ({
    components: { PanelFrame },
    setup: () => ({ args }),
    template: `
      <div style="height: 300px;">
        <PanelFrame v-bind="args">
          <div class="p-4 text-sm">Contenido de la vista ASCOPE</div>
        </PanelFrame>
      </div>
    `,
  }),
}

export const FrozenAndClosable: Story = {
  args: {
    viewId: 'ppi',
    viewOptions,
    frozen: true,
    closable: true,
  },
  render: (args) => ({
    components: { PanelFrame },
    setup: () => ({ args }),
    template: `
      <div style="height: 300px;">
        <PanelFrame v-bind="args">
          <div class="p-4 text-sm">Contenido de la vista PPI (Congelado)</div>
        </PanelFrame>
      </div>
    `,
  }),
}

export const NotApplicable: Story = {
  args: {
    viewId: 'rhi',
    viewOptions,
    frozen: false,
    closable: false,
  },
  render: (args) => ({
    components: { PanelFrame },
    setup: () => ({ args }),
    template: `
      <div style="height: 300px;">
        <PanelFrame v-bind="args">
          <div class="p-4 text-sm">Contenido RHI</div>
        </PanelFrame>
      </div>
    `,
  }),
}
