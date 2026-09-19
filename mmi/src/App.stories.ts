import type { Meta, StoryObj } from '@storybook/vue3-vite'
import App from './App.vue'

// Ensamblaje real completo: App.vue tal cual corre en producción (mismo
// catálogo/presets/indicadores de paso 3), con useGateway() sustituido por
// su doble de Storybook (ver useGateway.mock.ts + el alias en
// .storybook/main.ts) en vez del RCP real. A diferencia de
// Shell/AppShell.stories.ts (que prueba sólo la mecánica del mosaico con
// vistas de relleno), esta historia es la app de verdad -- si algo se ve
// mal aquí, se ve mal en producción.
const meta: Meta<typeof App> = {
  title: 'App/App (real, gateway mockeado)',
  component: App,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
