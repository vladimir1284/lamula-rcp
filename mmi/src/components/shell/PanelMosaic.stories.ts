import type { Meta, StoryObj } from '@storybook/vue3-vite'
import PanelMosaic from './PanelMosaic.vue'

const meta: Meta<typeof PanelMosaic> = {
  title: 'Shell/PanelMosaic',
  component: PanelMosaic,
}
export default meta

type Story = StoryObj<typeof meta>

const slotTemplate = `
  <template #a>
    <div class="flex h-full w-full items-center justify-center rounded border border-border bg-card p-4 font-mono text-sm">
      Panel A (C3 Scan Worksheet)
    </div>
  </template>
  <template #b>
    <div class="flex h-full w-full items-center justify-center rounded border border-border bg-card p-4 font-mono text-sm">
      Panel B (D2 ASCOPE)
    </div>
  </template>
  <template #c>
    <div class="flex h-full w-full items-center justify-center rounded border border-border bg-card p-4 font-mono text-sm">
      Panel C (G2 TX/RX Adjustment)
    </div>
  </template>
  <template #d>
    <div class="flex h-full w-full items-center justify-center rounded border border-border bg-card p-4 font-mono text-sm">
      Panel D (H1 Sun Position)
    </div>
  </template>
`

export const Single: Story = {
  args: { layout: 'single' },
  render: (args) => ({
    components: { PanelMosaic },
    setup: () => ({ args }),
    template: `
      <div style="height: 400px; display: flex; flex-direction: column;">
        <PanelMosaic v-bind="args">
          ${slotTemplate}
        </PanelMosaic>
      </div>
    `,
  }),
}

export const SplitHorizontal: Story = {
  args: { layout: 'split-h' },
  render: (args) => ({
    components: { PanelMosaic },
    setup: () => ({ args }),
    template: `
      <div style="height: 400px; display: flex; flex-direction: column;">
        <PanelMosaic v-bind="args">
          ${slotTemplate}
        </PanelMosaic>
      </div>
    `,
  }),
}

export const SplitVertical: Story = {
  args: { layout: 'split-v' },
  render: (args) => ({
    components: { PanelMosaic },
    setup: () => ({ args }),
    template: `
      <div style="height: 400px; display: flex; flex-direction: column;">
        <PanelMosaic v-bind="args">
          ${slotTemplate}
        </PanelMosaic>
      </div>
    `,
  }),
}

export const TripleLeft: Story = {
  args: { layout: 'triple-left' },
  render: (args) => ({
    components: { PanelMosaic },
    setup: () => ({ args }),
    template: `
      <div style="height: 400px; display: flex; flex-direction: column;">
        <PanelMosaic v-bind="args">
          ${slotTemplate}
        </PanelMosaic>
      </div>
    `,
  }),
}

export const Quad: Story = {
  args: { layout: 'quad' },
  render: (args) => ({
    components: { PanelMosaic },
    setup: () => ({ args }),
    template: `
      <div style="height: 400px; display: flex; flex-direction: column;">
        <PanelMosaic v-bind="args">
          ${slotTemplate}
        </PanelMosaic>
      </div>
    `,
  }),
}
