import type { Meta, StoryObj } from '@storybook/vue3-vite'
import PresetBar from './PresetBar.vue'
import type { MosaicPreset } from '@/types/shell'

const meta: Meta<typeof PresetBar> = {
  title: 'Shell/PresetBar',
  component: PresetBar,
}
export default meta

type Story = StoryObj<typeof meta>

const presets: MosaicPreset[] = [
  {
    id: 'tx-pulse-sampling',
    label: 'Muestreo pulso TX',
    layout: 'triple-left',
    viewIds: ['scan-worksheet', 'ascope', 'rsp-tx-rx-adjust'],
    builtin: true,
  },
  {
    id: 'sun-az',
    label: 'Corrección az. por sol',
    layout: 'triple-left',
    viewIds: ['antenna-control', 'ppi', 'sun-position'],
    builtin: true,
  },
  {
    id: 'sun-el',
    label: 'Corrección el. por sol',
    layout: 'quad',
    viewIds: ['antenna-control', 'scan-worksheet', 'rhi', 'sun-position'],
    builtin: true,
  },
  {
    id: 'fine-az-el',
    label: 'Ajuste fino az/el',
    layout: 'quad',
    viewIds: ['antenna-control', 'scan-worksheet', 'ascope', 'sun-position'],
    builtin: true,
  },
]

export const Default: Story = {
  args: {
    presets,
    activePresetId: 'tx-pulse-sampling',
  },
}

export const NoneActive: Story = {
  args: {
    presets,
    activePresetId: null,
  },
}

export const EmptyPresets: Story = {
  args: {
    presets: [],
    activePresetId: null,
  },
}
