import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ConfigDiffView from './ConfigDiffView.vue'
import type { RcpConfigProfile } from '@/types/mmi'

const sampleCurrent: RcpConfigProfile = {
  power_limits: { forward_limit_kw: 250, reverse_limit_kw: 15, vswr_limit: 1.5 },
  antenna_step_config: { azimuth_step_deg: 0.5, elevation_step_deg: 1.0 },
  sector_blanking: {
    enabled: true,
    sectors: [{ in_use: true, az_start_deg: 45, az_end_deg: 90, el_start_deg: 0, el_end_deg: 30 }],
  },
  thresholds: { log_threshold_db: 1.2, csr_threshold_db: -18.0, sqi_threshold: 0.35, speckle_remover: true },
  clutter_filter: { doppler_filter_id: 2, doppler_type_db: '30', fft_filter_enabled: true, statistical_filter_enabled: false },
}

const sampleSaved: RcpConfigProfile = {
  power_limits: { forward_limit_kw: 250, reverse_limit_kw: 15, vswr_limit: 1.5 },
  antenna_step_config: { azimuth_step_deg: 1.0, elevation_step_deg: 1.0 },
  sector_blanking: {
    enabled: false,
    sectors: [],
  },
  thresholds: { log_threshold_db: 1.0, csr_threshold_db: -18.0, sqi_threshold: 0.3, speckle_remover: true },
  clutter_filter: { doppler_filter_id: 1, doppler_type_db: 'default', fft_filter_enabled: false, statistical_filter_enabled: false },
}

const meta: Meta<typeof ConfigDiffView> = {
  title: 'Domain/ConfigDiffView',
  component: ConfigDiffView,
}

export default meta
type Story = StoryObj<typeof ConfigDiffView>

export const WithDifferences: Story = {
  args: {
    current: sampleCurrent,
    saved: sampleSaved,
  },
}

export const Synchronized: Story = {
  args: {
    current: sampleSaved,
    saved: sampleSaved,
  },
}
