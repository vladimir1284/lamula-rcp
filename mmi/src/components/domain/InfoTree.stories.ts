import type { Meta, StoryObj } from '@storybook/vue3-vite'
import InfoTree, { type TreeNode } from './InfoTree.vue'

const sampleTreeData: TreeNode[] = [
  {
    id: 'rcp',
    label: 'RCP (Radar Control Processor)',
    children: [
      {
        id: 'rcp-config',
        label: 'Configuración & Estado',
        items: [
          { key: 'version', label: 'Versión del RCP', value: '1.2.0' },
          { key: 'started', label: 'Arrancado', value: '2026-09-20 10:00:00' },
          { key: 'authority_mode', label: 'Modo de Control', value: 'local' },
          { key: 'authority_actor', label: 'Actor de Control', value: 'operator' },
        ],
      },
    ],
  },
  {
    id: 'dsp',
    label: 'Contrato DSP (LAMULA DSP)',
    children: [
      {
        id: 'dsp-contract',
        label: 'Ancla y Procedencia de Contrato',
        items: [
          { key: 'dsp_ver', label: 'Versión del Contrato', value: 'v1.3' },
          { key: 'dsp_commit', label: 'Commit del Contrato', value: '6a09656' },
        ],
      },
    ],
  },
  {
    id: 'radar',
    label: 'Radar & Clientes',
    children: [
      {
        id: 'radar-components',
        label: 'Componentes & Subsistemas',
        gap: 'sin backend de estado por componente',
        items: [
          { key: 'comp_status', label: 'Estado Subsistemas', value: 'Pendiente de telemetría detallada', gap: 'sin backend' },
        ],
      },
    ],
  },
]

const meta: Meta<typeof InfoTree> = {
  title: 'Domain/InfoTree (A7)',
  component: InfoTree,
}
export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    nodes: sampleTreeData,
  },
}

export const MinimalWithGap: Story = {
  args: {
    nodes: [
      {
        id: 'acu',
        label: 'ACU (Antenna Control Unit)',
        gap: 'módulos de ACU sin backend',
        children: [
          {
            id: 'acu-modules',
            label: 'Module Info',
            gap: 'sin backend ACU',
            items: [
              { key: 'acu_info', label: 'Módulos ACU', value: 'No disponible', gap: 'sin backend' },
            ],
          },
        ],
      },
    ],
  },
}
