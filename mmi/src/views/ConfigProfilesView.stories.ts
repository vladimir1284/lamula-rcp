import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ConfigProfilesView from './ConfigProfilesView.vue'

const meta: Meta<typeof ConfigProfilesView> = {
  title: 'Views/ConfigProfilesView',
  component: ConfigProfilesView,
}

export default meta
type Story = StoryObj<typeof ConfigProfilesView>

export const Default: Story = {}
