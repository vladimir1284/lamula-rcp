<script setup lang="ts">
import { ref } from 'vue'
import { Button } from '@/components/ui/button'

const props = defineProps<{
  configData?: Record<string, unknown>
  filename?: string
}>()

const copied = ref(false)

function getExportPayload(): Record<string, unknown> {
  if (props.configData) {
    return props.configData
  }
  // Genera un snapshot completo por defecto de la configuración DSP
  return {
    dsp_config_version: 'v1.3',
    exported_at: new Date().toISOString(),
    source: 'E1 — DSP Setup Hub',
    e2_processing_options: {
      spectral_window: 'Hamming',
      r2_processing: 'User',
      clutter_microsuppression: 'User',
      linearized_saturation_headroom_db: 6.0,
      interference_filter: 'Alg.1',
    },
    e3_thresholds_matrix: {
      dbz_log_db: 0.75,
      dbz_csr_db: -18.0,
      tcf_mask: 'LOG & CSR',
    },
    e4_clutter_filters: [
      { id: 1, type: 'Fixed', win: 'Hamming', width_pts: 3 },
      { id: 4, type: 'Variable', win: 'Hamming', hunt_pts: 5 },
    ],
    e5_trigger_setup: {
      prf_hz: 1200,
      pulse_width_index: 0,
      use_external_pretrigger: false,
    },
    e6_pulse_width_triggers: [
      { pw_index: 0, pw_name: 'SP', triggers: [{ start_us: 0, width_us: 1.0, high: true }] },
      { pw_index: 1, pw_name: 'LP', triggers: [{ start_us: 0, width_us: 2.0, high: true }] },
    ],
    e7_burst_pulse_afc: {
      tx_if_mhz: 30.0,
      rx_if_mhz: 30.0,
      afc_enabled: true,
      afc_servo: 'DC Coupled',
    },
    e8_transmissions: {
      modulation: 'None',
      chan_a: 'FixedFreq',
      chan_b: 'Unused',
    },
    e9_top_level: {
      ip_address: '192.168.1.100',
      clock_mhz: 60.0,
    },
    e10_debug_options: {
      noise_level_sim_db: -110.0,
      nyquist_sign_flip: false,
    },
  }
}

function exportJson() {
  const payload = getExportPayload()
  const jsonStr = JSON.stringify(payload, null, 2)
  const blob = new Blob([jsonStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = props.filename || `dsp-config-export-${new Date().toISOString().slice(0, 10)}.json`
  a.click()
  URL.revokeObjectURL(url)
}

async function copyToClipboard() {
  const payload = getExportPayload()
  const jsonStr = JSON.stringify(payload, null, 2)
  try {
    await navigator.clipboard.writeText(jsonStr)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
    console.error('Error al copiar al portapapeles:', err)
  }
}
</script>

<template>
  <div class="flex items-center gap-2">
    <Button size="sm" variant="outline" @click="exportJson">
      <span class="mr-1">📥</span> Exportar Config (JSON)
    </Button>
    <Button size="sm" variant="ghost" @click="copyToClipboard">
      <span class="mr-1">📋</span> {{ copied ? '¡Copiado!' : 'Copiar' }}
    </Button>
  </div>
</template>
