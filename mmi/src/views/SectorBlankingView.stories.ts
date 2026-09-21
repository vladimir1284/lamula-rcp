import type { Meta, StoryObj } from '@storybook/vue3-vite'
import SectorBlankingView from './SectorBlankingView.vue'

const meta: Meta<typeof SectorBlankingView> = {
  title: 'Views/SectorBlankingView (C5)',
  component: SectorBlankingView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
