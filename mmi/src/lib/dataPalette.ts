// Resuelve el sistema de color de datos (D6, paso 1 "diseño de color",
// tokens en assets/main.css) a colores usables por un canvas 2D -- fillStyle
// no acepta `var(--x)` directo, hay que leer el custom property calculado.
// No define una paleta nueva: reutiliza la ya validada (ΔE, ver
// ColorSystem.vue) en vez de inventar otra para las vistas de datos.
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
