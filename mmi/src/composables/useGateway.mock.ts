// Doble de useGateway.ts para Storybook -- SOLO se usa ahí (ver el alias en
// .storybook/main.ts, que redirige el import exacto '@/composables/useGateway'
// a este fichero al construir Storybook; la app real y `vue-tsc` siguen
// resolviendo el módulo de verdad vía tsconfig paths).
//
// Motivo: paso 3 (docs/diseno/inventario-ui.md) cableó las vistas P0 de
// operación directo a useGateway() -- fetch/WS reales. Sin este doble, esas
// vistas sólo se pueden "ver" en Storybook mostrando errores de red
// (ERR_CONNECTION_REFUSED), que es exactamente lo que NO sirve para iterar
// sobre diseño visual. Este doble no reemplaza un backend real: da datos de
// ejemplo estables y funciones que responden localmente, para que cada
// vista se vea con contenido realista sin depender de que el RCP esté
// corriendo.
//
// Excepción conocida: ScanWorksheetView hace `fetch(GATEWAY_HTTP + ...)`
// directo para el CRUD del worksheet (no pasa por useGateway) -- eso sigue
// fallando en Storybook igual que sin backend real (mismo camino de error ya
// manejado en la vista). No se mockeó `fetch` global (MSW u otro) -- fuera
// de alcance de este paso.
import { computed, ref, shallowRef } from 'vue'
import type {
  AntennaMessage,
  BiteFaultSummary,
  ControlAuthorityState,
  ControlJobStatusResponse,
  DspStreamStatus,
  RoutineResult,
  SetControlModeRequest,
  SystemStatusSnapshot,
  WsMessage,
} from '@/types/mmi'
import type { ScanCutResult } from '@/types/scan'
import type { LampState } from '@/types/shell'
import type { SessionInfo } from './useGateway'

export const GATEWAY_HTTP = 'http://mock.invalid:8000'

const now = Date.now()
const iso = (msAgo: number) => new Date(now - msAgo).toISOString()

const status = ref<'CONNECTING' | 'OPEN' | 'CLOSED'>('OPEN')

const control = shallowRef<ControlAuthorityState | null>({
  mode: 'active',
  actor: 'operador-demo',
  since_wall: iso(45 * 60_000),
})

const antenna = shallowRef<AntennaMessage['position'] | null>({
  az_deg: 123.4,
  el_deg: 12.3,
  az_rate_deg_s: 6,
  el_rate_deg_s: 0,
  az_valid: true,
  el_valid: true,
  az_ref_ok: true,
  el_ref_ok: true,
  az_fault: false,
  el_fault: false,
  degraded: false,
  seq: 4821,
  at_us: now * 1000,
})

const dsp = shallowRef<DspStreamStatus | null>({
  connected: true,
  radials_received: 48213,
  last_volume_number: 12,
  last_elevation_number: 3,
  last_radial_status: 'intermediate',
})

const sessionInfo = shallowRef<SessionInfo | null>({
  rcp_version: 'v0.1.0-mock',
  started_at_wall: iso(2 * 3_600_000),
})

const biteFaults = ref<Map<string, BiteFaultSummary>>(
  new Map([
    ['tx.interlock_ok_status', { signal_id: 'tx.interlock_ok_status', detail: 'interlock abierto', since_wall: iso(3 * 60_000) }],
  ]),
)

const halConnected = shallowRef<boolean | null>(true)

// Historial mixto (eventos de operador + transiciones BiTE) -- mismo `type`
// discriminado que consume EventLogView/BiteMessagesView del stream real.
const messages = ref<WsMessage[]>([
  { type: 'session', rcp_version: 'v0.1.0-mock', started_at_wall: iso(2 * 3_600_000), control: control.value! },
  { type: 'event', seq: 1, at_wall: iso(40 * 60_000), kind: 'control_mode_changed', actor: 'operador-demo', payload: { mode: 'active' } },
  { type: 'bite_event', signal_id: 'ant.servo_ok_status', transition: 'fault', detail: 'servo sin respuesta', at_wall: iso(20 * 60_000) },
  { type: 'event', seq: 2, at_wall: iso(19 * 60_000), kind: 'general-power-on_started', actor: 'operador-demo', payload: {} },
  { type: 'event', seq: 3, at_wall: iso(18 * 60_000), kind: 'general-power-on_failed', actor: 'operador-demo', payload: { reason: 'precondición no cumplida' } },
  { type: 'bite_event', signal_id: 'ant.servo_ok_status', transition: 'cleared', detail: 'servo sin respuesta', at_wall: iso(10 * 60_000) },
  { type: 'event', seq: 4, at_wall: iso(9 * 60_000), kind: 'antenna-positioning_cancelled', actor: 'operador-demo', payload: {} },
  { type: 'bite_event', signal_id: 'tx.interlock_ok_status', transition: 'fault', detail: 'interlock abierto', at_wall: iso(3 * 60_000) },
])

const alarmAckedAt = ref<string | null>(null)
function acknowledgeAlarm() {
  alarmAckedAt.value = new Date().toISOString()
}
const alarmWorst = computed<LampState>(() => {
  const acked = alarmAckedAt.value
  for (const f of biteFaults.value.values()) {
    if (!acked || f.since_wall > acked) return 'fault'
  }
  return 'ok'
})
const alarmCount = computed(() => biteFaults.value.size)

async function fetchStatus(): Promise<SystemStatusSnapshot> {
  return {
    control: control.value!,
    hal_connected: halConnected.value ?? false,
    antenna: antenna.value,
    dsp: dsp.value,
    active_bite_faults: [...biteFaults.value.values()],
  }
}

async function setControlMode(req: SetControlModeRequest): Promise<ControlAuthorityState> {
  control.value = { mode: req.mode, actor: req.actor, since_wall: new Date().toISOString() }
  return control.value
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

// Simula "202 + sondeo" con un único delay -- suficiente para que
// JobActionPanel muestre su estado `busy` antes de resolver, sin tener que
// reimplementar el ciclo de sondeo real por job_id.
async function runControlJob<T>(path: string, _body?: unknown, onJobId?: (jobId: string) => void): Promise<T> {
  onJobId?.(`mock-job-${Date.now()}`)
  await delay(600)
  if (path.includes('/scan/worksheet/')) {
    const result: ScanCutResult = {
      outcome: 'success',
      steps: [{ signal_id: 'ant.az_position_ok_status', ok: true, detail: 'ok (mock)' }],
      at_us: Date.now() * 1000,
    }
    return result as T
  }
  const routine = path.split('/').pop() ?? 'routine'
  const result: RoutineResult = {
    routine,
    outcome: 'success',
    steps: [{ signal_id: 'sys.standby_system_ok_status', ok: true, detail: 'ok (mock)' }],
    at_us: Date.now() * 1000,
  }
  return result as T
}

async function cancelControlJob(jobId: string): Promise<ControlJobStatusResponse> {
  return { job_id: jobId, routine: 'mock', status: 'done', result: null, error: null }
}

function send() {
  // No hay socket real que mandar nada -- no-op deliberado.
}

export function useGateway() {
  return {
    status,
    messages,
    control,
    antenna,
    dsp,
    sessionInfo,
    biteFaults,
    halConnected,
    alarmAckedAt,
    alarmWorst,
    alarmCount,
    acknowledgeAlarm,
    fetchStatus,
    setControlMode,
    runControlJob,
    cancelControlJob,
    send,
  }
}
