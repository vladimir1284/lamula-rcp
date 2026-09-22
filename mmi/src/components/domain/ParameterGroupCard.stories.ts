import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ParameterGroupCard from './ParameterGroupCard.vue'

const meta: Meta<typeof ParameterGroupCard> = {
  title: 'Domain/ParameterGroupCard (G7)',
  component: ParameterGroupCard,
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    title: 'Parámetros de la Antena',
    description: 'Ganancia y anchos de haz vertical y horizontal (RAVIS §14)',
  },
  render: (args) => ({
    components: { ParameterGroupCard },
    setup() {
      return { args }
    },
    template: `
      <ParameterGroupCard v-bind="args">
        <div class="text-xs text-muted-foreground">
          Contenido de prueba dentro de la tarjeta de grupo de parámetros.
        </div>
      </ParameterGroupCard>
    `,
  }),
}

export const Minimal: Story = {
  args: {
    title: 'Pérdidas de Sistema',
  },
  render: (args) => ({
    components: { ParameterGroupCard },
    setup() {
      return { args }
    },
    template: `
      <ParameterGroupCard v-bind="args">
        <div class="text-xs text-muted-foreground">
          Sin descripción en el encabezado.
        </div>
      </ParameterGroupCard>
    `,
  }),
}
