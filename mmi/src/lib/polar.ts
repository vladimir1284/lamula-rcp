// Matemática polar compartida por los dials SVG del dominio (AzimuthSectorDial,
// AntennaAngleDial). Convención: angleDeg=0 apunta "arriba" (Norte / cenit),
// crece en sentido horario -- misma convención que usa el legacy para azimut.
export function polarToCartesian(cx: number, cy: number, radius: number, angleDeg: number) {
  const rad = (angleDeg * Math.PI) / 180.0
  return {
    x: cx + radius * Math.sin(rad),
    y: cy - radius * Math.cos(rad),
  }
}
