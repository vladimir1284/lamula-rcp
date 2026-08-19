<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { useGateway } from '@/composables/useGateway'
import type { WsMessage } from '@/types/mmi'

const { status, messages, control, antenna, dsp, fetchStatus, setControlMode } = useGateway()

const actor = ref('operador')
const busy = ref(false)
const error = ref<string | null>(null)

const wsStatusVariant = computed(() => {
  if (status.value === 'OPEN') return 'default'
  if (status.value === 'CONNECTING') return 'secondary'
  return 'destructive'
})

const controlVariant = computed(() => (control.value?.mode === 'active' ? 'default' : 'secondary'))

function messageLabel(msg: WsMessage): string {
  if (msg.type === 'event') return `${msg.kind} (${msg.actor})`
  if (msg.type === 'antenna') return `az=${msg.position.az_deg.toFixed(1)} el=${msg.position.el_deg.toFixed(1)}`
  if (msg.type === 'session') return `rcp ${msg.rcp_version}`
  return ''
}

async function toggleControl() {
  if (!control.value) return
  busy.value = true
  error.value = null
  try {
    const nextMode = control.value.mode === 'active' ? 'passive' : 'active'
    await setControlMode({ mode: nextMode, actor: actor.value })
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    busy.value = false
  }
}

onMounted(async () => {
  try {
    await fetchStatus()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
})
</script>

<template>
  <div class="mx-auto flex max-w-3xl flex-col gap-4 p-6">
    <h1 class="text-2xl font-semibold">Control Center</h1>

    <Card>
      <CardHeader>
        <CardTitle>Conexión al gateway</CardTitle>
      </CardHeader>
      <CardContent class="flex flex-wrap items-center gap-3">
        <Badge :variant="wsStatusVariant">WS {{ status }}</Badge>
        <Badge :variant="dsp?.connected ? 'default' : 'secondary'">
          DSP {{ dsp?.connected ? 'conectado' : 'sin conexión' }}
        </Badge>
        <span v-if="error" class="text-destructive">{{ error }}</span>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Autoridad de control</CardTitle>
      </CardHeader>
      <CardContent class="flex flex-wrap items-center gap-3">
        <Badge :variant="controlVariant">{{ control?.mode ?? '...' }}</Badge>
        <span v-if="control" class="text-sm text-muted-foreground">
          {{ control.actor }} desde {{ new Date(control.since_wall).toLocaleTimeString() }}
        </span>
        <Separator orientation="vertical" class="h-6" />
        <Input v-model="actor" placeholder="actor" class="w-40" />
        <Button :disabled="!control || busy" @click="toggleControl">
          {{ control?.mode === 'active' ? 'Ceder control' : 'Tomar control' }}
        </Button>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Antena</CardTitle>
      </CardHeader>
      <CardContent class="flex flex-wrap items-center gap-4 text-sm">
        <template v-if="antenna">
          <span>az: {{ antenna.az_deg.toFixed(2) }}°</span>
          <span>el: {{ antenna.el_deg.toFixed(2) }}°</span>
          <Badge v-if="!antenna.az_valid || !antenna.el_valid" variant="destructive">encoder inválido</Badge>
          <Badge v-if="antenna.degraded" variant="secondary">degradado</Badge>
        </template>
        <span v-else class="text-muted-foreground">sin posición todavía</span>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Log de mensajes</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea class="h-64 w-full">
          <ul class="flex flex-col gap-1 text-sm">
            <li v-for="(msg, i) in [...messages].reverse()" :key="i" class="flex items-center gap-2">
              <Badge variant="outline" class="w-20 shrink-0 justify-center">{{ msg.type }}</Badge>
              <span>{{ messageLabel(msg) }}</span>
            </li>
          </ul>
        </ScrollArea>
      </CardContent>
    </Card>
  </div>
</template>
