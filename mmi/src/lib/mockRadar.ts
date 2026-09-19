// Generador de datos sintéticos para D2/D3/D4 (ASCOPE/PPI/RHI, docs/diseno/
// inventario-ui.md, Familia D) -- "camino 1" acordado: solo UI en Storybook,
// sin backend. No hay contrato RCP<->MMI que transmita momentos todavía
// (ver DspStreamStatus en src/core/contracts/mmi.py, decisión 2026-08-19).
// Estos números no representan clima real ni ningún dato de radar: son dos
// "blobs" gaussianos fijos + ruido, solo para tener algo que animar/congelar/
// hacer zoom mientras se itera sobre el diseño.

export type DataKind = 'reflectivity' | 'velocity' | 'width'

export const DATA_KINDS: { id: DataKind; label: string }[] = [
  { id: 'reflectivity', label: 'Reflectivity' },
  { id: 'velocity', label: 'Velocity' },
  { id: 'width', label: 'Spectrum Width' },
]

export const GATE_COUNT = 128
export const MAX_RANGE_KM = 150

function noise(seed: number): number {
  const x = Math.sin(seed * 12.9898) * 43758.5453
  return x - Math.floor(x)
}

/** `angleDeg` es azimut (PPI/ASCOPE) o elevación (RHI); mismo campo sintético
 * para los tres, no hay razón para que difieran. */
function blobIntensity(kind: DataKind, angleDeg: number, gateIdx: number, gateCount: number): number {
  const rangeFrac = gateIdx / gateCount
  const a = ((angleDeg % 360) + 360) % 360
  const blob1 = Math.exp(-(((a - 60) / 25) ** 2)) * Math.exp(-(((rangeFrac - 0.35) / 0.15) ** 2))
  const blob2 = Math.exp(-(((a - 200) / 40) ** 2)) * Math.exp(-(((rangeFrac - 0.6) / 0.2) ** 2))
  const base = Math.max(blob1, blob2 * 0.8)
  const grain = noise(a * 7.1 + gateIdx * 3.3) * 0.08
  if (kind === 'velocity') {
    // Signo sintético (acercándose/alejándose) según el ángulo -- no hay
    // física real detrás, solo para ejercitar la rampa divergente.
    const sign = Math.sin((a * Math.PI) / 180)
    return Math.max(-1, Math.min(1, sign * base * 1.4 + (grain - 0.04)))
  }
  return Math.max(0, Math.min(1, base + grain))
}

export function generateGates(kind: DataKind, angleDeg: number, gateCount = GATE_COUNT): number[] {
  return Array.from({ length: gateCount }, (_, i) => blobIntensity(kind, angleDeg, i, gateCount))
}
