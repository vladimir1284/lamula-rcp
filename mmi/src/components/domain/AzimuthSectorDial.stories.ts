import type { Meta, StoryObj } from '@storybook/vue3-vite'
import AzimuthSectorDial from './AzimuthSectorDial.vue'
import type { BlankingSector } from '@/types/mmi'

const sampleSectors: BlankingSector[] = [
  { in_use: true, az_start_deg: 0, az_end_deg: 45, el_start_deg: -90, el_end_deg: 90 },
  { in_use: true, az_start_deg: 90, az_end_deg: 135, el_start_deg: -10, el_end_deg: 30 },
  { in_use: false, az_start_deg: 180, az_end_deg: 225, el_start_deg: -90, el_end_deg: 90 },
  { in_use: true, az_start_deg: 270, az_end_deg: 315, el_start_deg: 0, el_end_deg: 45 },
]

const meta: Meta<typeof AzimuthSectorDial> = {
  title: 'Domain/AzimuthSectorDial (C5)',
  component: AzimuthSectorDial,
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    sectors: sampleSectors,
    selectedIndex: 0,
    enabled: true,
  },
}

export const Disabled: Story = {
  args: {
    sectors: sampleSectors,
    selectedIndex: null,
    enabled: false,
  },
}
