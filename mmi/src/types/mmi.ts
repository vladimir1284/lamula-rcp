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

export interface DspInternalStatusSnapshot {
  connected: boolean
  uptime_s: number
  phase: number
  severity: number
  last_error: number
  n_rx_channels: number
  capability_flags: number
  bite_flags: number
  config_seq: number
  rays_in: number
  rays_out: number
  rays_dropped: number
  queue_depth: number
  bins_ok: number
  bins_total: number
  trigger_period_cmd_ns: number
  trigger_period_meas_ns: number
  noise_floor_dbm: number[]
  dc_offset_i: number[]
  dc_offset_q: number[]
  n_gates: number
  n_pulses: number
  prf_hz: number
  gate_spacing_m: number
  sqi_threshold: number
  sig_threshold: number
  ccor_threshold: number
  log_threshold: number
  rfi_filter: number
}

export interface DspResetCountersResponse {
  status: string
  message: string
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

export type SinglePointCalibrationMode = 'auto' | 'external'

export interface SinglePointCalibrationRequest {
  mode: SinglePointCalibrationMode
  injected_power_dbm?: number | null
  measured_radar_constant_db?: number | null
}

export interface MeasuredRadarConstant {
  radar_constant_db: number
  mode: SinglePointCalibrationMode
  measured_at: string
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

export interface CalibrationLogEntry {
  at_wall: string
  severity: 'info' | 'warn' | 'error'
  procedure: string
  actor: string
  message: string
  detail?: string | null
}

export interface BlankingSector {
  in_use: boolean
  az_start_deg: number
  az_end_deg: number
  el_start_deg: number
  el_end_deg: number
}

export interface SectorBlankingProfile {
  enabled: boolean
  sectors: BlankingSector[]
}

export interface ThresholdsConfig {
  log_threshold_db: number
  csr_threshold_db: number
  sqi_threshold: number
  speckle_remover: boolean
}

export interface ClutterFilterConfig {
  doppler_filter_id: number
  doppler_type_db: string
  fft_filter_enabled: boolean
  statistical_filter_enabled: boolean
}

export interface ClutterFilterSettings {
  clutter_filter: 'none' | 'gmap' | 'notch'
  clutter_width_ms: number
  fixed_win: number
  fixed_width_pts: number
  fixed_edge_pts: number
  variable_hunt_pts: number
  secondary_sqi_slope: number
  secondary_sqi_offset: number
}

export interface TriggerTimingRow {
  trigger_index: number
  name: string
  start_us: number
  width_us: number
  high: boolean
  prt_term_enabled: boolean
}

export interface TriggerSetupPwSettings {
  selected_pulse_width: 'short' | 'medium' | 'long'
  gate_spacing_m: number
  prf_hz: number
  external_pretrigger_delay_us: number
  current_noise_level_dbm: number
  powerup_noise_level_dbm: number
  triggers: TriggerTimingRow[]
}

export interface ProcessingOptionsSettings {
  spectral_window: 'user' | 'rect' | 'hamming' | 'blackman'
  r2_processing: 'never' | 'user' | 'always'
  clutter_microsuppression: 'never' | 'user' | 'always'
  ppp_autocorrels: 'never' | 'user' | 'always'
  unfold_velocity: 'never' | 'user' | 'always'
  process_custom_trigs: 'never' | 'user' | 'always'
  interference_filter: 'none' | 'alg1' | 'alg2' | 'alg3'
  phidp_offset_deg: number
}

export interface RadarConstantParameters {
  pulse_width_us: number
  zero_check_high_dbm: number
  zero_check_low_dbm: number
  tx_losses_db: number
  rx_losses_db: number
  radome_losses_db: number
  atmospheric_attenuation_db_km: number
  horizontal_beam_width_deg: number
  vertical_beam_width_deg: number
  antenna_gain_db: number
  wavelength_cm: number
  noise_figure_db: number | null
  filter_init_pulses: number
}

export interface RadarConstantSnapshot {
  params: RadarConstantParameters
  radar_constant_db: number
}

export interface PowerMeasurementLimits {
  forward_limit_kw: number
  reverse_limit_kw: number
  vswr_limit: number
}

export interface RcpConfigProfile {
  power_limits: PowerMeasurementLimits | null
  antenna_step_config: AntennaStepConfig
  sector_blanking: SectorBlankingProfile
  thresholds: ThresholdsConfig
  clutter_filter: ClutterFilterConfig
}

export interface PowerMonitorSnapshot {
  forward_power_kw: number | null
  reverse_power_kw: number | null
  vswr: number | null
  bus_ok: boolean
  radiating: boolean
  limits: PowerMeasurementLimits | null
}

export interface ZeroCheckSnapshot {
  last_run_at_wall: string | null
  next_run_at_wall: string | null
  interval_s: number
  enabled: boolean
  noise_high_dbm: number | null
  noise_low_dbm: number | null
  last_result: RoutineResult | null
}

export interface WizardStepInputRequest {
  data: Record<string, unknown>
}

export interface TxSamplingAdjustParams {
  tx_sample: number
  tx_frequency_mhz: number
  commanded_lo_freq_mhz: number
  tx_start_sample: number
  tx_stop_sample: number
}

export interface TxSamplingAdjustSnapshot {
  tx_sample_readout: number | null
  tx_frequency_readout_mhz: number | null
  commanded_lo_freq_readout_mhz: number | null
  tx_start_sample_readout: number | null
  tx_stop_sample_readout: number | null
  bus_ok: boolean
  radiating: boolean
  params: TxSamplingAdjustParams | null
}

// D-12: los seis POST /api/control/* ya no bloquean hasta que la rutina
// termina -- devuelven un job (202) y el llamador sondea su estado.
export type ControlJobStatus = 'running' | 'awaiting_operator_input' | 'done'

export interface ControlJobAccepted {
  job_id: string
  routine: string
  status: ControlJobStatus
}

export interface ControlJobStatusResponse {
  job_id: string
  routine: string
  status: ControlJobStatus
  current_step?: number | null
  total_steps?: number | null
  step_name?: string | null
  prompt?: string | null
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
