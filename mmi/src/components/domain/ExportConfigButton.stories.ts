import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ExportConfigButton from './ExportConfigButton.vue'

const meta: Meta<typeof ExportConfigButton> = {
  title: 'Domain/ExportConfigButton (E1)',
  component: ExportConfigButton,
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {},
}

export const CustomConfig: Story = {
  args: {
    filename: 'custom-dsp-config.json',
    configData: {
      dsp_config_version: 'v1.3',
      exported_at: '2025-01-15T12:00:00Z',
      source: 'E1 — DSP Setup Hub',
      e2_processing_options: {
        spectral_window: 'Hamming',
      },
    },
  },
}
