import type { Meta, StoryObj } from '@storybook/vue3-vite'
import { ref } from 'vue'
import TernaryOverrideField from './TernaryOverrideField.vue'

const meta: Meta<typeof TernaryOverrideField> = {
  title: 'Domain/TernaryOverrideField (E2)',
  component: TernaryOverrideField,
}
export default meta

type Story = StoryObj<typeof meta>

export const Interactive: Story = {
  args: {
    label: 'R2 Processing',
    description: 'Calculo preciso R0, R1, R2 de ancho espectral (Never/User/Always)',
    supported: false,
  },
  render: (args) => ({
    components: { TernaryOverrideField },
    setup() {
      const val = ref<'never' | 'user' | 'always'>('user')
      return { args, val }
    },
    template: `
      <div class="p-4 max-w-md bg-card rounded border border-border">
        <TernaryOverrideField
          v-bind="args"
          v-model="val"
        />
        <div class="mt-2 text-xs text-muted-foreground font-mono">
          Selected value: {{ val }}
        </div>
      </div>
    `,
  }),
}

export const SupportedMode: Story = {
  args: {
    label: 'Clutter Microsuppression',
    description: 'Supresión de micro-clutter en la densidad de potencia',
    supported: true,
  },
  render: (args) => ({
    components: { TernaryOverrideField },
    setup() {
      const val = ref<'never' | 'user' | 'always'>('never')
      return { args, val }
    },
    template: `
      <div class="p-4 max-w-md bg-card rounded border border-border">
        <TernaryOverrideField
          v-bind="args"
          v-model="val"
        />
      </div>
    `,
  }),
}
