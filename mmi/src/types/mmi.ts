// Copia manual de src/core/contracts/mmi.py -- el pipeline de codegen
// Pydantic -> TypeScript (project-plan.md Sec.5, D-08) todavia no existe.
// Si el contrato Python cambia, este archivo hay que actualizarlo a mano
// hasta que exista el codegen real.

import type { ScanCutResult } from '@/types/scan'

export type OperatorMode = 'passive' | 'active'

export interface ControlAuthorityState {
  mode: OperatorMode
  actor: string
  since_wall: string
}

export type AccessLevel = 'OP' | 'MANT'

export interface MaintenanceState {
  level: AccessLevel
  actor: string | null
  since_wall: string | null
  expires_wall: string | null
}

export interface UnlockMaintenanceRequest {
  password: string
  actor: string
  duration_s: number
}

export interface AntennaPosition {
  az_deg: number
  el_deg: number
  az_rate_deg_s: number
  el_rate_deg_s: number
  az_valid: boolean
  el_valid: boolean
  az_ref_ok: boolean
  el_ref_ok: boolean
  az_fault: boolean
  el_fault: boolean
  degraded: boolean
  seq: number
  at_us: number
}

export type RadialStatus =
  | 'start_of_volume'
  | 'start_of_elevation'
  | 'intermediate'
  | 'end_of_elevation'
  | 'end_of_volume'

export interface DspStreamStatus {
  connected: boolean
  radials_received: number
  last_volume_number: number | null
  last_elevation_number: number | null
  last_radial_status: RadialStatus | null
  last_radial_at_wall: string | null
}

export type BiteTransition = 'fault' | 'cleared'

export interface BiteFaultSummary {
  signal_id: string
  detail: string
  since_wall: string
}

export interface SystemInfo {
  rcp_version: string
  dsp_contract_version: string
  dsp_contract_commit: string
  dsp_contract_commit_date: string
  connected_clients: number
}

export interface SystemStatusSnapshot {
  control: ControlAuthorityState
  maintenance: MaintenanceState
  hal_connected: boolean
  antenna: AntennaPosition | null
  dsp: DspStreamStatus | null
  active_bite_faults: BiteFaultSummary[]
}

export interface SetControlModeRequest {
  mode: OperatorMode
  actor: string
}

// --- Ejecucion de rutinas de control (Fase 2, core/control_routines/ via
// POST /api/control/*) -- espejo manual de los request models nuevos en
// core/contracts/mmi.py. Ningun campo lleva default: ver la regla del
// modulo Python, es la misma aqui.

export type RoutineOutcome = 'success' | 'failed' | 'interrupted'

export interface RoutineStepResult {
  signal_id: string
  ok: boolean
  detail: string
}

export interface RoutineResult {
  routine: string
  outcome: RoutineOutcome
  steps: RoutineStepResult[]
  at_us: number
}

export type AntennaAxis = 'azimuth' | 'elevation'

export interface TransmitterPowerOnRequest {
  warmup_timeout_s: number
}

export interface ReceiverPowerOnRequest {
  confirm_timeout_s: number
}

export interface AntennaUnitPowerOnRequest {
  confirm_timeout_s: number
}

export interface AntennaMovementRequest {
  axis: AntennaAxis
  voltage_reference: number
}

export interface AntennaPositioningRequest {
  axis: AntennaAxis
  target_deg: number
  gain_v_per_deg: number
  max_voltage: number
  tolerance_deg: number
  timeout_s: number
}

export interface AntennaStepConfig {
  azimuth_step_deg: number
  elevation_step_deg: number
}

export interface ProcessInfo {
  pid: number
  name: string
  priority: number
  status: string
  cpu_percent: number
  memory_mb: number
}

export interface RcpTaskInfo {
  name: string
  state: 'pending' | 'done' | 'cancelled'
}

export interface ProcessMonitorSnapshot {
  process: ProcessInfo
  tasks: RcpTaskInfo[]
}

export interface TrendChannelSample {
  at_wall: string
  value: number | null
}

export interface TrendSeries {
  signal_id: string
  samples: TrendChannelSample[]
}

export interface TrendStartRequest {
  signal_ids: string[]
}

export interface TrendStatus {
  running: boolean
  started_at_wall: string | null
  signal_ids: string[]
}

export interface PowerMeasurementLimits {
  forward_limit_kw: number
  reverse_limit_kw: number
  vswr_limit: number
}

export interface PowerMonitorSnapshot {
  forward_power_kw: number | null
  reverse_power_kw: number | null
  vswr: number | null
  bus_ok: boolean
  radiating: boolean
  limits: PowerMeasurementLimits | null
}

// D-12: los seis POST /api/control/* ya no bloquean hasta que la rutina
// termina -- devuelven un job (202) y el llamador sondea su estado.
export type ControlJobStatus = 'running' | 'done'

export interface ControlJobAccepted {
  job_id: string
  routine: string
  status: ControlJobStatus
}

export interface ControlJobStatusResponse {
  job_id: string
  routine: string
  status: ControlJobStatus
  // `ScanCutResult` (Scan Controller, POST /api/scan/worksheet/{index}/execute)
  // se agrego a esta union en vez de un contrato de job separado -- ver
  // ControlJobStatusResponse en core/contracts/mmi.py.
  result: RoutineResult | ScanCutResult | null
  error: string | null
}

export interface SessionMessage {
  type: 'session'
  rcp_version: string
  started_at_wall: string
  control: ControlAuthorityState
}

export interface AntennaMessage {
  type: 'antenna'
  position: AntennaPosition
}

export interface OperatorEventMessage {
  type: 'event'
  seq: number
  at_wall: string
  kind: string
  actor: string
  payload: Record<string, unknown>
}

export interface HeartbeatMessage {
  type: 'heartbeat'
  at_wall: string
}

// A6 (SI/SR/SD/RD, docs/diseno/inventario-ui.md): empujado cada ~1s (ver
// WS_STATUS_PERIOD_S en src/adapters/gateway/app.py). Si este mensaje deja
// de llegar es en si mismo la señal de que SD esta caido -- ver D-14 en
// docs/alcance/decisiones.md.
export interface StatusMessage {
  type: 'status'
  at_wall: string
  hal_connected: boolean
  dsp: DspStreamStatus | null
}

export interface BiteEventMessage {
  type: 'bite_event'
  signal_id: string
  transition: BiteTransition
  detail: string
  at_wall: string
}

export type WsMessage =
  | SessionMessage
  | AntennaMessage
  | OperatorEventMessage
  | HeartbeatMessage
  | BiteEventMessage
  | StatusMessage
