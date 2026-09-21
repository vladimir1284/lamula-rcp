// Funciones de interpolación de color OKLCH para escalas continuas (D6)
//
// Permiten construir rampas de N colores interpolando de forma continua entre
// un conjunto de puntos de control (stops) definidos en OKLCH.
// La interpolación de Hue (H) respeta el camino corto sobre la rueda cromática 0-360°.

export interface OklchColor {
  l: number
  c: number
  h: number
}

const OKLCH_REGEX = /oklch\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\)/i

export function parseOklch(colorStr: string): OklchColor | null {
  const match = colorStr.trim().match(OKLCH_REGEX)
  if (!match) return null
  return {
    l: parseFloat(match[1]!),
    c: parseFloat(match[2]!),
    h: parseFloat(match[3]!),
  }
}

export function formatOklch(color: OklchColor): string {
  const l = Number(color.l.toFixed(3))
  const c = Number(color.c.toFixed(3))
  const h = Number((((color.h % 360) + 360) % 360).toFixed(1))
  return `oklch(${l} ${c} ${h})`
}

/**
 * Interpola linealmente entre dos tonos OKLCH.
 * h se interpola usando la ruta más corta sobre el círculo de 0 a 360°.
 */
export function interpolateOklch(a: OklchColor, b: OklchColor, t: number): OklchColor {
  const clampedT = Math.max(0, Math.min(1, t))
  const l = a.l + (b.l - a.l) * clampedT
  const c = a.c + (b.c - a.c) * clampedT

  let hA = ((a.h % 360) + 360) % 360
  let hB = ((b.h % 360) + 360) % 360

  const diff = hB - hA
  if (diff > 180) {
    hA += 360
  } else if (diff < -180) {
    hB += 360
  }

  const h = hA + (hB - hA) * clampedT
  return { l, c, h: ((h % 360) + 360) % 360 }
}

/**
 * Interpola un array de N colores a partir de una lista de stops OKLCH.
 * `stops` son strings en formato `oklch(L C H)`.
 */
export function buildSequentialScale(stops: string[], n: number): string[] {
  if (n <= 0) return []
  if (stops.length === 0) return Array.from({ length: n }, () => 'oklch(0.5 0 0)')

  const parsedStops = stops
    .map((s) => parseOklch(s))
    .filter((c): c is OklchColor => c !== null)

  if (parsedStops.length === 0) return Array.from({ length: n }, () => 'oklch(0.5 0 0)')
  if (parsedStops.length === 1 || n === 1) {
    return Array.from({ length: n }, () => formatOklch(parsedStops[0]!))
  }

  const result: string[] = []
  const segmentCount = parsedStops.length - 1

  for (let i = 0; i < n; i++) {
    const norm = i / (n - 1)
    const pos = norm * segmentCount
    const segIndex = Math.min(Math.floor(pos), segmentCount - 1)
    const segT = pos - segIndex

    const interpolated = interpolateOklch(parsedStops[segIndex]!, parsedStops[segIndex + 1]!, segT)
    result.push(formatOklch(interpolated))
  }

  return result
}

/**
 * Interpola una escala divergente de N colores a partir de stops OKLCH.
 * Para escalas divergentes (ej. velocidad centrado en 0), los stops se interpolan
 * asegurando la simetría si es aplicable o la ruta continua a través del centro.
 */
export function buildDivergentScale(stops: string[], n: number): string[] {
  return buildSequentialScale(stops, n)
}
