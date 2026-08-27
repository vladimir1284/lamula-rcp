import type { Meta, StoryObj } from '@storybook/vue3-vite'
import AntennaPositionReadout from './AntennaPositionReadout.vue'
import type { AntennaPosition } from '@/types/mmi'

const meta: Meta<typeof AntennaPositionReadout> = {
  title: 'Domain/AntennaPositionReadout',
  component: AntennaPositionReadout,
}
export default meta

type Story = StoryObj<typeof meta>

const nominal: AntennaPosition = {
  az_deg: 123.45,
  el_deg: 12.3,
  az_rate_deg_s: 6.0,
  el_rate_deg_s: 0.0,
  az_valid: true,
  el_valid: true,
  az_ref_ok: true,
  el_ref_ok: true,
  az_fault: false,
  el_fault: false,
  degraded: false,
  seq: 1,
  at_us: 0,
}

export const Abbreviated: Story = { args: { antenna: nominal } }
export const WithRates: Story = { args: { antenna: nominal, showRates: true } }
export const Degraded: Story = { args: { antenna: { ...nominal, degraded: true }, showRates: true } }
export const InvalidEncoder: Story = {
  args: { antenna: { ...nominal, az_valid: false, el_valid: false }, showRates: true },
}
export const NoData: Story = { args: { antenna: null, showRates: true } }
