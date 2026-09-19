// B2 Subsystem Detail (docs/diseno/inventario-ui.md) -- "camino 1a"
// (decisión del usuario, 2026-09-19): espejo estático de `MONITORED_SIGNALS`
// en `src/core/bite/manager.py`. El backend nunca expone ese catálogo por
// REST/WS -- sólo `active_bite_faults` (las que están fallando ahora) -- así
// que sin este espejo no hay forma de pintar una fila "sana" en la MMI: sólo
// sabríamos de una señal cuando ya está en falla.
//
// Riesgo aceptado: esta lista puede desincronizarse si `MONITORED_SIGNALS`
// cambia en el backend sin actualizar este fichero. Mismo trade-off que
// `SUBSYSTEMS` en SystemVisualizationView.vue, a mayor escala (20 señales en
// vez de 4 subsistemas).
//
// Fuera de esta lista, sin respaldo real en absoluto:
// - Señales analógicas / analógico-digitales (clases del inventario): el
//   backend no monitorea ninguna, sólo digitales.
// - Los `label` de abajo son paráfrasis propia de la MMI, no el texto legacy
//   exacto de RAVIS -- no hay ese glosario disponible acá.
export interface BiteCatalogEntry {
  signalId: string
  label: string
}

export const SUBSYSTEM_LABELS: Record<string, string> = {
  sys: 'Sistema',
  tx: 'Transmisor',
  rx: 'Receptor',
  ant: 'Antena',
}

export const BITE_CATALOG: BiteCatalogEntry[] = [
  { signalId: 'sys.line_parameters_ok_status', label: 'Parámetros de línea' },
  { signalId: 'sys.environment_ok_status', label: 'Ambiente' },
  { signalId: 'sys.standby_system_ok_status', label: 'Sistema standby' },
  { signalId: 'tx.interlock_ok_status', label: 'Interlock' },
  { signalId: 'tx.wg_pressure_ok_status', label: 'Presión guía de onda' },
  { signalId: 'tx.cb_blower_ok_status', label: 'Soplador CB' },
  { signalId: 'tx.magnetron_blower_ok_status', label: 'Soplador magnetrón' },
  { signalId: 'tx.pha_seq_ok_status', label: 'Secuencia de fase' },
  { signalId: 'tx.duty_cycle_ok_status', label: 'Ciclo de trabajo' },
  { signalId: 'tx.fps_ok_status', label: 'FPS' },
  { signalId: 'tx.mps_fault_status', label: 'Falla MPS' },
  { signalId: 'tx.magnetron_peak_over_current_status', label: 'Sobrecorriente pico magnetrón' },
  { signalId: 'rx.p_15_v_ps_ok_status', label: 'Fuente +15V' },
  { signalId: 'rx.n_15_v_ps_ok_status', label: 'Fuente -15V' },
  { signalId: 'rx.p_12_v_ps_ok_status', label: 'Fuente +12V' },
  { signalId: 'rx.rfe_fault_status', label: 'Falla RFE' },
  { signalId: 'ant.drive_az_ok_status', label: 'Drive azimut' },
  { signalId: 'ant.drive_el_ok_status', label: 'Drive elevación' },
  { signalId: 'ant.i2t_drive_az_status', label: 'Protección térmica drive AZ (I2T)' },
  { signalId: 'ant.i2t_drive_el_status', label: 'Protección térmica drive EL (I2T)' },
]

export function subsystemOf(signalId: string): string {
  return signalId.split('.', 1)[0] ?? signalId
}
