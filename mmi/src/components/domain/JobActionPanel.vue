<script setup lang="ts">
// Patrón busy/jobId/result/error + ejecutar/cancelar vía runControlJob --
// antes repetido 4 veces dentro de ControlCenterView.vue (las cuatro
// rutinas de encendido) más una vez cada uno en el panel Posicionar
// (AntennaControlView.vue) y el panel Ejecutar (ScanWorksheetView.vue). El
// panel Jog de AntennaControlView.vue queda afuera a propósito: "Detener"
// no cancela un job por id, manda un comando nuevo (0V) -- semántica
// distinta, forzarlo aquí hubiera sido una abstracción falsa.
//
// El slot `params` es para controles que van en la MISMA fila que los
// botones (ej. el Input de warmup_timeout_s en TX/RX/AU power-on); cuando
// los parámetros van en su propio grid arriba (Posicionar, Ejecutar), el
// padre los renderiza fuera de este componente y el slot queda vacío.
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { RoutineResult } from '@/types/mmi'
import type { ScanCutResult } from '@/types/scan'

withDefaults(
  defineProps<{
    busy: boolean
    jobId?: string | null
    result?: RoutineResult | ScanCutResult | null
    error?: string | null
    runLabel?: string
    runningLabel?: string | null
    runDisabled?: boolean
    cancelLabel?: string
    busyText?: string | null
  }>(),
  {
    jobId: null,
    result: null,
    error: null,
    runLabel: 'Ejecutar',
    runningLabel: null,
    runDisabled: false,
    cancelLabel: 'Cancelar',
    busyText: null,
  },
)

defineEmits<{
  run: []
  cancel: []
}>()
</script>

<template>
  <div class="flex flex-col gap-2">
    <div class="flex flex-wrap items-center gap-2">
      <slot name="params" />
      <Button :disabled="runDisabled || busy" @click="$emit('run')">
        {{ busy && runningLabel ? runningLabel : runLabel }}
      </Button>
      <Button v-if="busy" variant="destructive" :disabled="!jobId" @click="$emit('cancel')">
        {{ cancelLabel }}
      </Button>
      <span v-if="busy && busyText" class="text-sm text-muted-foreground">{{ busyText }}</span>
      <span v-if="error" class="text-sm text-destructive">{{ error }}</span>
      <Badge v-if="result" :variant="result.outcome === 'success' ? 'default' : 'destructive'">
        {{ result.outcome }}
      </Badge>
    </div>
    <ul v-if="result" class="flex flex-col gap-0.5 text-xs text-muted-foreground">
      <li v-for="(s, i) in result.steps" :key="i">{{ s.ok ? '✓' : '✗' }} {{ s.signal_id }} — {{ s.detail }}</li>
    </ul>
  </div>
</template>
