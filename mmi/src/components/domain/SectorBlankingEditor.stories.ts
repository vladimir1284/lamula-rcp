import type { Meta, StoryObj } from '@storybook/vue3-vite'
import SectorBlankingEditor from './SectorBlankingEditor.vue'
import type { SectorBlankingProfile } from '@/types/mmi'

const sampleProfile: SectorBlankingProfile = {
  enabled: true,
  sectors: [
    { in_use: true, az_start_deg: 0, az_end_deg: 45, el_start_deg: -90, el_end_deg: 90 },
    { in_use: true, az_start_deg: 90, az_end_deg: 135, el_start_deg: -10, el_end_deg: 30 },
    { in_use: false, az_start_deg: 180, az_end_deg: 225, el_start_deg: -90, el_end_deg: 90 },
    { in_use: false, az_start_deg: 0, az_end_deg: 45, el_start_deg: -90, el_end_deg: 90 },
    { in_use: false, az_start_deg: 0, az_end_deg: 45, el_start_deg: -90, el_end_deg: 90 },
    { in_use: false, az_start_deg: 0, az_end_deg: 45, el_start_deg: -90, el_end_deg: 90 },
    { in_use: false, az_start_deg: 0, az_end_deg: 45, el_start_deg: -90, el_end_deg: 90 },
    { in_use: false, az_start_deg: 0, az_end_deg: 45, el_start_deg: -90, el_end_deg: 90 },
  ],
}

const invalidProfile: SectorBlankingProfile = {
  enabled: true,
  sectors: [
    { in_use: true, az_start_deg: 400, az_end_deg: 45, el_start_deg: 50, el_end_deg: 10 },
    { in_use: false, az_start_deg: 0, az_end_deg: 45, el_start_deg: -90, el_end_deg: 90 },
  ],
}

const meta: Meta<typeof SectorBlankingEditor> = {
  title: 'Domain/SectorBlankingEditor (C5)',
  component: SectorBlankingEditor,
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    profile: sampleProfile,
    busy: false,
    selectedIndex: 0,
  },
}

export const ValidationError: Story = {
  args: {
    profile: invalidProfile,
    busy: false,
    selectedIndex: 0,
  },
}
