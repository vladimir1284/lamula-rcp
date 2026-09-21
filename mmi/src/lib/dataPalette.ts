// Resuelve el sistema de color de datos (D6, paso 1 "diseño de color",
// tokens en assets/main.css) a colores usables por un canvas 2D -- fillStyle
// no acepta `var(--x)` directo, hay que leer el custom property calculated.
// No define una paleta nueva: reutiliza la ya validada (ΔE, ver
// ColorSystem.vue) en vez de inventar otra para las vistas de datos.
import { buildDivergentScale, buildSequentialScale } from './colorScales'
import type { DataKind } from './mockRadar'

const STEP_VARS: Record<DataKind, string[]> = {
  reflectivity: Array.from({ length: 8 }, (_, i) => `--data-reflectivity-${i + 1}`),
  velocity: [
    ...Array.from({ length: 5 }, (_, i) => `--data-velocity-away-${5 - i}`),
    '--data-velocity-zero',
    ...Array.from({ length: 5 }, (_, i) => `--data-velocity-toward-${i + 1}`),
  ],
  width: Array.from({ length: 4 }, (_, i) => `--data-width-${i + 1}`),
}

export function paletteVars(kind: DataKind): string[] {
  return STEP_VARS[kind]
}

export function resolvePalette(kind: DataKind, el: Element = document.documentElement): string[] {
  const style = getComputedStyle(el)
  return STEP_VARS[kind].map((name) => style.getPropertyValue(name).trim() || '#666')
}

/** `value` normalizado: 0..1 para reflectivity/width, -1..1 (con signo) para velocity. */
export function colorForValue(palette: string[], kind: DataKind, value: number): string {
  const t = kind === 'velocity' ? (value + 1) / 2 : value
  const idx = Math.min(palette.length - 1, Math.max(0, Math.round(t * (palette.length - 1))))
  return palette[idx] ?? '#666'
}

/**
 * Modo continuo (D6): interpola entre los N colores generados por `colorScales.ts`
 * en vez de redondear al escalón más cercano (`colorForValue` discreto intacto).
 * `value` normalizado: 0..1 para reflectivity/width, -1..1 (con signo) para velocity.
 */
export function colorForValueContinuous(scale: string[], kind: DataKind, value: number): string {
  if (scale.length === 0) return '#666'
  const t = kind === 'velocity' ? (value + 1) / 2 : value
  const clampedT = Math.max(0, Math.min(1, t))
  const pos = clampedT * (scale.length - 1)
  const idx = Math.min(scale.length - 1, Math.floor(pos))
  return scale[idx] ?? '#666'
}

// Persistencia LocalStorage (D6):
// Convención de persistencia del proyecto RCP MMI:
// Como no existe un patrón previo de `localStorage` en `mmi/src/`, utilizamos la clave
// namespaced `rcp.colorComposer.<kind>` para almacenar la lista de stops editados.
// Esto aísla las preferencias personalizadas por magnitud y evita colisiones globales.

const STORAGE_KEY_PREFIX = 'rcp.colorComposer.'

export function getStoredStops(kind: DataKind): string[] | null {
  if (typeof localStorage === 'undefined') return null
  try {
    const raw = localStorage.getItem(`${STORAGE_KEY_PREFIX}${kind}`)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) && parsed.length > 0 ? (parsed as string[]) : null
  } catch {
    return null
  }
}

export function setStoredStops(kind: DataKind, stops: string[]): void {
  if (typeof localStorage === 'undefined') return
  try {
    localStorage.setItem(`${STORAGE_KEY_PREFIX}${kind}`, JSON.stringify(stops))
  } catch {
    // Ignorar errores de almacenamiento cuota / permisos
  }
}

export function removeStoredStops(kind: DataKind): void {
  if (typeof localStorage === 'undefined') return
  try {
    localStorage.removeItem(`${STORAGE_KEY_PREFIX}${kind}`)
  } catch {
    // Ignorar errores
  }
}

/**
 * Obtiene los stops activos para un `kind` dado (stops personalizados en LocalStorage
 * o los valores por defecto leídos de main.css vía `resolvePalette`).
 */
export function getActiveStops(kind: DataKind, el: Element = document.documentElement): string[] {
  const custom = getStoredStops(kind)
  if (custom && custom.length > 0) return custom
  return resolvePalette(kind, el)
}

/**
 * Construye la escala continua activa de N colores (por defecto N=64 o 256)
 * leyendo los stops activos.
 */
export function buildActiveScale(kind: DataKind, n: number = 256, el: Element = document.documentElement): string[] {
  const stops = getActiveStops(kind, el)
  if (kind === 'velocity') {
    return buildDivergentScale(stops, n)
  }
  return buildSequentialScale(stops, n)
}
