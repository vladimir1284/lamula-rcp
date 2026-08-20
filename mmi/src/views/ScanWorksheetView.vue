<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { MOMENT_IDS, type MomentId, type ScanCut } from '@/types/scan'

const GATEWAY_HTTP = 'http://127.0.0.1:8000'

const worksheet = ref<ScanCut[]>([])
const loadError = ref<string | null>(null)
const submitError = ref<string | null>(null)

type Mode = 'ppi' | 'rhi'
const mode = ref<Mode>('ppi')

// Campos compartidos por ambos modos.
const prfHz = ref(1000)
const pulseWidthUs = ref(1)
const selectedMoments = ref<Set<MomentId>>(new Set(['UZ']))

// Campos PPI.
const elevationDeg = ref(0)
const azimuthStartDeg = ref(0)
const azimuthEndDeg = ref(360)

// Campos RHI.
const azimuthDeg = ref(0)
const elevationStartDeg = ref(-1)
const elevationEndDeg = ref(90)

function toggleMoment(id: MomentId) {
  const next = new Set(selectedMoments.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  selectedMoments.value = next
}

// Validacion de cliente minima -- solo lo visible en el form (rangos,
// start != end, al menos un moment). La validacion completa (Pydantic) la
// hace el backend; esto es feedback antes de golpear la red, no un
// duplicado de esa logica.
const clientError = computed(() => {
  if (selectedMoments.value.size === 0) return 'seleccione al menos un moment'
  if (mode.value === 'ppi') {
    if (elevationDeg.value < -90 || elevationDeg.value > 90) return 'elevation_deg fuera de rango (-90..90)'
    if (azimuthStartDeg.value < 0 || azimuthStartDeg.value >= 360) return 'azimuth_start_deg fuera de rango (0..<360)'
    if (azimuthEndDeg.value < 0 || azimuthEndDeg.value > 360) return 'azimuth_end_deg fuera de rango (0..360)'
    if (azimuthStartDeg.value === azimuthEndDeg.value) return 'azimuth_start_deg y azimuth_end_deg no pueden ser iguales'
  } else {
    if (azimuthDeg.value < 0 || azimuthDeg.value >= 360) return 'azimuth_deg fuera de rango (0..<360)'
    if (elevationStartDeg.value < -90 || elevationStartDeg.value > 90) return 'elevation_start_deg fuera de rango (-90..90)'
    if (elevationEndDeg.value < -90 || elevationEndDeg.value > 90) return 'elevation_end_deg fuera de rango (-90..90)'
    if (elevationStartDeg.value === elevationEndDeg.value) return 'elevation_start_deg y elevation_end_deg no pueden ser iguales'
  }
  if (prfHz.value <= 0) return 'prf_hz debe ser mayor que 0'
  if (pulseWidthUs.value <= 0) return 'pulse_width_us debe ser mayor que 0'
  return null
})

function buildCut(): ScanCut {
  const moments = [...selectedMoments.value]
  if (mode.value === 'ppi') {
    return {
      mode: 'ppi',
      elevation_deg: elevationDeg.value,
      azimuth_start_deg: azimuthStartDeg.value,
      azimuth_end_deg: azimuthEndDeg.value,
      prf_hz: prfHz.value,
      pulse_width_us: pulseWidthUs.value,
      moments,
    }
  }
  return {
    mode: 'rhi',
    azimuth_deg: azimuthDeg.value,
    elevation_start_deg: elevationStartDeg.value,
    elevation_end_deg: elevationEndDeg.value,
    prf_hz: prfHz.value,
    pulse_width_us: pulseWidthUs.value,
    moments,
  }
}

async function fetchWorksheet() {
  const res = await fetch(`${GATEWAY_HTTP}/api/scan/worksheet`)
  if (!res.ok) throw new Error(`GET /api/scan/worksheet: HTTP ${res.status}`)
  worksheet.value = (await res.json()) as ScanCut[]
}

async function addCut() {
  submitError.value = null
  if (clientError.value) {
    submitError.value = clientError.value
    return
  }
  const res = await fetch(`${GATEWAY_HTTP}/api/scan/worksheet`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(buildCut()),
  })
  if (!res.ok) {
    const body = await res.text()
    submitError.value = `POST /api/scan/worksheet: HTTP ${res.status} — ${body}`
    return
  }
  worksheet.value = (await res.json()) as ScanCut[]
}

async function removeCut(index: number) {
  const res = await fetch(`${GATEWAY_HTTP}/api/scan/worksheet/${index}`, { method: 'DELETE' })
  if (!res.ok) return
  worksheet.value = (await res.json()) as ScanCut[]
}

function summarize(cut: ScanCut): string {
  if (cut.mode === 'ppi') {
    return `elev ${cut.elevation_deg}° · az ${cut.azimuth_start_deg}°→${cut.azimuth_end_deg}°`
  }
  return `az ${cut.azimuth_deg}° · elev ${cut.elevation_start_deg}°→${cut.elevation_end_deg}°`
}

onMounted(() => {
  fetchWorksheet().catch((e) => {
    loadError.value = e instanceof Error ? e.message : String(e)
  })
})
</script>

<template>
  <div class="mx-auto flex max-w-3xl flex-col gap-4 p-6">
    <h1 class="text-2xl font-semibold">Scan Worksheet</h1>
    <p class="text-sm text-muted-foreground">
      Cortes de escaneo manuales (PPI/RHI) -- sin scheduler automatico ni ejecucion todavia.
    </p>

    <Card>
      <CardHeader>
        <CardTitle>Nuevo corte</CardTitle>
      </CardHeader>
      <CardContent class="flex flex-col gap-3">
        <div class="flex gap-4 text-sm">
          <label class="flex items-center gap-1">
            <input type="radio" value="ppi" v-model="mode">
            PPI
          </label>
          <label class="flex items-center gap-1">
            <input type="radio" value="rhi" v-model="mode">
            RHI
          </label>
        </div>

        <div v-if="mode === 'ppi'" class="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <label class="flex flex-col gap-1 text-sm">
            elevation_deg
            <Input v-model.number="elevationDeg" type="number" min="-90" max="90" step="0.1" />
          </label>
          <label class="flex flex-col gap-1 text-sm">
            azimuth_start_deg
            <Input v-model.number="azimuthStartDeg" type="number" min="0" max="359.999" step="0.1" />
          </label>
          <label class="flex flex-col gap-1 text-sm">
            azimuth_end_deg
            <Input v-model.number="azimuthEndDeg" type="number" min="0" max="360" step="0.1" />
          </label>
        </div>
        <div v-else class="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <label class="flex flex-col gap-1 text-sm">
            azimuth_deg
            <Input v-model.number="azimuthDeg" type="number" min="0" max="359.999" step="0.1" />
          </label>
          <label class="flex flex-col gap-1 text-sm">
            elevation_start_deg
            <Input v-model.number="elevationStartDeg" type="number" min="-90" max="90" step="0.1" />
          </label>
          <label class="flex flex-col gap-1 text-sm">
            elevation_end_deg
            <Input v-model.number="elevationEndDeg" type="number" min="-90" max="90" step="0.1" />
          </label>
        </div>

        <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <label class="flex flex-col gap-1 text-sm">
            prf_hz
            <Input v-model.number="prfHz" type="number" min="0.01" step="1" />
          </label>
          <label class="flex flex-col gap-1 text-sm">
            pulse_width_us
            <Input v-model.number="pulseWidthUs" type="number" min="0.01" step="0.1" />
          </label>
        </div>

        <div class="flex flex-col gap-1 text-sm">
          moments
          <div class="flex flex-wrap gap-2">
            <label
              v-for="id in MOMENT_IDS"
              :key="id"
              class="flex items-center gap-1 rounded border px-2 py-1"
            >
              <input
                type="checkbox"
                :checked="selectedMoments.has(id)"
                @change="toggleMoment(id)"
              >
              {{ id }}
            </label>
          </div>
        </div>

        <p v-if="submitError" class="text-sm text-destructive">{{ submitError }}</p>
        <div>
          <Button @click="addCut">Agregar</Button>
        </div>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Worksheet ({{ worksheet.length }} corte(s))</CardTitle>
      </CardHeader>
      <CardContent class="flex flex-col gap-2">
        <p v-if="loadError" class="text-sm text-destructive">{{ loadError }}</p>
        <p v-else-if="worksheet.length === 0" class="text-sm text-muted-foreground">
          Sin cortes todavia.
        </p>
        <div
          v-for="(cut, index) in worksheet"
          :key="index"
          class="flex flex-wrap items-center justify-between gap-2 rounded border p-2 text-sm"
        >
          <div class="flex flex-wrap items-center gap-2">
            <Badge variant="default">{{ cut.mode.toUpperCase() }}</Badge>
            <span>{{ summarize(cut) }}</span>
            <span class="text-muted-foreground">
              PRF {{ cut.prf_hz }} Hz · PW {{ cut.pulse_width_us }} µs · {{ cut.moments.join(', ') }}
            </span>
          </div>
          <Button variant="destructive" size="sm" @click="removeCut(index)">Eliminar</Button>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
