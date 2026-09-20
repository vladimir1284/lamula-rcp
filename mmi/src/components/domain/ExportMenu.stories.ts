import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ExportMenu from './ExportMenu.vue'

const meta: Meta<typeof ExportMenu> = {
  title: 'Domain/ExportMenu',
  component: ExportMenu,
  args: {
    filename: 'export-data',
    exportData: {
      radar: 'RD100S-01',
      status: 'OK',
      metrics: [12.5, 34.2, 88.0],
    },
    size: 'icon-xs',
    variant: 'ghost',
  },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}

export const SmallButton: Story = {
  args: {
    size: 'sm',
    variant: 'outline',
  },
}
