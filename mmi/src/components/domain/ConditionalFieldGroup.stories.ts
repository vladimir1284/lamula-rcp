import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ConditionalFieldGroup from './ConditionalFieldGroup.vue'

const meta: Meta<typeof ConditionalFieldGroup> = {
  title: 'Domain/ConditionalFieldGroup (E4/E6)',
  component: ConditionalFieldGroup,
}
export default meta

type Story = StoryObj<typeof meta>

export const Supported: Story = {
  args: {
    title: 'Filtro Gaussiano (#5)',
    description: 'Ajuste de ancho de clutter en modelo gaussiano GMAP',
    supported: true,
  },
  render: (args) => ({
    components: { ConditionalFieldGroup },
    setup() {
      return { args }
    },
    template: `
      <ConditionalFieldGroup v-bind="args">
        <div class="text-xs text-muted-foreground">
          Campo soportado por el backend activo.
        </div>
      </ConditionalFieldGroup>
    `,
  }),
}

export const UnsupportedWithBadge: Story = {
  args: {
    title: 'Filtro Fijo (#1)',
    description: 'Filtro de muesca (Notch) de ancho fijo',
    supported: false,
    badgeLabel: 'Sin backend',
  },
  render: (args) => ({
    components: { ConditionalFieldGroup },
    setup() {
      return { args }
    },
    template: `
      <ConditionalFieldGroup v-bind="args">
        <div class="text-xs text-muted-foreground">
          Parámetros maquetados pero no expuestos por el contrato actual.
        </div>
      </ConditionalFieldGroup>
    `,
  }),
}
