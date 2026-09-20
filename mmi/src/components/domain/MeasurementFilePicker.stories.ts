import type { Meta, StoryObj } from '@storybook/vue3-vite'
import MeasurementFilePicker from './MeasurementFilePicker.vue'

const meta: Meta<typeof MeasurementFilePicker> = {
  title: 'Domain/MeasurementFilePicker',
  component: MeasurementFilePicker,
  args: {
    loadLabel: 'Cargar archivo',
    saveLabel: 'Guardar conjunto',
    canSave: true,
  },
}
export default meta

type Story = StoryObj<typeof meta>

export const Empty: Story = {}

export const Loaded: Story = {
  args: {
    loadedFileName: 'bite_history_2026-09-20.json',
    totalRecords: 14,
  },
}
