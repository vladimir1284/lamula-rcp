<!--
  PowerMonitorView.vue: Vista B7 — Power Monitor (VSWR).
  Gaps documentados:
  1. No hay Profibus en este sistema -- una sola conexion Modbus multiplexada
     (D-06, ver simulated_hal.py) hace de "bus status" real. `bus_ok` es
     `hal_connected`, no una senal Profibus fabricada.
  2. Reverse Power (`tx.tx_reflected_power_sample`) no tiene respaldo de
     hardware real todavia -- PEND-29 en radar_emulator: modulo/unit_id
     inventados, sin sensor confirmado. VSWR calculado a partir de ese valor
     hereda la misma incertidumbre.
  3. Sin limite de fabrica confirmado (mismo criterio que PEND-RCP-07):
     `limits` empieza en null, los semaforos quedan neutros hasta el primer
     "Set" del operador -- no se fabrica un umbral de partida.
-->
<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import IndicatorLamp from '@/components/shell/IndicatorLamp.vue'
import { useGateway } from '@/composables/useGateway'
import type { LampState } from '@/types/shell'
import type { PowerMeasurementLimits, PowerMonitorSnapshot } from '@/types/mmi'

const { fetchPowerMonitor, setPowerLimits, savePowerLimits } = useGateway()

const snapshot = ref<PowerMonitorSnapshot | null>(null)
const draft = ref<PowerMeasurementLimits>({ forward_limit_kw: 0, reverse_limit_kw: 0, vswr_limit: 0 })
const draftTouched = ref(false)
const busy = ref(false)
const error = ref<string | null>(null)

let pollTimer: ReturnType<typeof setInterval> | null = null

async function refresh() {
  try {
    snapshot.value = await fetchPowerMonitor()
    if (!draftTouched.value && snapshot.value.limits) {
      draft.value = { ...snapshot.value.limits }
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

// "Set" (volatil, D-10 mismo criterio que el resto de este contrato): manda el
// draft al gateway pero no lo persiste en disco -- se pierde al reiniciar
// hasta que se pulse "Save".
async function doSet() {
  busy.value = true
  error.value = null
  try {
    const limits = await setPowerLimits(draft.value)
    if (snapshot.value) snapshot.value.limits = limits
    draftTouched.value = false
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    busy.value = false
  }
}

// "Save": persiste a disco (data/power_limits.json) -- el backend rechaza con
// 409 si no hay limites puestos por "Set" todavia, o si el radar esta
// radiando (RAVIS Sec.7.7: bloqueado mientras radia).
async function doSave() {
  busy.value = true
  error.value = null
  try {
    await doSet()
    await savePowerLimits()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    busy.value = false
  }
}

function lampState(value: number | null, limit: number | undefined, busOk: boolean): LampState {
  if (!busOk) return 'neutral'
  if (value === null || limit === undefined || !snapshot.value?.limits) return 'neutral'
  return value <= limit ? 'ok' : 'fault'
}

function fmt(v: number | null): string {
  return v === null ? '— (sin lectura)' : v.toFixed(1)
}

onMounted(() => {
  refresh()
  pollTimer = setInterval(refresh, 1000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 overflow-auto p-3">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold text-foreground">B7 Power Monitor (VSWR)</h2>
      <IndicatorLamp
        label="Bus Modbus"
        :state="snapshot?.bus_ok ? 'ok' : 'fault'"
        :detail="snapshot?.bus_ok ? 'Conectado' : 'Sin comunicacion Modbus -- lecturas no confiables'"
      />
    </div>

    <p v-if="error" class="text-xs font-medium text-destructive">{{ error }}</p>
    <p v-if="!snapshot?.limits" class="text-xs text-muted-foreground">
      Sin limite configurado todavia -- ponga valores y pulse "Set" (o "Save" para persistir).
    </p>

    <Card>
      <CardHeader>
        <CardTitle>Mediciones</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="border-b bg-muted/50 text-muted-foreground">
              <tr>
                <th class="p-2 font-medium">Medicion</th>
                <th class="p-2 font-medium">Valor</th>
                <th class="p-2 font-medium">Limite</th>
                <th class="p-2 font-medium">Estado</th>
              </tr>
            </thead>
            <tbody class="divide-y">
              <tr>
                <td class="p-2 font-medium">Forward Power [kW]</td>
                <td class="p-2 font-mono">{{ fmt(snapshot?.forward_power_kw ?? null) }}</td>
                <td class="p-2">
                  <Input v-model.number="draft.forward_limit_kw" type="number" step="0.1" class="h-7 w-24 text-xs"
                    @input="draftTouched = true" />
                </td>
                <td class="p-2">
                  <IndicatorLamp label="" :state="lampState(snapshot?.forward_power_kw ?? null, snapshot?.limits?.forward_limit_kw, snapshot?.bus_ok ?? false)" />
                </td>
              </tr>
              <tr>
                <td class="p-2 font-medium">Reverse Power [kW]</td>
                <td class="p-2 font-mono">{{ fmt(snapshot?.reverse_power_kw ?? null) }}</td>
                <td class="p-2">
                  <Input v-model.number="draft.reverse_limit_kw" type="number" step="0.1" class="h-7 w-24 text-xs"
                    @input="draftTouched = true" />
                </td>
                <td class="p-2">
                  <IndicatorLamp label="" :state="lampState(snapshot?.reverse_power_kw ?? null, snapshot?.limits?.reverse_limit_kw, snapshot?.bus_ok ?? false)" />
                </td>
              </tr>
              <tr>
                <td class="p-2 font-medium">VSWR</td>
                <td class="p-2 font-mono">{{ fmt(snapshot?.vswr ?? null) }}</td>
                <td class="p-2">
                  <Input v-model.number="draft.vswr_limit" type="number" step="0.01" class="h-7 w-24 text-xs"
                    @input="draftTouched = true" />
                </td>
                <td class="p-2">
                  <IndicatorLamp label="" :state="lampState(snapshot?.vswr ?? null, snapshot?.limits?.vswr_limit, snapshot?.bus_ok ?? false)" />
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="mt-3 flex flex-wrap items-center gap-2">
          <Button size="sm" :disabled="busy" @click="doSet">Set</Button>
          <Button size="sm" variant="outline" :disabled="busy || snapshot?.radiating" @click="doSave">Save</Button>
          <p v-if="snapshot?.radiating" class="text-xs text-muted-foreground">
            Save bloqueado: el radar esta radiando. Apague la radiacion antes de guardar.
          </p>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
