import type { Meta, StoryObj } from '@storybook/vue3-vite'
import SetSaveActions from './SetSaveActions.vue'

const meta: Meta<typeof SetSaveActions> = {
  title: 'Domain/SetSaveActions (G7)',
  component: SetSaveActions,
}
export default meta

type Story = StoryObj<typeof meta>

export const Synchronized: Story = {
  args: {
    dirty: false,
    canSave: true,
    busy: false,
  },
}

export const Modified: Story = {
  args: {
    dirty: true,
    canSave: true,
    busy: false,
  },
}

export const SaveBlocked: Story = {
  args: {
    dirty: true,
    canSave: false,
    saveBlockedReason: 'Existen parámetros con valores fuera de rango o inválidos',
    busy: false,
  },
}

export const Busy: Story = {
  args: {
    dirty: true,
    canSave: true,
    busy: true,
  },
}
