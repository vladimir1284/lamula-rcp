<script setup lang="ts">
// Componente A4 MaintenanceUnlockCard (docs/diseno/inventario-ui.md):
// Permite desbloquear el nivel de acceso MANT ingresando contraseña, actor y
// duración en segundos. Muestra el estado activo con temporizador y botón para volver a OP.
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import type { MaintenanceState } from '@/types/mmi'

const props = defineProps<{
  maintenance: MaintenanceState | null
  busy?: boolean
  error?: string | null
}>()

const emit = defineEmits<{
  unlock: [payload: { password: string; actor: string; duration_s: number }]
  lock: []
}>()

const password = ref('')
const actor = ref('tecnico')
const durationS = ref(1800)

const now = ref(Date.now())
let timer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  timer = setInterval(() => {
    now.value = Date.now()
  }, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

const isMant = computed(() => props.maintenance?.level === 'MANT')

const remainingSeconds = computed(() => {
  if (!props.maintenance?.expires_wall) return 0
  const exp = new Date(props.maintenance.expires_wall).getTime()
  const diff = Math.floor((exp - now.value) / 1000)
  return diff > 0 ? diff : 0
})

const countdownFormatted = computed(() => {
  const sec = remainingSeconds.value
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}m ${s.toString().padStart(2, '0')}s`
})

function handleUnlock() {
  if (!password.value) return
  emit('unlock', {
    password: password.value,
    actor: actor.value || 'operador',
    duration_s: Number(durationS.value) || 1800,
  })
}
</script>

<template>
  <Card class="w-full max-w-md">
    <CardHeader>
      <div class="flex items-center justify-between gap-2">
        <CardTitle class="text-base">Desbloqueo de Mantenimiento (A4)</CardTitle>
        <Badge :variant="isMant ? 'destructive' : 'outline'">
          {{ maintenance?.level ?? 'OP' }}
        </Badge>
      </div>
      <CardDescription>
        Nivel de acceso MANT para calibración y parámetros del sistema.
      </CardDescription>
    </CardHeader>

    <CardContent class="flex flex-col gap-4 text-sm">
      <div v-if="isMant" class="flex flex-col gap-3 rounded-md border border-destructive/50 bg-destructive/10 p-3">
        <div class="flex items-center justify-between">
          <span class="font-medium text-destructive">Modo Mantenimiento Activo</span>
          <span class="font-mono font-semibold text-destructive">{{ countdownFormatted }}</span>
        </div>
        <div class="text-xs text-muted-foreground">
          <span>Actor: {{ maintenance?.actor ?? 'desconocido' }}</span>
          <span v-if="maintenance?.since_wall"> · Desde: {{ new Date(maintenance.since_wall).toLocaleTimeString() }}</span>
        </div>
        <Button variant="destructive" size="sm" :disabled="busy" @click="emit('lock')">
          Bloquear (Volver a OP)
        </Button>
      </div>

      <div v-else class="flex flex-col gap-3">
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium">Contraseña de mantenimiento</label>
          <Input
            v-model="password"
            type="password"
            placeholder="Contraseña..."
            :disabled="busy"
            @keyup.enter="handleUnlock"
          />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium">Actor</label>
            <Input v-model="actor" placeholder="Nombre..." :disabled="busy" />
          </div>
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium">Duración (segundos)</label>
            <Input v-model.number="durationS" type="number" min="10" step="60" :disabled="busy" />
          </div>
        </div>

        <p v-if="error" class="text-xs font-medium text-destructive">{{ error }}</p>

        <Button :disabled="!password || busy" @click="handleUnlock">
          Desbloquear Mantenimiento
        </Button>
      </div>
    </CardContent>
  </Card>
</template>
