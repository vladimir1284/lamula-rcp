// Cliente del gateway RCP<->MMI (src/adapters/gateway) -- REST + WS sobre el
// sobre ya congelado en core/contracts/mmi.py (ver src/types/mmi.ts).
//
// PEND: URLs fijas a localhost -- no hay todavia empaquetado/despliegue
// decidido para la MMI (D-09 solo cubre el backend); revisar cuando exista.
import { useWebSocket } from '@vueuse/core'
import { ref, shallowRef } from 'vue'
import type {
  AntennaMessage,
  BiteFaultSummary,
  ControlAuthorityState,
  DspStreamStatus,
  SetControlModeRequest,
  SystemStatusSnapshot,
  WsMessage,
} from '@/types/mmi'

const GATEWAY_HTTP = 'http://127.0.0.1:8000'
const GATEWAY_WS = 'ws://127.0.0.1:8000/ws'

const MAX_LOG = 200

export function useGateway() {
  const messages = ref<WsMessage[]>([])
  const control = shallowRef<ControlAuthorityState | null>(null)
  const antenna = shallowRef<AntennaMessage['position'] | null>(null)
  const dsp = shallowRef<DspStreamStatus | null>(null)
  // clave: signal_id -- mismo dato que app.state.bite_since_wall del lado del gateway,
  // reconstruido aca a partir del snapshot inicial + BiteEventMessage en vivo.
  const biteFaults = ref<Map<string, BiteFaultSummary>>(new Map())

  const { status, send } = useWebSocket(GATEWAY_WS, {
    autoReconnect: { retries: -1, delay: 1000 },
    onMessage(_ws, event) {
      const msg = JSON.parse(event.data) as WsMessage
      messages.value.push(msg)
      if (messages.value.length > MAX_LOG) messages.value.shift()

      if (msg.type === 'session') control.value = msg.control
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

  async function fetchStatus(): Promise<SystemStatusSnapshot> {
    const res = await fetch(`${GATEWAY_HTTP}/api/status`)
    if (!res.ok) throw new Error(`GET /api/status: HTTP ${res.status}`)
    const snapshot = (await res.json()) as SystemStatusSnapshot
    control.value = snapshot.control
    antenna.value = snapshot.antenna
    dsp.value = snapshot.dsp
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

  return { status, messages, control, antenna, dsp, biteFaults, fetchStatus, setControlMode, send }
}
