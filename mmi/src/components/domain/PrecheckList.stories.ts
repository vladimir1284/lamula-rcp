import type { Meta, StoryObj } from '@storybook/vue3-vite'
import PrecheckList from './PrecheckList.vue'

const meta: Meta<typeof PrecheckList> = {
  title: 'Domain/PrecheckList',
  component: PrecheckList,
}
export default meta

type Story = StoryObj<typeof meta>

// C4: "botón de ejecución deshabilitado con la causa visible" -- una
// precondición por rutina (autoridad activa + campo obligatorio).
export const AllOk: Story = {
  args: {
    checks: [
      { label: 'Autoridad de control activa', ok: true },
      { label: 'warmup_timeout_s definido', ok: true },
    ],
  },
}

export const SomeFailing: Story = {
  args: {
    checks: [
      { label: 'Autoridad de control activa', ok: false },
      { label: 'warmup_timeout_s definido', ok: false },
    ],
  },
}

export const Mixed: Story = {
  args: {
    checks: [
      { label: 'Autoridad de control activa', ok: true },
      { label: 'confirm_timeout_s definido', ok: false },
    ],
  },
}
