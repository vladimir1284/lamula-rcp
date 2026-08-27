<script setup lang="ts">
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import ControlAuthorityCard from '@/components/domain/ControlAuthorityCard.vue'
import UptimeDisplay from '@/components/domain/UptimeDisplay.vue'
import { useGateway } from '@/composables/useGateway'

const { control, sessionInfo } = useGateway()
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
          <span>Uptime: <UptimeDisplay :started-at-wall="sessionInfo.started_at_wall" /></span>
        </template>
        <span v-else class="text-muted-foreground">sin sesión todavía (esperando WS)</span>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Autoridad de control</CardTitle>
      </CardHeader>
      <CardContent>
        <ControlAuthorityCard :control="control" />
      </CardContent>
    </Card>
  </div>
</template>
