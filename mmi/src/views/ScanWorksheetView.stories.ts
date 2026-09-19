import type { Meta, StoryObj } from '@storybook/vue3-vite'
import ScanWorksheetView from './ScanWorksheetView.vue'

// C3. Excepción del doble de gateway: el CRUD del worksheet
// (fetch/POST/DELETE a /api/scan/worksheet) no pasa por useGateway(), es
// fetch directo -- en Storybook falla igual que sin backend real ("Failed
// to fetch"), mismo camino ya manejado por la vista. El formulario de
// "nuevo corte" y el panel "Ejecutar" (que sí usan el doble, vía
// runControlJob) se ven completos.
const meta: Meta<typeof ScanWorksheetView> = {
  title: 'Views/ScanWorksheetView (C3)',
  component: ScanWorksheetView,
  parameters: { layout: 'fullscreen' },
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {}
