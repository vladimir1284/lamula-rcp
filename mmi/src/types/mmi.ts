// Copia manual de src/core/contracts/mmi.py -- el pipeline de codegen
// Pydantic -> TypeScript (project-plan.md Sec.5, D-08) todavia no existe.
// Si el contrato Python cambia, este archivo hay que actualizarlo a mano
// hasta que exista el codegen real.

export type OperatorMode = 'passive' | 'active'

export interface ControlAuthorityState {
  mode: OperatorMode
  actor: string
  since_wall: string
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
}

export type BiteTransition = 'fault' | 'cleared'

export interface BiteFaultSummary {
  signal_id: string
  detail: string
  since_wall: string
}

export interface SystemStatusSnapshot {
  control: ControlAuthorityState
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
  result: RoutineResult | null
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
