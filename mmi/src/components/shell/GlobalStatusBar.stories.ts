import type { Meta, StoryObj } from '@storybook/vue3-vite'
import GlobalStatusBar from './GlobalStatusBar.vue'
import type { ControlAuthorityState, MaintenanceState } from '@/types/mmi'
import type { IndicatorState } from '@/types/shell'

const meta: Meta<typeof GlobalStatusBar> = {
  title: 'Shell/GlobalStatusBar',
  component: GlobalStatusBar,
}
export default meta

type Story = StoryObj<typeof meta>

const control: ControlAuthorityState = {
  mode: 'active',
  actor: 'operador-1',
  since_wall: new Date().toISOString(),
}

const indicators: IndicatorState[] = [
  { id: 'SI', state: 'ok', detail: 'Tarea recibida, esperando inicio' },
  { id: 'SR', state: 'ok', detail: 'Scan en ejecución' },
  { id: 'SD', state: 'neutral', detail: 'Sin datos de estado hace 6 s' },
  { id: 'RD', state: 'ok', detail: '3.2 Mbps' },
]

const baseArgs = {
  siteName: 'RD100S-01',
  host: '10.0.4.12',
  simulated: false,
  control,
  accessLevel: 'OP' as const,
  indicators,
  alarmWorst: 'ok' as const,
  alarmCount: 0,
}

export const Default: Story = {
  args: baseArgs,
}

export const MaintenanceMode: Story = {
  args: {
    ...baseArgs,
    accessLevel: 'MANT',
    maintenance: {
      level: 'MANT',
      actor: 'tecnico-1',
      expires_wall: new Date(Date.now() + 15 * 60 * 1000).toISOString(),
    } as MaintenanceState,
  },
}

export const SimulatedEnvironment: Story = {
  args: {
    ...baseArgs,
    simulated: true,
    siteName: 'RD100S-EMU',
  },
}

export const WithAlarmsAndNoControl: Story = {
  args: {
    ...baseArgs,
    control: null,
    alarmWorst: 'fault',
    alarmCount: 5,
    indicators: [
      { id: 'SI', state: 'fault', detail: 'Error en subsecuencia de barrido' },
      { id: 'SR', state: 'neutral', detail: 'Velocidad de antena fuera de tolerancia' },
      { id: 'SD', state: 'neutral', detail: 'Sin datos' },
      { id: 'RD', state: 'ok', detail: '1.1 Mbps' },
    ],
  },
}
