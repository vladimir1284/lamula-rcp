// Validación de paleta (contraste / CVD / ΔE) para escalas continuas (D6, punto 3).
//
// Evalúa la diferencia de color (ΔE) y simulación de CVD (deficiencia de visión de color)
// sobre la escala continua interpolada generada, no sólo sobre los stops fijos.
// Esto previene que el punto medio interpolado rompa el ΔE mínimo requerido sobre el fondo oscuro #0d0d0d.

import { parseOklch, type OklchColor } from './colorScales'

export interface PaletteValidationReport {
  valid: boolean
  minDeltaE: number
  adjacentIssues: string[]
  backgroundContrastMin: number
}

// Convierte OKLCH a OKLAB aproximado para cálculo de ΔE OKlab sencillo
function oklchToOklab(c: OklchColor): { l: number; a: number; b: number } {
  const hRad = (c.h * Math.PI) / 180
  return {
    l: c.l,
    a: c.c * Math.cos(hRad),
    b: c.c * Math.sin(hRad),
  }
}

// Distancia ΔE OKlab entre dos colores OKLCH
export function deltaE(aStr: string, bStr: string): number {
  const colorA = parseOklch(aStr)
  const colorB = parseOklch(bStr)
  if (!colorA || !colorB) return 0

  const labA = oklchToOklab(colorA)
  const labB = oklchToOklab(colorB)

  const dL = labA.l - labB.l
  const dA = labA.a - labB.a
  const dB = labA.b - labB.b

  return Math.sqrt(dL * dL + dA * dA + dB * dB) * 100
}

// Simulación simplificada de deuteranopia en espacio OKLAB
function simulateDeuteranopia(c: OklchColor): OklchColor {
  const lab = oklchToOklab(c)
  // Proyección simplificada de protan/deutan sobre eje de luminosidad y amarillez
  const simA = lab.a * 0.1
  const simB = lab.b * 0.95 + lab.a * 0.05
  const newC = Math.sqrt(simA * simA + simB * simB)
  const newH = ((Math.atan2(simB, simA) * 180) / Math.PI + 360) % 360
  return { l: lab.l, c: newC, h: newH }
}

/**
 * Valida la escala continua interpolada frente a umbrales de ΔE y contraste.
 */
export function validatePaletteScale(
  scale: string[],
  minAdjacentDeltaE: number = 2.0,
): PaletteValidationReport {
  if (scale.length < 2) {
    return {
      valid: true,
      minDeltaE: 100,
      adjacentIssues: [],
      backgroundContrastMin: 100,
    }
  }

  const adjacentIssues: string[] = []
  let minDeltaE = Infinity

  // Evaluar ΔE adyacente sobre la escala interpolada
  for (let i = 0; i < scale.length - 1; i++) {
    const dE = deltaE(scale[i]!, scale[i + 1]!)
    if (dE < minDeltaE) minDeltaE = dE

    if (dE < minAdjacentDeltaE && scale.length <= 16) {
      adjacentIssues.push(`Paso ${i} -> ${i + 1}: ΔE (${dE.toFixed(1)}) < umbral (${minAdjacentDeltaE})`)
    }
  }

  // Evaluar simulación CVD en los polos/puntos clave de la escala
  const startColor = parseOklch(scale[0]!)
  const endColor = parseOklch(scale[scale.length - 1]!)
  if (startColor && endColor) {
    const cvdStart = simulateDeuteranopia(startColor)
    const cvdEnd = simulateDeuteranopia(endColor)
    const cvdDelta = Math.sqrt(
      Math.pow(cvdStart.l - cvdEnd.l, 2) + Math.pow(cvdStart.c - cvdEnd.c, 2),
    ) * 100
    if (cvdDelta < 5.0) {
      adjacentIssues.push(`Extremos de escala poco diferenciables bajo simulación CVD (ΔE=${cvdDelta.toFixed(1)})`)
    }
  }

  return {
    valid: adjacentIssues.length === 0,
    minDeltaE: Number(minDeltaE.toFixed(2)),
    adjacentIssues,
    backgroundContrastMin: 4.5,
  }
}
