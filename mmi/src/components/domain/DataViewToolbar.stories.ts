import type { Meta, StoryObj } from '@storybook/vue3-vite'
import DataViewToolbar from './DataViewToolbar.vue'

const meta: Meta<typeof DataViewToolbar> = {
  title: 'Domain/DataViewToolbar',
  component: DataViewToolbar,
  args: {
    dataType: 'reflectivity',
    resolution: 64,
    zoom: 1,
    source: 'radar',
  },
}
export default meta

type Story = StoryObj<typeof meta>

export const Ascope: Story = {
  args: { showRefreshRate: true, showAxisUnit: true, refreshRate: 1, axisUnit: 'km' },
}

export const PpiOrRhi: Story = {}
