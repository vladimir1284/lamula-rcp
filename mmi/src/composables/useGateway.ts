// Cliente del gateway RCP<->MMI (src/adapters/gateway) -- REST + WS sobre el
// sobre ya congelado en core/contracts/mmi.py (ver src/types/mmi.ts).
//
// PEND: URLs fijas a localhost -- no hay todavia empaquetado/despliegue
// decidido para la MMI (D-09 solo cubre el backend); revisar cuando exista.
//
// Singleton deliberado (paso 3, docs/diseno/inventario-ui.md): antes de
// AppShell, solo una vista (una ruta) estaba montada a la vez, así que cada
// `useGateway()` de fábrica abría su propio WebSocket sin problema. El
// mosaico monta hasta 4 vistas a la vez -- sin singleton, cada panel abriría
// una conexión WS y un fetchStatus() independientes, y biteFaults/control
// quedarían desincronizados entre paneles. Todo el estado reactivo y la
// conexión WS se crean una sola vez, a nivel de módulo; `useGateway()` sólo
// devuelve las mismas referencias.
import { useWebSocket } from '@vueuse/core'
import { computed, ref, shallowRef } from 'vue'
import type {
  AntennaMessage,
  AntennaStepConfig,
  BiteFaultSummary,
  CalibrationLogEntry,
  ClutterFilterSettings,
  ControlAuthorityState,
  ControlJobAccepted,
  ControlJobStatusResponse,
  DspInternalStatusSnapshot,
  DspResetCountersResponse,
  DspStreamStatus,
  MaintenanceState,
  MeasuredRadarConstant,
  PowerMeasurementLimits,
  PowerMonitorSnapshot,
  ProcessingOptionsSettings,
  ProcessMonitorSnapshot,
  RadarConstantParameters,
  RadarConstantSnapshot,
  RcpConfigProfile,
  SectorBlankingProfile,
  SetControlModeRequest,
  SystemInfo,
  SystemStatusSnapshot,
  TrendSeries,
  TrendStatus,
  TriggerSetupPwSettings,
  UnlockMaintenanceRequest,
  WsMessage,
  ZeroCheckSnapshot,
} from '@/types/mmi'
import type { ScanCut } from '@/types/scan'
import { STALE_TIMEOUT_MS } from '@/types/shell'
import type { LampState } from '@/types/shell'

export interface SessionInfo {
  rcp_version: string
  started_at_wall: string
}

export const GATEWAY_HTTP = 'http://127.0.0.1:8000'
const GATEWAY_WS = 'ws://127.0.0.1:8000/ws'

const MAX_LOG = 200

const messages = ref<WsMessage[]>([])
const control = shallowRef<ControlAuthorityState | null>(null)
const maintenance = shallowRef<MaintenanceState | null>(null)
const antenna = shallowRef<AntennaMessage['position'] | null>(null)
const dsp = shallowRef<DspStreamStatus | null>(null)
const sessionInfo = shallowRef<SessionInfo | null>(null)
const systemInfo = shallowRef<SystemInfo | null>(null)
// clave: signal_id -- mismo dato que app.state.bite_since_wall del lado del gateway,
// reconstruido aca a partir del snapshot inicial + BiteEventMessage en vivo.
const biteFaults = ref<Map<string, BiteFaultSummary>>(new Map())
// hal_connected llega en cada /api/status y ahora tambien por StatusMessage
// (WS, ~1 Hz) -- se guarda aparte para que A6/A1 (indicadores SD/RD) lo
// puedan leer de forma reactiva sin que cada vista tenga que llamar
// fetchStatus() y desempacarlo ella misma.
const halConnected = shallowRef<boolean | null>(null)

// A6 SD/RD "stale" (D-14, docs/alcance/decisiones.md): medido contra
// Date.now() del propio navegador al momento de RECIBIR cada dato, nunca
// contra at_wall del servidor -- AGENTS.md "dos clocks", no hay que asumir
// relojes sincronizados entre gateway y MMI.
const lastStatusMessageAt = shallowRef<number | null>(null)
const lastRadialSample = shallowRef<{ count: number; at: number } | null>(null)
const lastRadialChangeAt = shallowRef<number | null>(null)
const dspRadialRate = shallowRef<number | null>(null)
// Tick de 1 s para que los computed de abajo se re-evaluen aunque no llegue
// ningun mensaje nuevo -- si el canal muere del todo, sin esto el estado
// quedaria congelado en el ultimo valor en vez de pasar a stale.
const nowTick = shallowRef(Date.now())

// `SD` cae en stale si StatusMessage deja de llegar -- el propio silencio es
// la señal (ver StatusMessage en core/contracts/mmi.py), no hace falta un
// campo de servidor aparte.
const statusChannelStale = computed(() => {
  if (lastStatusMessageAt.value === null) return false
  return nowTick.value - lastStatusMessageAt.value > STALE_TIMEOUT_MS
})

// `RD` cae en stale si el emisor sigue conectado (TCP) pero el contador de
// radiales no avanzo hace mas de STALE_TIMEOUT_MS -- distinto de `fault`
// (sin conexion), que ya cubre dsp.connected === false.
const dspDataStale = computed(() => {
  if (!dsp.value?.connected) return false
  if (lastRadialChangeAt.value === null) return false
  return nowTick.value - lastRadialChangeAt.value > STALE_TIMEOUT_MS
})

// A2 Connection/Login (docs/diseno/inventario-ui.md): motivo del último
// cierre/fallo del WS, para mostrar un error legible en vez de solo
// "CLOSED". `CloseEvent.reason` suele venir vacío en cierres de red (no es
// un cierre de protocolo), así que esto es best-effort, no garantizado.
const lastCloseReason = shallowRef<string | null>(null)

// A6/B8: "silenciar/reconocer" (docs/diseno/inventario-ui.md, B8) -- reconocer
// no borra las fallas activas, sólo apaga el semáforo hasta la PRÓXIMA falla
// nueva. alarmAckedAt es la marca de tiempo del último reconocimiento; toda
// falla con since_wall posterior vuelve a encender el semáforo aunque se haya
// reconocido antes. Vive aquí (no en BiteMessagesView) porque B8 exige estar
// sincronizado con el resumen de alarma del Control Center (A1/A6).
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
  const res = await fetch(`${GATEWAY_HTTP}/api/status`)
  if (!res.ok) throw new Error(`GET /api/status: HTTP ${res.status}`)
  const snapshot = (await res.json()) as SystemStatusSnapshot
  control.value = snapshot.control
  maintenance.value = snapshot.maintenance
  antenna.value = snapshot.antenna
  dsp.value = snapshot.dsp
  halConnected.value = snapshot.hal_connected
  biteFaults.value = new Map(snapshot.active_bite_faults.map((f) => [f.signal_id, f]))
  return snapshot
}

async function fetchSystemInfo(): Promise<SystemInfo> {
  const res = await fetch(`${GATEWAY_HTTP}/api/system-info`)
  if (!res.ok) throw new Error(`GET /api/system-info: HTTP ${res.status}`)
  const info = (await res.json()) as SystemInfo
  systemInfo.value = info
  return info
}

async function setControlMode(req: SetControlModeRequest): Promise<ControlAuthorityState> {
  const res = await fetch(`${GATEWAY_HTTP}/api/control`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) throw new Error(`POST /api/control: HTTP ${res.status}`)
  const state = (await res.json()) as ControlAuthorityState
  control.value = state
  return state
}

async function unlockMaintenance(req: UnlockMaintenanceRequest): Promise<MaintenanceState> {
  const res = await fetch(`${GATEWAY_HTTP}/api/maintenance/unlock`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST /api/maintenance/unlock: HTTP ${res.status} — ${detail}`)
  }
  const state = (await res.json()) as MaintenanceState
  maintenance.value = state
  return state
}

async function fetchStepConfig(): Promise<AntennaStepConfig> {
  const res = await fetch(`${GATEWAY_HTTP}/api/antenna/step-config`)
  if (!res.ok) throw new Error(`GET /api/antenna/step-config: HTTP ${res.status}`)
  return (await res.json()) as AntennaStepConfig
}

async function setStepConfig(config: AntennaStepConfig): Promise<AntennaStepConfig> {
  const res = await fetch(`${GATEWAY_HTTP}/api/antenna/step-config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST /api/antenna/step-config: HTTP ${res.status} — ${detail}`)
  }
  return (await res.json()) as AntennaStepConfig
}

async function fetchProcessMonitor(): Promise<ProcessMonitorSnapshot> {
  const res = await fetch(`${GATEWAY_HTTP}/api/process-monitor`)
  if (!res.ok) throw new Error(`GET /api/process-monitor: HTTP ${res.status}`)
  return (await res.json()) as ProcessMonitorSnapshot
}

async function fetchTrendChannels(): Promise<string[]> {
  const res = await fetch(`${GATEWAY_HTTP}/api/trend/channels`)
  if (!res.ok) throw new Error(`GET /api/trend/channels: HTTP ${res.status}`)
  return (await res.json()) as string[]
}

async function fetchTrendStatus(): Promise<TrendStatus> {
  const res = await fetch(`${GATEWAY_HTTP}/api/trend/status`)
  if (!res.ok) throw new Error(`GET /api/trend/status: HTTP ${res.status}`)
  return (await res.json()) as TrendStatus
}

async function startTrend(signalIds: string[]): Promise<TrendStatus> {
  const res = await fetch(`${GATEWAY_HTTP}/api/trend/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ signal_ids: signalIds }),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST /api/trend/start: HTTP ${res.status} — ${detail}`)
  }
  return (await res.json()) as TrendStatus
}

async function stopTrend(): Promise<TrendStatus> {
  const res = await fetch(`${GATEWAY_HTTP}/api/trend/stop`, { method: 'POST' })
  if (!res.ok) throw new Error(`POST /api/trend/stop: HTTP ${res.status}`)
  return (await res.json()) as TrendStatus
}

async function continueTrend(): Promise<TrendStatus> {
  const res = await fetch(`${GATEWAY_HTTP}/api/trend/continue`, { method: 'POST' })
  if (!res.ok) throw new Error(`POST /api/trend/continue: HTTP ${res.status}`)
  return (await res.json()) as TrendStatus
}

async function clearTrend(): Promise<TrendStatus> {
  const res = await fetch(`${GATEWAY_HTTP}/api/trend/clear`, { method: 'POST' })
  if (!res.ok) throw new Error(`POST /api/trend/clear: HTTP ${res.status}`)
  return (await res.json()) as TrendStatus
}

async function fetchTrendData(): Promise<TrendSeries[]> {
  const res = await fetch(`${GATEWAY_HTTP}/api/trend/data`)
  if (!res.ok) throw new Error(`GET /api/trend/data: HTTP ${res.status}`)
  return (await res.json()) as TrendSeries[]
}

async function fetchPowerMonitor(): Promise<PowerMonitorSnapshot> {
  const res = await fetch(`${GATEWAY_HTTP}/api/power-monitor`)
  if (!res.ok) throw new Error(`GET /api/power-monitor: HTTP ${res.status}`)
  return (await res.json()) as PowerMonitorSnapshot
}

async function fetchCalibrationLog(): Promise<CalibrationLogEntry[]> {
  const res = await fetch(`${GATEWAY_HTTP}/api/calibration-log`)
  if (!res.ok) throw new Error(`GET /api/calibration-log: HTTP ${res.status}`)
  return (await res.json()) as CalibrationLogEntry[]
}

async function fetchZeroCheck(): Promise<ZeroCheckSnapshot> {
  const res = await fetch(`${GATEWAY_HTTP}/api/zero-check`)
  if (!res.ok) throw new Error(`GET /api/zero-check: HTTP ${res.status}`)
  return (await res.json()) as ZeroCheckSnapshot
}

async function fetchDspInternalStatus(): Promise<DspInternalStatusSnapshot> {
  const res = await fetch(`${GATEWAY_HTTP}/api/dsp/internal-status`)
  if (!res.ok) throw new Error(`GET /api/dsp/internal-status: HTTP ${res.status}`)
  return (await res.json()) as DspInternalStatusSnapshot
}

async function fetchClutterFilters(): Promise<ClutterFilterSettings> {
  const res = await fetch(`${GATEWAY_HTTP}/api/dsp/clutter-filters`)
  if (!res.ok) throw new Error(`GET /api/dsp/clutter-filters: HTTP ${res.status}`)
  return (await res.json()) as ClutterFilterSettings
}

async function setClutterFilters(settings: ClutterFilterSettings): Promise<ClutterFilterSettings> {
  const res = await fetch(`${GATEWAY_HTTP}/api/dsp/clutter-filters`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST /api/dsp/clutter-filters: HTTP ${res.status} — ${detail}`)
  }
  return (await res.json()) as ClutterFilterSettings
}

async function fetchTriggerSetupPw(): Promise<TriggerSetupPwSettings> {
  const res = await fetch(`${GATEWAY_HTTP}/api/dsp/trigger-setup-pw`)
  if (!res.ok) throw new Error(`GET /api/dsp/trigger-setup-pw: HTTP ${res.status}`)
  return (await res.json()) as TriggerSetupPwSettings
}

async function setTriggerSetupPw(settings: TriggerSetupPwSettings): Promise<TriggerSetupPwSettings> {
  const res = await fetch(`${GATEWAY_HTTP}/api/dsp/trigger-setup-pw`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST /api/dsp/trigger-setup-pw: HTTP ${res.status} — ${detail}`)
  }
  return (await res.json()) as TriggerSetupPwSettings
}

async function fetchProcessingOptions(): Promise<ProcessingOptionsSettings> {
  const res = await fetch(`${GATEWAY_HTTP}/api/dsp/processing-options`)
  if (!res.ok) throw new Error(`GET /api/dsp/processing-options: HTTP ${res.status}`)
  return (await res.json()) as ProcessingOptionsSettings
}

async function setProcessingOptions(settings: ProcessingOptionsSettings): Promise<ProcessingOptionsSettings> {
  const res = await fetch(`${GATEWAY_HTTP}/api/dsp/processing-options`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST /api/dsp/processing-options: HTTP ${res.status} — ${detail}`)
  }
  return (await res.json()) as ProcessingOptionsSettings
}

async function resetDspCounters(): Promise<DspResetCountersResponse> {
  const res = await fetch(`${GATEWAY_HTTP}/api/dsp/reset-counters`, {
    method: 'POST',
  })
  if (!res.ok) throw new Error(`POST /api/dsp/reset-counters: HTTP ${res.status}`)
  return (await res.json()) as DspResetCountersResponse
}

async function setPowerLimits(limits: PowerMeasurementLimits): Promise<PowerMeasurementLimits> {
  const res = await fetch(`${GATEWAY_HTTP}/api/power-monitor/limits`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(limits),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST /api/power-monitor/limits: HTTP ${res.status} — ${detail}`)
  }
  return (await res.json()) as PowerMeasurementLimits
}

async function fetchSectorBlanking(): Promise<SectorBlankingProfile> {
  const res = await fetch(`${GATEWAY_HTTP}/api/sector-blanking`)
  if (!res.ok) throw new Error(`GET /api/sector-blanking: HTTP ${res.status}`)
  return (await res.json()) as SectorBlankingProfile
}

async function setSectorBlanking(profile: SectorBlankingProfile): Promise<SectorBlankingProfile> {
  const res = await fetch(`${GATEWAY_HTTP}/api/sector-blanking/set`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profile),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST /api/sector-blanking/set: HTTP ${res.status} — ${detail}`)
  }
  return (await res.json()) as SectorBlankingProfile
}

async function saveSectorBlanking(): Promise<SectorBlankingProfile> {
  const res = await fetch(`${GATEWAY_HTTP}/api/sector-blanking/save`, { method: 'POST' })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST /api/sector-blanking/save: HTTP ${res.status} — ${detail}`)
  }
  return (await res.json()) as SectorBlankingProfile
}

async function fetchScanWorksheet(): Promise<ScanCut[]> {
  const res = await fetch(`${GATEWAY_HTTP}/api/scan/worksheet`)
  if (!res.ok) throw new Error(`GET /api/scan/worksheet: HTTP ${res.status}`)
  return (await res.json()) as ScanCut[]
}

async function fetchConfigProfileCurrent(): Promise<RcpConfigProfile> {
  const res = await fetch(`${GATEWAY_HTTP}/api/config/profile/current`)
  if (!res.ok) throw new Error(`GET /api/config/profile/current: HTTP ${res.status}`)
  return (await res.json()) as RcpConfigProfile
}

async function fetchConfigProfileSaved(): Promise<RcpConfigProfile> {
  const res = await fetch(`${GATEWAY_HTTP}/api/config/profile/saved`)
  if (!res.ok) throw new Error(`GET /api/config/profile/saved: HTTP ${res.status}`)
  return (await res.json()) as RcpConfigProfile
}

async function setConfigProfile(profile: RcpConfigProfile): Promise<RcpConfigProfile> {
  const res = await fetch(`${GATEWAY_HTTP}/api/config/profile/set`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profile),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST /api/config/profile/set: HTTP ${res.status} — ${detail}`)
  }
  return (await res.json()) as RcpConfigProfile
}

async function saveConfigProfile(): Promise<RcpConfigProfile> {
  const res = await fetch(`${GATEWAY_HTTP}/api/config/profile/save`, { method: 'POST' })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST /api/config/profile/save: HTTP ${res.status} — ${detail}`)
  }
  return (await res.json()) as RcpConfigProfile
}

async function restoreConfigProfile(): Promise<RcpConfigProfile> {
  const res = await fetch(`${GATEWAY_HTTP}/api/config/profile/restore`, { method: 'POST' })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST /api/config/profile/restore: HTTP ${res.status} — ${detail}`)
  }
  return (await res.json()) as RcpConfigProfile
}

async function factoryConfigProfile(): Promise<RcpConfigProfile> {
  const res = await fetch(`${GATEWAY_HTTP}/api/config/profile/factory`, { method: 'POST' })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST /api/config/profile/factory: HTTP ${res.status} — ${detail}`)
  }
  return (await res.json()) as RcpConfigProfile
}

async function savePowerLimits(): Promise<PowerMeasurementLimits> {
  const res = await fetch(`${GATEWAY_HTTP}/api/power-monitor/limits/save`, { method: 'POST' })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST /api/power-monitor/limits/save: HTTP ${res.status} — ${detail}`)
  }
  return (await res.json()) as PowerMeasurementLimits
}

async function fetchRadarConstant(): Promise<RadarConstantSnapshot> {
  const res = await fetch(`${GATEWAY_HTTP}/api/radar-constant`)
  if (!res.ok) throw new Error(`GET /api/radar-constant: HTTP ${res.status}`)
  return (await res.json()) as RadarConstantSnapshot
}

async function setRadarConstant(params: RadarConstantParameters): Promise<RadarConstantSnapshot> {
  const res = await fetch(`${GATEWAY_HTTP}/api/radar-constant`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST /api/radar-constant: HTTP ${res.status} — ${detail}`)
  }
  return (await res.json()) as RadarConstantSnapshot
}

async function saveRadarConstant(): Promise<RadarConstantSnapshot> {
  const res = await fetch(`${GATEWAY_HTTP}/api/radar-constant/save`, { method: 'POST' })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST /api/radar-constant/save: HTTP ${res.status} — ${detail}`)
  }
  return (await res.json()) as RadarConstantSnapshot
}

async function saveSinglePointCalibrationResult(jobId: string): Promise<MeasuredRadarConstant> {
  const res = await fetch(`${GATEWAY_HTTP}/api/control/single-point-calibration/${jobId}/save-result`, {
    method: 'POST',
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(
      `POST /api/control/single-point-calibration/${jobId}/save-result: HTTP ${res.status} — ${detail}`,
    )
  }
  return (await res.json()) as MeasuredRadarConstant
}

async function lockMaintenance(): Promise<MaintenanceState> {
  const res = await fetch(`${GATEWAY_HTTP}/api/maintenance/lock`, {
    method: 'POST',
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST /api/maintenance/lock: HTTP ${res.status} — ${detail}`)
  }
  const state = (await res.json()) as MaintenanceState
  maintenance.value = state
  return state
}

// Ejecucion de rutinas de control (POST /api/control/*, ver core/contracts/mmi.py
// y src/adapters/gateway/app.py) -- D-12: el POST ya no bloquea hasta que la
// rutina termina (podia ser hasta timeout_s, minutos en antenna-positioning o
// power-on con caldeo real). Devuelve un job_id de inmediato (202); esta funcion
// sondea GET /api/control/jobs/{job_id} hasta que el job termina y devuelve el
// RoutineResult -- cada vista sigue viendo la misma forma "await, obtengo el
// resultado final" que ya tenia, solo que ahora puede tardar de verdad sin
// dejar el fetch original colgado.
const CONTROL_JOB_POLL_INTERVAL_MS = 400

async function advanceControlJobStep(jobId: string, data: Record<string, unknown>): Promise<ControlJobStatusResponse> {
  const res = await fetch(`${GATEWAY_HTTP}/api/control/jobs/${jobId}/step`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data }),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST /api/control/jobs/${jobId}/step: HTTP ${res.status} — ${detail}`)
  }
  return (await res.json()) as ControlJobStatusResponse
}

async function runControlJob<T>(
  path: string,
  body?: unknown,
  onJobId?: (jobId: string) => void,
  onJobStatus?: (job: ControlJobStatusResponse) => void,
): Promise<T> {
  const res = await fetch(`${GATEWAY_HTTP}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST ${path}: HTTP ${res.status} — ${detail}`)
  }
  const accepted = (await res.json()) as ControlJobAccepted
  onJobId?.(accepted.job_id)

  while (true) {
    const jobRes = await fetch(`${GATEWAY_HTTP}/api/control/jobs/${accepted.job_id}`)
    if (!jobRes.ok) throw new Error(`GET /api/control/jobs/${accepted.job_id}: HTTP ${jobRes.status}`)
    const job = (await jobRes.json()) as ControlJobStatusResponse
    onJobStatus?.(job)
    if (job.status === 'done') {
      if (job.error) throw new Error(`job ${job.job_id} (${job.routine}) fallo: ${job.error}`)
      return job.result as T
    }
    await new Promise((resolve) => setTimeout(resolve, CONTROL_JOB_POLL_INTERVAL_MS))
  }
}

// Cancela un job en curso (POST /api/control/jobs/{job_id}/cancel) -- cada
// rutina de movimiento/Scan Controller ya se encarga de detener el eje que
// estuviera comandando antes de que el job quede en `done` (ver
// adapters/gateway/app.py, `_start_control_job`/docstrings de
// core/control_routines/antenna_*.py). Idempotente del lado del backend:
// si el job ya termino, esto no falla, solo devuelve su estado actual.
async function cancelControlJob(jobId: string): Promise<ControlJobStatusResponse> {
  const res = await fetch(`${GATEWAY_HTTP}/api/control/jobs/${jobId}/cancel`, { method: 'POST' })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST /api/control/jobs/${jobId}/cancel: HTTP ${res.status} — ${detail}`)
  }
  return (await res.json()) as ControlJobStatusResponse
}

// El WebSocket se crea una sola vez, en el primer useGateway() que se
// invoque (normalmente App.vue al montar) -- no a nivel de módulo puro,
// porque useWebSocket registra limpieza vía onScopeDispose y conviene que
// esa primera llamada ocurra dentro de un setup() real.
let ws: ReturnType<typeof useWebSocket> | null = null

function ensureConnected() {
  if (ws) return ws
  ws = useWebSocket(GATEWAY_WS, {
    autoReconnect: { retries: -1, delay: 1000 },
    onConnected() {
      lastCloseReason.value = null
    },
    onDisconnected(_socket, event) {
      lastCloseReason.value = event.reason || `código ${event.code}`
    },
    onError() {
      lastCloseReason.value = 'error de red'
    },
    onMessage(_socket, event) {
      const msg = JSON.parse(event.data) as WsMessage
      messages.value.push(msg)
      if (messages.value.length > MAX_LOG) messages.value.shift()

      if (msg.type === 'session') {
        control.value = msg.control
        sessionInfo.value = { rcp_version: msg.rcp_version, started_at_wall: msg.started_at_wall }
      }
      if (msg.type === 'antenna') antenna.value = msg.position
      if (msg.type === 'event' && (msg.kind === 'control_mode_changed' || msg.kind.startsWith('maintenance_'))) {
        // el gateway ya mando el nuevo estado via el POST que origino este evento
        // o evento de expiracion; refrescamos el estado por /api/status.
        fetchStatus().catch(() => {})
      }
      if (msg.type === 'bite_event') {
        const next = new Map(biteFaults.value)
        if (msg.transition === 'fault') {
          next.set(msg.signal_id, { signal_id: msg.signal_id, detail: msg.detail, since_wall: msg.at_wall })
        } else {
          next.delete(msg.signal_id)
        }
        biteFaults.value = next
      }
      if (msg.type === 'status') {
        const receivedAt = Date.now()
        lastStatusMessageAt.value = receivedAt
        halConnected.value = msg.hal_connected
        dsp.value = msg.dsp
        const count = msg.dsp?.radials_received ?? null
        if (count !== null) {
          const prev = lastRadialSample.value
          if (prev !== null && count !== prev.count) {
            const elapsedS = (receivedAt - prev.at) / 1000
            if (elapsedS > 0) dspRadialRate.value = (count - prev.count) / elapsedS
            lastRadialChangeAt.value = receivedAt
          } else if (prev === null) {
            lastRadialChangeAt.value = receivedAt
          }
          lastRadialSample.value = { count, at: receivedAt }
        }
      }
    },
  })
  // 1 Hz alcanza para el umbral de STALE_TIMEOUT_MS (5 s) con margen -- ver
  // statusChannelStale/dspDataStale mas arriba.
  setInterval(() => {
    nowTick.value = Date.now()
  }, 1000)
  return ws
}

export function useGateway() {
  const { status, send, open, close } = ensureConnected()
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
    fetchCalibrationLog,
    fetchZeroCheck,
    setPowerLimits,
    savePowerLimits,
    fetchSectorBlanking,
    setSectorBlanking,
    saveSectorBlanking,
    fetchScanWorksheet,
    fetchConfigProfileCurrent,
    fetchConfigProfileSaved,
    setConfigProfile,
    saveConfigProfile,
    restoreConfigProfile,
    factoryConfigProfile,
    fetchDspInternalStatus,
    resetDspCounters,
    fetchClutterFilters,
    setClutterFilters,
    fetchTriggerSetupPw,
    setTriggerSetupPw,
    fetchProcessingOptions,
    setProcessingOptions,
    fetchRadarConstant,
    setRadarConstant,
    saveRadarConstant,
    saveSinglePointCalibrationResult,
    advanceControlJobStep,
    runControlJob,
    cancelControlJob,
    send,
    open,
    close,
  }
}
