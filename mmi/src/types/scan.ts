// Copia manual de src/core/contracts/scan.py -- mismo motivo/patron que
// mmi/src/types/mmi.ts (sin pipeline de codegen Pydantic -> TypeScript
// todavia). Si el contrato Python cambia, este archivo hay que
// actualizarlo a mano.

import type { RoutineOutcome, RoutineStepResult } from '@/types/mmi'

// Vocabulario canonico de momentos, plan Sec.6 (core/contracts/dsp.py,
// MomentId) -- no inventar nombres nuevos.
export const MOMENT_IDS = [
  'UZ',
  'CZ',
  'V',
  'W',
  'ZDR',
  'PHIDP',
  'KDP',
  'LDR',
  'RHOHV',
  'SQI',
  'CCOR',
  'SIG',
  'I',
  'Q',
] as const

export type MomentId = (typeof MOMENT_IDS)[number]

export interface PpiCut {
  mode: 'ppi'
  elevation_deg: number // ge=-90, le=90
  azimuth_start_deg: number // ge=0, lt=360
  azimuth_end_deg: number // ge=0, le=360 (360 = una vuelta completa desde 0)
  prf_hz: number // gt=0
  pulse_width_us: number // gt=0
  moments: MomentId[] // min_length=1
}

export interface RhiCut {
  mode: 'rhi'
  azimuth_deg: number // ge=0, lt=360
  elevation_start_deg: number // ge=-90, le=90
  elevation_end_deg: number // ge=-90, le=90
  prf_hz: number // gt=0
  pulse_width_us: number // gt=0
  moments: MomentId[] // min_length=1
}

export type ScanCut = PpiCut | RhiCut

// --- Ejecucion de un corte (Scan Controller, core/scan_controller.py via
// POST /api/scan/worksheet/{index}/execute) -- espejo manual de
// AxisPositioningParams/ScanCutExecutionRequest/ScanCutResult en
// core/contracts/scan.py y mmi.py. Ningun campo lleva default, mismo motivo
// que AntennaPositioningRequest en mmi.ts.

export interface AxisPositioningParams {
  gain_v_per_deg: number
  max_voltage: number
  tolerance_deg: number
  timeout_s: number
}

export interface ScanCutExecutionRequest {
  azimuth_positioning: AxisPositioningParams
  elevation_positioning: AxisPositioningParams
  sweep_voltage_magnitude: number
  sweep_tolerance_deg: number
  sweep_timeout_s: number
}

// Espejo de ScanCutResult (core/contracts/scan.py) -- a diferencia de
// RoutineResult (mmi.ts) no lleva `routine`: el Scan Controller no es una de
// las seis rutinas del plan, es un orquestador que las consume.
export interface ScanCutResult {
  outcome: RoutineOutcome
  steps: RoutineStepResult[]
  at_us: number
}
