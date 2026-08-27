import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ControlAuthorityCard from './ControlAuthorityCard.vue'

const meta: Meta<typeof ControlAuthorityCard> = {
  title: 'Domain/ControlAuthorityCard',
  component: ControlAuthorityCard,
}
export default meta

type Story = StoryObj<typeof meta>

const activeControl = { mode: 'active' as const, actor: 'operador', since_wall: new Date().toISOString() }
const passiveControl = { mode: 'passive' as const, actor: 'operador', since_wall: new Date().toISOString() }

export const ReadOnlyActive: Story = { args: { control: activeControl } }
export const ReadOnlyPassive: Story = { args: { control: passiveControl } }
export const ReadOnlyNoData: Story = { args: { control: null } }
export const Editable: Story = { args: { control: passiveControl, editable: true, actor: 'operador' } }
export const EditableBusy: Story = { args: { control: passiveControl, editable: true, actor: 'operador', busy: true } }
export const EditableNoData: Story = { args: { control: null, editable: true, actor: '' } }
