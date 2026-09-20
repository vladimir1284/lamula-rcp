// Doble de useGateway.ts para Storybook -- SOLO se usa ahí (ver el alias en
// .storybook/main.ts, que redirige el import exacto '@/composables/useGateway'
// a este fichero al construir Storybook; la app real y `vue-tsc` siguen
// resolviendo el módulo de verdad vía tsconfig paths).
//
// Motivo: paso 3 (docs/diseno/inventario-ui.md) cableó las vistas P0 de
// operación directo a useGateway() -- fetch/WS reales. Sin este doble, esas
// vistas sólo se pueden "ver" en Storybook mostrando errores de red
// (ERR_CONNECTION_REFUSED), que es exactamente lo que NO sirve para iterar
// sobre diseño visual. Este doble no reemplaza un backend real: da datos de
// ejemplo estables y funciones que responden localmente, para que cada
// vista se vea con contenido realista sin depender de que el RCP esté
// corriendo.
//
// Excepción conocida: ScanWorksheetView hace `fetch(GATEWAY_HTTP + ...)`
// directo para el CRUD del worksheet (no pasa por useGateway) -- eso sigue
// fallando en Storybook igual que sin backend real (mismo camino de error ya
// manejado en la vista). No se mockeó `fetch` global (MSW u otro) -- fuera
// de alcance de este paso.
import { computed, ref, shallowRef } from 'vue'
import type {
  AntennaMessage,
  AntennaStepConfig,
  BiteFaultSummary,
  ControlAuthorityState,
  ControlJobStatusResponse,
  DspStreamStatus,
  MaintenanceState,
  PowerMeasurementLimits,
  PowerMonitorSnapshot,
  ProcessMonitorSnapshot,
  RoutineResult,
  SetControlModeRequest,
  SystemInfo,
  SystemStatusSnapshot,
  TrendSeries,
  TrendStatus,
  UnlockMaintenanceRequest,
  WsMessage,
} from '@/types/mmi'
import type { ScanCutResult } from '@/types/scan'
import type { LampState } from '@/types/shell'
import type { SessionInfo } from './useGateway'

export const GATEWAY_HTTP = 'http://mock.invalid:8000'

const now = Date.now()
const iso = (msAgo: number) => new Date(now - msAgo).toISOString()

const status = ref<'CONNECTING' | 'OPEN' | 'CLOSED'>('OPEN')

const control = shallowRef<ControlAuthorityState | null>({
  mode: 'active',
  actor: 'operador-demo',
  since_wall: iso(45 * 60_000),
})

const maintenance = shallowRef<MaintenanceState | null>({
  level: 'OP',
  actor: null,
  since_wall: null,
  expires_wall: null,
})

const stepConfig = ref<AntennaStepConfig>({
  azimuth_step_deg: 1.0,
  elevation_step_deg: 1.0,
})

const trendRunning = ref(false)
const trendChannels = ref<string[]>(['tx.mps_output_voltage_sample', 'tx.fps_output_voltage_sample'])
const trendStartedAt = ref<string | null>(null)
const trendData = ref<TrendSeries[]>([])
const powerLimits = ref<PowerMeasurementLimits | null>(null)
const powerRadiating = ref(false)

const antenna = shallowRef<AntennaMessage['position'] | null>({
  az_deg: 123.4,
  el_deg: 12.3,
  az_rate_deg_s: 6,
  el_rate_deg_s: 0,
  az_valid: true,
  el_valid: true,
  az_ref_ok: true,
  el_ref_ok: true,
  az_fault: false,
  el_fault: false,
  degraded: false,
  seq: 4821,
  at_us: now * 1000,
})

const dsp = shallowRef<DspStreamStatus | null>({
  connected: true,
  radials_received: 48213,
  last_volume_number: 12,
  last_elevation_number: 3,
  last_radial_status: 'intermediate',
  last_radial_at_wall: iso(0),
})

// A6 SD/RD "stale" (D-14, docs/alcance/decisiones.md): el doble no simula el
// paso del tiempo, así que se fija en "fresco" -- las tres lecturas de
// LampState de A6 ya se ven en AppShell.stories.ts con su propio array
// `indicators` fijo, sin pasar por useGateway.
const statusChannelStale = computed(() => false)
const dspDataStale = computed(() => false)
const dspRadialRate = shallowRef<number | null>(212.5)

const sessionInfo = shallowRef<SessionInfo | null>({
  rcp_version: 'v0.1.0-mock',
  started_at_wall: iso(2 * 3_600_000),
})

const systemInfo = shallowRef<SystemInfo | null>({
  rcp_version: 'v0.1.0-mock',
  dsp_contract_version: 'v1.3',
  dsp_contract_commit: '6a09656',
  dsp_contract_commit_date: '2026-09-16',
  connected_clients: 2,
})

const biteFaults = ref<Map<string, BiteFaultSummary>>(
  new Map([
    ['tx.interlock_ok_status', { signal_id: 'tx.interlock_ok_status', detail: 'interlock abierto', since_wall: iso(3 * 60_000) }],
  ]),
)

const halConnected = shallowRef<boolean | null>(true)
const lastCloseReason = shallowRef<string | null>(null)

// A2 Connection/Login: doble interactivo de open/close para poder ver los
// 3 estados reales (CONNECTING/OPEN/CLOSED) en Storybook sin un WS real.
function close() {
  status.value = 'CLOSED'
  lastCloseReason.value = 'cerrado por el operador (mock)'
}
function open() {
  status.value = 'CONNECTING'
  lastCloseReason.value = null
  setTimeout(() => {
    status.value = 'OPEN'
  }, 500)
}

// Historial mixto (eventos de operador + transiciones BiTE) -- mismo `type`
// discriminado que consume EventLogView/BiteMessagesView del stream real.
const messages = ref<WsMessage[]>([
  { type: 'session', rcp_version: 'v0.1.0-mock', started_at_wall: iso(2 * 3_600_000), control: control.value! },
  { type: 'event', seq: 1, at_wall: iso(40 * 60_000), kind: 'control_mode_changed', actor: 'operador-demo', payload: { mode: 'active' } },
  { type: 'bite_event', signal_id: 'ant.servo_ok_status', transition: 'fault', detail: 'servo sin respuesta', at_wall: iso(20 * 60_000) },
  { type: 'event', seq: 2, at_wall: iso(19 * 60_000), kind: 'general-power-on_started', actor: 'operador-demo', payload: {} },
  { type: 'event', seq: 3, at_wall: iso(18 * 60_000), kind: 'general-power-on_failed', actor: 'operador-demo', payload: { reason: 'precondición no cumplida' } },
  { type: 'bite_event', signal_id: 'ant.servo_ok_status', transition: 'cleared', detail: 'servo sin respuesta', at_wall: iso(10 * 60_000) },
  { type: 'event', seq: 4, at_wall: iso(9 * 60_000), kind: 'antenna-positioning_cancelled', actor: 'operador-demo', payload: {} },
  { type: 'bite_event', signal_id: 'tx.interlock_ok_status', transition: 'fault', detail: 'interlock abierto', at_wall: iso(3 * 60_000) },
])

const alarmAckedAt = ref<string | null>(null)
function acknowledgeAlarm() {
  alarmAckedAt.value = new Date().toISOString()
}
const alarmWorst = computed<LampState>(() => {
  const acked = alarmAckedAt.value
  for (const f of biteFaults.value.values()) {
    if (!acked || f.since_wall > acked) return 'fault'
  }
  return 'ok'
})
const alarmCount = computed(() => biteFaults.value.size)

async function fetchStatus(): Promise<SystemStatusSnapshot> {
  if (!control.value || !maintenance.value) {
    throw new Error('mock missing initial state')
  }
  return {
    control: control.value,
    maintenance: maintenance.value,
    hal_connected: halConnected.value ?? false,
    antenna: antenna.value,
    dsp: dsp.value,
    active_bite_faults: [...biteFaults.value.values()],
  }
}

async function fetchSystemInfo(): Promise<SystemInfo> {
  return systemInfo.value!
}

async function setControlMode(req: SetControlModeRequest): Promise<ControlAuthorityState> {
  control.value = { mode: req.mode, actor: req.actor, since_wall: new Date().toISOString() }
  return control.value
}

async function unlockMaintenance(req: UnlockMaintenanceRequest): Promise<MaintenanceState> {
  await delay(300)
  if (req.password !== 'mant1234') {
    throw new Error('POST /api/maintenance/unlock: HTTP 403 — {"detail":"contraseña de mantenimiento incorrecta"}')
  }
  const nowMs = Date.now()
  const expIso = new Date(nowMs + req.duration_s * 1000).toISOString()
  maintenance.value = {
    level: 'MANT',
    actor: req.actor,
    since_wall: new Date(nowMs).toISOString(),
    expires_wall: expIso,
  }
  return maintenance.value
}

async function fetchStepConfig(): Promise<AntennaStepConfig> {
  await delay(100)
  return { ...stepConfig.value }
}

async function setStepConfig(config: AntennaStepConfig): Promise<AntennaStepConfig> {
  await delay(100)
  if (config.azimuth_step_deg < 0.1 || config.azimuth_step_deg > 1.0 || config.elevation_step_deg < 0.1 || config.elevation_step_deg > 1.0) {
    throw new Error('POST /api/antenna/step-config: HTTP 422 — Unprocessable Entity')
  }
  stepConfig.value = { ...config }
  return { ...stepConfig.value }
}

async function fetchProcessMonitor(): Promise<ProcessMonitorSnapshot> {
  await delay(100)
  return {
    process: {
      pid: 12345,
      name: 'uvicorn',
      priority: 0,
      status: 'running',
      cpu_percent: 1.2,
      memory_mb: 42.8,
    },
    tasks: [
      { name: 'Task-1 (_bite_poll_loop)', state: 'pending' },
      { name: 'Task-2 (ws_endpoint)', state: 'pending' },
      { name: 'Task-3 (antenna_positioning)', state: 'done' },
    ],
  }
}

async function fetchTrendChannels(): Promise<string[]> {
  await delay(50)
  return [
    'tx.mps_output_voltage_sample',
    'tx.fps_output_voltage_sample',
    'tx.tx_peak_power_sample',
    'ant.az_motor_current_sample',
    'ant.el_motor_current_sample',
  ]
}

async function fetchTrendStatus(): Promise<TrendStatus> {
  await delay(50)
  return {
    running: trendRunning.value,
    started_at_wall: trendStartedAt.value,
    signal_ids: trendChannels.value,
  }
}

async function startTrend(signalIds: string[]): Promise<TrendStatus> {
  await delay(50)
  if (trendRunning.value) {
    throw new Error('POST /api/trend/start: HTTP 409 — muestreo ya en ejecución')
  }
  trendChannels.value = signalIds
  trendStartedAt.value = new Date().toISOString()
  trendRunning.value = true
  const nowMs = Date.now()
  trendData.value = signalIds.map((sig, idx) => ({
    signal_id: sig,
    samples: Array.from({ length: 30 }, (_, i) => ({
      at_wall: new Date(nowMs - (30 - i) * 1000).toISOString(),
      value: i === 15 ? null : 100 + idx * 20 + Math.sin(i / 2) * 10,
    })),
  }))
  return fetchTrendStatus()
}

async function stopTrend(): Promise<TrendStatus> {
  await delay(50)
  trendRunning.value = false
  return fetchTrendStatus()
}

async function continueTrend(): Promise<TrendStatus> {
  await delay(50)
  trendRunning.value = true
  return fetchTrendStatus()
}

async function clearTrend(): Promise<TrendStatus> {
  await delay(50)
  trendRunning.value = false
  trendData.value = []
  trendChannels.value = []
  trendStartedAt.value = null
  return fetchTrendStatus()
}

async function fetchTrendData(): Promise<TrendSeries[]> {
  await delay(50)
  if (trendRunning.value && trendData.value.length > 0) {
    const nowIso = new Date().toISOString()
    trendData.value.forEach((series) => {
      const lastSample = series.samples.length > 0 ? series.samples[series.samples.length - 1] : undefined
      const lastVal = (lastSample && lastSample.value !== null) ? lastSample.value : 100
      series.samples.push({
        at_wall: nowIso,
        value: lastVal + (Math.random() - 0.5) * 2,
      })
      if (series.samples.length > 300) series.samples.shift()
    })
  }
  return trendData.value
}

async function fetchPowerMonitor(): Promise<PowerMonitorSnapshot> {
  await delay(80)
  const forward = 210 + Math.sin(Date.now() / 3000) * 5
  const reverse = 3 + Math.random()
  const ratio = Math.sqrt(reverse / forward)
  return {
    forward_power_kw: forward,
    reverse_power_kw: reverse,
    vswr: Math.round(((1 + ratio) / (1 - ratio)) * 1000) / 1000,
    bus_ok: true,
    radiating: powerRadiating.value,
    limits: powerLimits.value,
  }
}

async function setPowerLimits(limits: PowerMeasurementLimits): Promise<PowerMeasurementLimits> {
  await delay(80)
  powerLimits.value = { ...limits }
  return { ...powerLimits.value }
}

async function savePowerLimits(): Promise<PowerMeasurementLimits> {
  await delay(150)
  if (powerLimits.value === null) {
    throw new Error('POST /api/power-monitor/limits/save: HTTP 409 — no hay limites para guardar -- use Set primero')
  }
  if (powerRadiating.value) {
    throw new Error(
      'POST /api/power-monitor/limits/save: HTTP 409 — no se puede guardar mientras el radar esta radiando',
    )
  }
  return { ...powerLimits.value }
}

async function lockMaintenance(): Promise<MaintenanceState> {
  await delay(300)
  maintenance.value = {
    level: 'OP',
    actor: null,
    since_wall: null,
    expires_wall: null,
  }
  return maintenance.value
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

// Simula "202 + sondeo" con un único delay -- suficiente para que
// JobActionPanel muestre su estado `busy` antes de resolver, sin tener que
// reimplementar el ciclo de sondeo real por job_id.
async function runControlJob<T>(path: string, _body?: unknown, onJobId?: (jobId: string) => void): Promise<T> {
  onJobId?.(`mock-job-${Date.now()}`)
  await delay(600)
  if (path.includes('/scan/worksheet/')) {
    const result: ScanCutResult = {
      outcome: 'success',
      steps: [{ signal_id: 'ant.az_position_ok_status', ok: true, detail: 'ok (mock)' }],
      at_us: Date.now() * 1000,
    }
    return result as T
  }
  const routine = path.split('/').pop() ?? 'routine'
  const result: RoutineResult = {
    routine,
    outcome: 'success',
    steps: [{ signal_id: 'sys.standby_system_ok_status', ok: true, detail: 'ok (mock)' }],
    at_us: Date.now() * 1000,
  }
  return result as T
}

async function cancelControlJob(jobId: string): Promise<ControlJobStatusResponse> {
  return { job_id: jobId, routine: 'mock', status: 'done', result: null, error: null }
}

function send() {
  // No hay socket real que mandar nada -- no-op deliberado.
}

export function useGateway() {
  return {
    status,
    lastCloseReason,
    messages,
    control,
    maintenance,
    antenna,
    dsp,
    sessionInfo,
    systemInfo,
    biteFaults,
    halConnected,
    statusChannelStale,
    dspDataStale,
    dspRadialRate,
    alarmAckedAt,
    alarmWorst,
    alarmCount,
    acknowledgeAlarm,
    fetchStatus,
    fetchSystemInfo,
    setControlMode,
    unlockMaintenance,
    lockMaintenance,
    fetchStepConfig,
    setStepConfig,
    fetchProcessMonitor,
    fetchTrendChannels,
    fetchTrendStatus,
    startTrend,
    stopTrend,
    continueTrend,
    clearTrend,
    fetchTrendData,
    fetchPowerMonitor,
    setPowerLimits,
    savePowerLimits,
    runControlJob,
    cancelControlJob,
    send,
    open,
    close,
  }
}
