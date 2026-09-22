import type { Meta, StoryObj } from '@storybook/vue3-vite'
import PresetManager from './PresetManager.vue'
import type { MosaicPreset } from '@/types/shell'

const meta: Meta<typeof PresetManager> = {
  title: 'Shell/PresetManager',
  component: PresetManager,
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
    id: 'custom-oper-1',
    label: 'Mi Preset Personalizado',
    layout: 'split-h',
    viewIds: ['scan-worksheet', 'ascope'],
    builtin: false,
  },
]

export const Default: Story = {
  args: { presets },
}

export const OnlyBuiltin: Story = {
  args: {
    presets: presets.filter((p) => p.builtin),
  },
}

export const CustomPresets: Story = {
  args: {
    presets: [
      {
        id: 'custom-1',
        label: 'Ajuste RF Personalizado',
        layout: 'quad',
        viewIds: ['antenna-control', 'scan-worksheet', 'ascope', 'sun-position'],
        builtin: false,
      },
      {
        id: 'custom-2',
        label: 'Monitoreo de Datos',
        layout: 'split-v',
        viewIds: ['bite-messages', 'calibration-log'],
        builtin: false,
      },
    ],
  },
}
