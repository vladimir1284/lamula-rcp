<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useGateway } from '@/composables/useGateway'

const { control, sessionInfo } = useGateway()

const now = ref(Date.now())
let timer: ReturnType<typeof setInterval> | undefined

onMounted(() => {
  timer = setInterval(() => {
    now.value = Date.now()
  }, 1000)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})

function formatUptime(startedAtWall: string): string {
  const totalS = Math.max(0, Math.floor((now.value - new Date(startedAtWall).getTime()) / 1000))
  const h = Math.floor(totalS / 3600)
  const m = Math.floor((totalS % 3600) / 60)
  const s = totalS % 60
  return `${h}h ${m}m ${s}s`
}

const controlVariant = computed(() => (control.value?.mode === 'active' ? 'default' : 'secondary'))
</script>

<template>
  <div class="mx-auto flex max-w-3xl flex-col gap-4 p-6">
    <h1 class="text-2xl font-semibold">System Information</h1>

    <Card>
      <CardHeader>
        <CardTitle>RCP</CardTitle>
      </CardHeader>
      <CardContent class="flex flex-col gap-2 text-sm">
        <template v-if="sessionInfo">
          <span>Versión: {{ sessionInfo.rcp_version }}</span>
          <span>Arrancado: {{ new Date(sessionInfo.started_at_wall).toLocaleString() }}</span>
          <span>Uptime: {{ formatUptime(sessionInfo.started_at_wall) }}</span>
        </template>
        <span v-else class="text-muted-foreground">sin sesión todavía (esperando WS)</span>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Autoridad de control</CardTitle>
      </CardHeader>
      <CardContent class="flex flex-wrap items-center gap-3 text-sm">
        <template v-if="control">
          <Badge :variant="controlVariant">{{ control.mode }}</Badge>
          <span>{{ control.actor }} desde {{ new Date(control.since_wall).toLocaleTimeString() }}</span>
        </template>
        <span v-else class="text-muted-foreground">sin dato todavía</span>
      </CardContent>
    </Card>
  </div>
</template>
