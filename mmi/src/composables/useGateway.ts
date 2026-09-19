// Cliente del gateway RCP<->MMI (src/adapters/gateway) -- REST + WS sobre el
// sobre ya congelado en core/contracts/mmi.py (ver src/types/mmi.ts).
//
// PEND: URLs fijas a localhost -- no hay todavia empaquetado/despliegue
// decidido para la MMI (D-09 solo cubre el backend); revisar cuando exista.
//
// Singleton deliberado (paso 3, docs/diseno/inventario-ui.md): antes de
// AppShell, solo una vista (una ruta) estaba montada a la vez, así que cada
// `useGateway()` de fábrica abría su propio WebSocket sin problema. El
// mosaico monta hasta 4 vistas a la vez -- sin singleton, cada panel abriría
// una conexión WS y un fetchStatus() independientes, y biteFaults/control
// quedarían desincronizados entre paneles. Todo el estado reactivo y la
// conexión WS se crean una sola vez, a nivel de módulo; `useGateway()` sólo
// devuelve las mismas referencias.
import { useWebSocket } from '@vueuse/core'
import { computed, ref, shallowRef } from 'vue'
import type {
  AntennaMessage,
  BiteFaultSummary,
  ControlAuthorityState,
  ControlJobAccepted,
  ControlJobStatusResponse,
  DspStreamStatus,
  SetControlModeRequest,
  SystemStatusSnapshot,
  WsMessage,
} from '@/types/mmi'
import type { LampState } from '@/types/shell'

export interface SessionInfo {
  rcp_version: string
  started_at_wall: string
}

export const GATEWAY_HTTP = 'http://127.0.0.1:8000'
const GATEWAY_WS = 'ws://127.0.0.1:8000/ws'

const MAX_LOG = 200

const messages = ref<WsMessage[]>([])
const control = shallowRef<ControlAuthorityState | null>(null)
const antenna = shallowRef<AntennaMessage['position'] | null>(null)
const dsp = shallowRef<DspStreamStatus | null>(null)
const sessionInfo = shallowRef<SessionInfo | null>(null)
// clave: signal_id -- mismo dato que app.state.bite_since_wall del lado del gateway,
// reconstruido aca a partir del snapshot inicial + BiteEventMessage en vivo.
const biteFaults = ref<Map<string, BiteFaultSummary>>(new Map())
// hal_connected llega en cada /api/status pero no viaja por WS -- se guarda
// aparte para que A6/A1 (indicadores SD/RD) lo puedan leer de forma reactiva
// sin que cada vista tenga que llamar fetchStatus() y desempacarlo ella misma.
const halConnected = shallowRef<boolean | null>(null)

// A2 Connection/Login (docs/diseno/inventario-ui.md): motivo del último
// cierre/fallo del WS, para mostrar un error legible en vez de solo
// "CLOSED". `CloseEvent.reason` suele venir vacío en cierres de red (no es
// un cierre de protocolo), así que esto es best-effort, no garantizado.
const lastCloseReason = shallowRef<string | null>(null)

// A6/B8: "silenciar/reconocer" (docs/diseno/inventario-ui.md, B8) -- reconocer
// no borra las fallas activas, sólo apaga el semáforo hasta la PRÓXIMA falla
// nueva. alarmAckedAt es la marca de tiempo del último reconocimiento; toda
// falla con since_wall posterior vuelve a encender el semáforo aunque se haya
// reconocido antes. Vive aquí (no en BiteMessagesView) porque B8 exige estar
// sincronizado con el resumen de alarma del Control Center (A1/A6).
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
  const res = await fetch(`${GATEWAY_HTTP}/api/status`)
  if (!res.ok) throw new Error(`GET /api/status: HTTP ${res.status}`)
  const snapshot = (await res.json()) as SystemStatusSnapshot
  control.value = snapshot.control
  antenna.value = snapshot.antenna
  dsp.value = snapshot.dsp
  halConnected.value = snapshot.hal_connected
  biteFaults.value = new Map(snapshot.active_bite_faults.map((f) => [f.signal_id, f]))
  return snapshot
}

async function setControlMode(req: SetControlModeRequest): Promise<ControlAuthorityState> {
  const res = await fetch(`${GATEWAY_HTTP}/api/control`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) throw new Error(`POST /api/control: HTTP ${res.status}`)
  const state = (await res.json()) as ControlAuthorityState
  control.value = state
  return state
}

// Ejecucion de rutinas de control (POST /api/control/*, ver core/contracts/mmi.py
// y src/adapters/gateway/app.py) -- D-12: el POST ya no bloquea hasta que la
// rutina termina (podia ser hasta timeout_s, minutos en antenna-positioning o
// power-on con caldeo real). Devuelve un job_id de inmediato (202); esta funcion
// sondea GET /api/control/jobs/{job_id} hasta que el job termina y devuelve el
// RoutineResult -- cada vista sigue viendo la misma forma "await, obtengo el
// resultado final" que ya tenia, solo que ahora puede tardar de verdad sin
// dejar el fetch original colgado.
const CONTROL_JOB_POLL_INTERVAL_MS = 400

async function runControlJob<T>(path: string, body?: unknown, onJobId?: (jobId: string) => void): Promise<T> {
  const res = await fetch(`${GATEWAY_HTTP}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST ${path}: HTTP ${res.status} — ${detail}`)
  }
  const accepted = (await res.json()) as ControlJobAccepted
  onJobId?.(accepted.job_id)

  while (true) {
    const jobRes = await fetch(`${GATEWAY_HTTP}/api/control/jobs/${accepted.job_id}`)
    if (!jobRes.ok) throw new Error(`GET /api/control/jobs/${accepted.job_id}: HTTP ${jobRes.status}`)
    const job = (await jobRes.json()) as ControlJobStatusResponse
    if (job.status === 'done') {
      if (job.error) throw new Error(`job ${job.job_id} (${job.routine}) fallo: ${job.error}`)
      return job.result as T
    }
    await new Promise((resolve) => setTimeout(resolve, CONTROL_JOB_POLL_INTERVAL_MS))
  }
}

// Cancela un job en curso (POST /api/control/jobs/{job_id}/cancel) -- cada
// rutina de movimiento/Scan Controller ya se encarga de detener el eje que
// estuviera comandando antes de que el job quede en `done` (ver
// adapters/gateway/app.py, `_start_control_job`/docstrings de
// core/control_routines/antenna_*.py). Idempotente del lado del backend:
// si el job ya termino, esto no falla, solo devuelve su estado actual.
async function cancelControlJob(jobId: string): Promise<ControlJobStatusResponse> {
  const res = await fetch(`${GATEWAY_HTTP}/api/control/jobs/${jobId}/cancel`, { method: 'POST' })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST /api/control/jobs/${jobId}/cancel: HTTP ${res.status} — ${detail}`)
  }
  return (await res.json()) as ControlJobStatusResponse
}

// El WebSocket se crea una sola vez, en el primer useGateway() que se
// invoque (normalmente App.vue al montar) -- no a nivel de módulo puro,
// porque useWebSocket registra limpieza vía onScopeDispose y conviene que
// esa primera llamada ocurra dentro de un setup() real.
let ws: ReturnType<typeof useWebSocket> | null = null

function ensureConnected() {
  if (ws) return ws
  ws = useWebSocket(GATEWAY_WS, {
    autoReconnect: { retries: -1, delay: 1000 },
    onConnected() {
      lastCloseReason.value = null
    },
    onDisconnected(_socket, event) {
      lastCloseReason.value = event.reason || `código ${event.code}`
    },
    onError() {
      lastCloseReason.value = 'error de red'
    },
    onMessage(_socket, event) {
      const msg = JSON.parse(event.data) as WsMessage
      messages.value.push(msg)
      if (messages.value.length > MAX_LOG) messages.value.shift()

      if (msg.type === 'session') {
        control.value = msg.control
        sessionInfo.value = { rcp_version: msg.rcp_version, started_at_wall: msg.started_at_wall }
      }
      if (msg.type === 'antenna') antenna.value = msg.position
      if (msg.type === 'event' && msg.kind === 'control_mode_changed') {
        // el gateway ya mando el nuevo ControlAuthorityState via el POST que
        // origino este evento -- aca solo reflejamos que hubo un cambio
        // hecho por otro cliente; el estado real llega por /api/status.
      }
      if (msg.type === 'bite_event') {
        const next = new Map(biteFaults.value)
        if (msg.transition === 'fault') {
          next.set(msg.signal_id, { signal_id: msg.signal_id, detail: msg.detail, since_wall: msg.at_wall })
        } else {
          next.delete(msg.signal_id)
        }
        biteFaults.value = next
      }
    },
  })
  return ws
}

export function useGateway() {
  const { status, send, open, close } = ensureConnected()
  return {
    status,
    lastCloseReason,
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
    open,
    close,
  }
}
