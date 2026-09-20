import type { Meta, StoryObj } from '@storybook/vue3-vite'
import MaintenanceUnlockCard from './MaintenanceUnlockCard.vue'

const meta: Meta<typeof MaintenanceUnlockCard> = {
  title: 'Domain/MaintenanceUnlockCard (A4)',
  component: MaintenanceUnlockCard,
}
export default meta

type Story = StoryObj<typeof meta>

const now = Date.now()

export const LockedOP: Story = {
  args: {
    maintenance: { level: 'OP', actor: null, since_wall: null, expires_wall: null },
    busy: false,
    error: null,
  },
}

export const LockedWithError: Story = {
  args: {
    maintenance: { level: 'OP', actor: null, since_wall: null, expires_wall: null },
    busy: false,
    error: 'POST /api/maintenance/unlock: HTTP 403 — {"detail":"contraseña de mantenimiento incorrecta"}',
  },
}

export const UnlockedMANT: Story = {
  args: {
    maintenance: {
      level: 'MANT',
      actor: 'tecnico1',
      since_wall: new Date(now - 300_000).toISOString(),
      expires_wall: new Date(now + 1_500_000).toISOString(),
    },
    busy: false,
    error: null,
  },
}

export const Busy: Story = {
  args: {
    maintenance: { level: 'OP', actor: null, since_wall: null, expires_wall: null },
    busy: true,
    error: null,
  },
}
