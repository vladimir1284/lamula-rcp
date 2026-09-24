<script setup lang="ts">
// A1 App Shell, cableado real (paso 3, docs/diseno/inventario-ui.md): antes
// era un nav de rutas planas + RouterView (Fase 2) -- la propia decisión de
// diseño rechaza ese patrón a favor del mosaico de 1-4 paneles. App.vue es
// ahora el único punto donde el catálogo de vistas reales se une con
// AppShell (que no sabe renderizar ninguna vista concreta, ver
// components/shell/AppShell.vue).
import { computed, onMounted } from 'vue'
import AppShell from '@/components/shell/AppShell.vue'
import AntennaControlView from '@/views/AntennaControlView.vue'
import AscopeView from '@/views/AscopeView.vue'
import BiteMessagesView from '@/views/BiteMessagesView.vue'
import ConnectionView from '@/views/ConnectionView.vue'
import ControlCenterView from '@/views/ControlCenterView.vue'
import EventLogView from '@/views/EventLogView.vue'
import PpiView from '@/views/PpiView.vue'
import RhiView from '@/views/RhiView.vue'
import ScanWorksheetView from '@/views/ScanWorksheetView.vue'
import SubsystemDetailView from '@/views/SubsystemDetailView.vue'
import BiteReviewView from '@/views/BiteReviewView.vue'
import MaintenanceUnlockView from '@/views/MaintenanceUnlockView.vue'
import PowerMonitorView from '@/views/PowerMonitorView.vue'
import ProcessMonitorView from '@/views/ProcessMonitorView.vue'
import RadarConstantView from '@/views/RadarConstantView.vue'
import StateTrendPlotView from '@/views/StateTrendPlotView.vue'
import DspSetupHubView from '@/views/DspSetupHubView.vue'
import ScanParameterPopup from '@/components/domain/ScanParameterPopup.vue'
import DspInternalStatusView from '@/views/DspInternalStatusView.vue'
import ThresholdsMatrixView from '@/views/ThresholdsMatrixView.vue'
import SystemInformationView from '@/views/SystemInformationView.vue'
import SectorBlankingView from '@/views/SectorBlankingView.vue'
import SystemStatusView from '@/views/SystemStatusView.vue'
import SystemVisualizationView from '@/views/SystemVisualizationView.vue'
import ZeroCheckView from '@/views/ZeroCheckView.vue'
import TxPowerCalibrationView from '@/views/TxPowerCalibrationView.vue'
import SinglePointCalibrationView from '@/views/SinglePointCalibrationView.vue'
import CalibrationLogView from '@/views/CalibrationLogView.vue'
import ConfigProfilesView from '@/views/ConfigProfilesView.vue'
import CalibrationHubView from '@/views/CalibrationHubView.vue'
import ClutterFiltersView from '@/views/ClutterFiltersView.vue'
import TriggerSetupPwView from '@/views/TriggerSetupPwView.vue'
import ProcessingOptionsView from '@/views/ProcessingOptionsView.vue'
import TxSamplingAdjustView from '@/views/TxSamplingAdjustView.vue'
import BurstAfcSetupView from '@/views/BurstAfcSetupView.vue'
import { GATEWAY_HTTP, useGateway } from '@/composables/useGateway'
import type { IndicatorState, MosaicPreset, ViewOption } from '@/types/shell'

const {
  control,
  maintenance,
  dsp,
  halConnected,
  statusChannelStale,
  dspDataStale,
  dspRadialRate,
  alarmWorst,
  alarmCount,
  fetchStatus,
} = useGateway()

// Catálogo completo de las 63 vistas del inventario está fuera de alcance
// (D1-D8, E-*, F-*, G-*, H-*, I-* siguen sin construir) -- las que ya
// existen quedan `available: true`; el resto se deja como placeholder para
// que el selector de panel (PanelFrame) muestre "no aplicable" en vez de
// hacer desaparecer la opción, igual que en AppShell.stories.ts.
const viewCatalog: ViewOption[] = [
  { id: 'system-visualization', label: 'B1 System Visualization', available: true },
  { id: 'subsystem-detail', label: 'B2 Subsystem Detail', available: true },
  { id: 'state-trend-plot', label: 'B4 State Trend Plot', available: true },
  { id: 'process-monitor', label: 'B5 RCP Process Monitor', available: true },
  { id: 'power-monitor', label: 'B7 Power Monitor (VSWR)', available: true },
  { id: 'radar-constant', label: 'G7 Radar Constant Parameters', available: true },
  { id: 'system-status', label: 'B10 System Status', available: true },
  { id: 'thresholds-matrix', label: 'E3 Thresholds Matrix (Vp)', available: true },
  { id: 'clutter-filters', label: 'E4 Clutter Filters (Mf)', available: true },
  { id: 'trigger-setup-pw', label: 'E6 Trigger Setup por Pulse Width (Mt<n>)', available: true },
  { id: 'processing-options', label: 'E2 Processing Options (Mp)', available: true },
  { id: 'dsp-internal-status', label: 'E12 DSP Internal Status', available: true },
  { id: 'bite-messages', label: 'B8 BiTE Messages', available: true },
  { id: 'bite-review', label: 'B9 BiTE Review', available: true },
  { id: 'antenna-control', label: 'C1 Antenna Control', available: true },
  { id: 'scan-worksheet', label: 'C3 Scan Worksheet', available: true },
  { id: 'control-routines', label: 'C4 Control Routine Runner', available: true },
  { id: 'sector-blanking', label: 'C5 Sector Blanking Editor', available: true },
  { id: 'connection', label: 'A2 Connection', available: true },
  { id: 'maintenance-unlock', label: 'A4 Maintenance Unlock', available: true },
  { id: 'event-log', label: 'A5 Event Log', available: true },
  { id: 'system-information', label: 'A7 System Information', available: true },
  { id: 'dsp-setup-hub', label: 'E1 DSP Setup Hub', available: true },
  { id: 'config-profiles', label: 'E11 Config Profiles', available: true },
  { id: 'ascope', label: 'D2 ASCOPE', available: true },
  { id: 'ppi', label: 'D3 PPI', available: true },
  { id: 'rhi', label: 'D4 RHI', available: true },
  { id: 'calibration-hub', label: 'G1 Calibration Hub', available: true },
  { id: 'zero-check', label: 'G5 Zero Check', available: true },
  { id: 'tx-power-calibration', label: 'G3 TX Power Calibration', available: true },
  { id: 'single-point-calibration', label: 'G4 Single Point Calibration', available: true },
  { id: 'scan-parameter-popup', label: 'D8 Scan Parameter Popup', available: true },
  { id: 'sun-position', label: 'H1 Sun Position', available: false },
  { id: 'itsg-control', label: 'I2 ITSG Control', available: false },
  { id: 'calibration-log', label: 'G8 Calibration Log', available: true },
  { id: 'rsp-tx-rx-adjust', label: 'G2 TX Sampling Adjust', available: true },
  { id: 'mb-setup', label: 'E7 Burst Pulse & AFC (Mb)', available: true },
  { id: 'pb-plot', label: 'F1 Burst Pulse Timing (Pb)', available: false },
]

// Mismos 8 presets de "Requisitos de concurrencia" que AppShell.stories.ts
// -- son las filas reales de la tabla del inventario, no inventados para la
// app. La mayoría todavía apunta a vistas D/E/F/G/H sin construir: eso es
// correcto, no un error -- refleja cuánto del inventario está hecho hoy.
const presets: MosaicPreset[] = [
  {
    id: 'tx-pulse-sampling',
    label: 'Muestreo pulso TX',
    layout: 'triple-left',
    viewIds: ['scan-worksheet', 'ascope', 'rsp-tx-rx-adjust'],
    builtin: true,
  },
  {
    id: 'sun-az',
    label: 'Corrección az. por sol',
    layout: 'triple-left',
    viewIds: ['antenna-control', 'ppi', 'sun-position'],
    builtin: true,
  },
  {
    id: 'sun-el',
    label: 'Corrección el. por sol',
    layout: 'quad',
    viewIds: ['antenna-control', 'scan-worksheet', 'rhi', 'sun-position'],
    builtin: true,
  },
  {
    id: 'fine-az-el',
    label: 'Ajuste fino az/el',
    layout: 'quad',
    viewIds: ['antenna-control', 'scan-worksheet', 'ascope', 'sun-position'],
    builtin: true,
  },
  {
    id: 'matched-filter',
    label: 'Filtro adaptado (Mb↔Pb)',
    layout: 'split-h',
    viewIds: ['mb-setup', 'pb-plot'],
    builtin: true,
  },
  {
    id: 'itsg-adjust',
    label: 'Ajuste ITSG',
    layout: 'split-h',
    viewIds: ['itsg-control', 'ascope'],
    builtin: true,
  },
  {
    id: 'calibration-log',
    label: 'Calibración + log',
    layout: 'split-h',
    viewIds: ['rsp-tx-rx-adjust', 'calibration-log'],
    builtin: true,
  },
  {
    id: 'surveillance',
    label: 'Vigilancia (BiTE)',
    layout: 'single',
    viewIds: ['bite-messages'],
    builtin: true,
  },
]

// Preset inicial: 'surveillance' es hoy el único 100% funcional (su único
// panel es una vista construida). Cualquier otro arrancaría mostrando
// paneles "no aplicable" -- honesto, pero mala primera impresión. El
// operador puede cambiar cualquier panel a otra vista real de inmediato, el
// selector no está restringido al preset activo.
const INITIAL_PRESET_ID = 'surveillance'

// A6 SI/SR/SD/RD -- el backend no implementa el scheduler RVP900 (SI/SR no
// tienen fuente real todavía). SD/RD se aproximan con lo que sí existe:
// hal_connected (conexión gateway<->HAL) y el stream DSP de radiales. No es
// 1:1 con la semántica legacy, pero es honesto: 'neutral' + detalle explica
// por qué, en vez de fabricar un estado sin respaldo.
//
// `fault` (rojo) y `stale` (gris, vía statusChannelStale/dspDataStale) son
// estados distintos a propósito (D-14, docs/alcance/decisiones.md): sin
// conexión vs. conectado-pero-sin-datos-hace-5s. Ambos se pintan 'neutral'
// porque LampState solo tiene tres colores (igual que la tabla A6 del
// inventario), pero el detalle deja clara la diferencia.
const indicators = computed<IndicatorState[]>(() => [
  { id: 'SI', state: 'neutral', detail: 'sin fuente de datos (scheduler RVP900 no implementado)' },
  { id: 'SR', state: 'neutral', detail: 'sin fuente de datos (scheduler RVP900 no implementado)' },
  {
    id: 'SD',
    state:
      halConnected.value === null
        ? 'neutral'
        : statusChannelStale.value
          ? 'neutral'
          : halConnected.value
            ? 'ok'
            : 'fault',
    detail:
      halConnected.value === null
        ? 'esperando estado inicial'
        : statusChannelStale.value
          ? 'sin datos de estado hace más de 5 s'
          : halConnected.value
            ? 'HAL conectado'
            : 'HAL sin conexión',
  },
  {
    id: 'RD',
    state:
      dsp.value === null
        ? 'neutral'
        : !dsp.value.connected
          ? 'fault'
          : dspDataStale.value
            ? 'neutral'
            : 'ok',
    detail:
      dsp.value === null
        ? 'sin stream DSP'
        : !dsp.value.connected
          ? 'DSP sin conexión'
          : dspDataStale.value
            ? 'sin radiales hace más de 5 s'
            : dspRadialRate.value !== null
              ? `${dspRadialRate.value.toFixed(1)} radiales/s`
              : `${dsp.value.radials_received} radiales recibidos`,
  },
])

// `simulated` (HAL real vs radar_emulator) no tiene respaldo en el backend
// todavía -- ningún contrato expone hal_kind. Se fija en falso en vez de
// fabricar un valor.

onMounted(() => {
  fetchStatus().catch(() => {
    // WS ya en autoReconnect -- si el snapshot inicial falla, el estado
    // sigue llegando por bite_event/antenna en cuanto el WS conecte.
  })
})
</script>

<template>
  <AppShell
    site-name="RD100S-01"
    :host="GATEWAY_HTTP"
    :simulated="false"
    :control="control"
    :access-level="maintenance?.level ?? 'OP'"
    :maintenance="maintenance"
    :indicators="indicators"
    :alarm-worst="alarmWorst"
    :alarm-count="alarmCount"
    :presets="presets"
    :view-catalog="viewCatalog"
    :initial-preset-id="INITIAL_PRESET_ID"
  >
    <template #system-visualization><SystemVisualizationView /></template>
    <template #subsystem-detail><SubsystemDetailView /></template>
    <template #state-trend-plot><StateTrendPlotView /></template>
    <template #process-monitor><ProcessMonitorView /></template>
    <template #power-monitor><PowerMonitorView /></template>
    <template #radar-constant><RadarConstantView /></template>
    <template #system-status><SystemStatusView /></template>
    <template #thresholds-matrix><ThresholdsMatrixView /></template>
    <template #dsp-internal-status><DspInternalStatusView /></template>
    <template #bite-messages><BiteMessagesView /></template>
    <template #bite-review><BiteReviewView /></template>
    <template #antenna-control><AntennaControlView /></template>
    <template #scan-worksheet><ScanWorksheetView /></template>
    <template #control-routines><ControlCenterView /></template>
    <template #sector-blanking><SectorBlankingView /></template>
    <template #connection><ConnectionView /></template>
    <template #maintenance-unlock><MaintenanceUnlockView /></template>
    <template #event-log><EventLogView /></template>
    <template #system-information><SystemInformationView /></template>
    <template #dsp-setup-hub><DspSetupHubView /></template>
    <template #config-profiles><ConfigProfilesView /></template>
    <template #ascope="{ panel }"><AscopeView :frozen="panel.frozen" /></template>
    <template #ppi="{ panel }"><PpiView :frozen="panel.frozen" /></template>
    <template #rhi="{ panel }"><RhiView :frozen="panel.frozen" /></template>
    <template #calibration-hub="{ setView }"><CalibrationHubView @navigate="setView" /></template>
    <template #zero-check><ZeroCheckView /></template>
    <template #tx-power-calibration><TxPowerCalibrationView /></template>
    <template #single-point-calibration><SinglePointCalibrationView /></template>
    <template #calibration-log><CalibrationLogView /></template>
    <template #clutter-filters><ClutterFiltersView /></template>
    <template #trigger-setup-pw><TriggerSetupPwView /></template>
    <template #processing-options><ProcessingOptionsView /></template>
    <template #rsp-tx-rx-adjust><TxSamplingAdjustView /></template>
    <template #mb-setup><BurstAfcSetupView /></template>
    <template #scan-parameter-popup><div class="flex h-full w-full items-center justify-center p-4"><ScanParameterPopup /></div></template>
  </AppShell>
</template>
