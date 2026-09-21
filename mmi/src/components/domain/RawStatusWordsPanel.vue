<script setup lang="ts">
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import BitmaskStatusList, { type BitmaskBitDef } from '@/components/domain/BitmaskStatusList.vue'

const props = defineProps<{
  biteFlags: number
  capabilityFlags: number
}>()

function formatHex(val: number): string {
  return '0x' + (val >>> 0).toString(16).padStart(8, '0').toUpperCase()
}

const BITE_FLAG_DEFS: BitmaskBitDef[] = [
  { bit: 1, label: 'INGEST_DROP', description: 'Pérdida de datos de entrada', severity: 'fault' },
  { bit: 2, label: 'QUEUE_OVERFLOW', description: 'Desbordamiento de cola', severity: 'fault' },
  { bit: 4, label: 'DRX_LINK_DOWN', description: 'Enlace DRX caído', severity: 'fault' },
  { bit: 8, label: 'DRX_CONFIG_REJECTED', description: 'Configuración DRX rechazada', severity: 'warn' },
  { bit: 16, label: 'TRIGGER_DRIFT', description: 'Deriva de periodo de trigger', severity: 'warn' },
  { bit: 32, label: 'NOISE_FLOOR_DRIFT', description: 'Deriva de nivel de ruido', severity: 'warn' },
  { bit: 64, label: 'MOMENT_OVERRUN', description: 'Exceso de tiempo en momentos', severity: 'fault' },
  { bit: 128, label: 'CALIBRATION_STALE', description: 'Calibración desactualizada', severity: 'warn' },
]

const CAPABILITY_FLAG_DEFS: BitmaskBitDef[] = [
  { bit: 1, label: 'DUAL_POL', description: 'Polarización dual', severity: 'info' },
  { bit: 2, label: 'SPECTRAL_ESTIMATOR', description: 'Estimador espectral', severity: 'info' },
  { bit: 4, label: 'DUAL_PRF', description: 'Dual PRF deambiguación', severity: 'info' },
  { bit: 8, label: 'STAGGERED_PRT', description: 'STAGGERED PRT', severity: 'info' },
  { bit: 16, label: 'RANGE_DEALIAS', description: 'Desambiguación en rango', severity: 'info' },
  { bit: 32, label: 'RFI_FILTER', description: 'Filtro RFI', severity: 'info' },
  { bit: 64, label: 'SPECTRUM_FEED', description: 'Alimentación espectral', severity: 'info' },
  { bit: 128, label: 'IQ_ARCHIVE', description: 'Archivo IQ', severity: 'info' },
  { bit: 256, label: 'SZ864', description: 'Algoritmo SZ864', severity: 'info' },
]
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <Card>
      <CardHeader class="pb-2">
        <CardTitle class="text-sm font-semibold flex justify-between items-center">
          <span>Palabra de Estado BiTE (`bite_flags`)</span>
          <span class="font-mono text-xs font-normal text-muted-foreground">{{ formatHex(props.biteFlags) }}</span>
        </CardTitle>
      </CardHeader>
      <CardContent class="text-xs space-y-2">
        <BitmaskStatusList :value="props.biteFlags" :bits="BITE_FLAG_DEFS" empty-text="Sin fallas activas (0x00000000)" />
      </CardContent>
    </Card>

    <Card>
      <CardHeader class="pb-2">
        <CardTitle class="text-sm font-semibold flex justify-between items-center">
          <span>Capacidades Habilitadas (`capability_flags`)</span>
          <span class="font-mono text-xs font-normal text-muted-foreground">{{ formatHex(props.capabilityFlags) }}</span>
        </CardTitle>
      </CardHeader>
      <CardContent class="text-xs space-y-2">
        <BitmaskStatusList :value="props.capabilityFlags" :bits="CAPABILITY_FLAG_DEFS" empty-text="Sin capacidades declaradas" />
      </CardContent>
    </Card>
  </div>
</template>
