<script setup lang="ts">
// Componente BiteMessageTable (docs/diseno/inventario-ui.md, B8/B9):
// Tabla reusable para renderizar mensajes BiTE (tanto en vivo como en histórico B9).
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { BiteEventMessage } from '@/types/mmi'

defineProps<{
  rows: BiteEventMessage[]
}>()
</script>

<template>
  <p v-if="rows.length === 0" class="text-sm text-muted-foreground">
    Sin mensajes BiTE para mostrar.
  </p>
  <ScrollArea v-else class="min-h-0 flex-1">
    <table class="w-full text-left text-xs">
      <thead class="text-muted-foreground">
        <tr>
          <th class="py-1 pr-2 font-medium">Nivel</th>
          <th class="py-1 pr-2 font-medium">Signal ID</th>
          <th class="py-1 pr-2 font-medium">Fecha</th>
          <th class="py-1 font-medium">Titular</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(m, i) in rows"
          :key="`${m.signal_id}-${m.at_wall}-${i}`"
          class="border-t border-border"
        >
          <td class="py-1 pr-2">
            <Badge :variant="m.transition === 'fault' ? 'destructive' : 'secondary'">
              {{ m.transition === 'fault' ? 'error' : 'resuelto' }}
            </Badge>
          </td>
          <td class="py-1 pr-2 font-medium">{{ m.signal_id }}</td>
          <td class="py-1 pr-2 text-muted-foreground">
            {{ new Date(m.at_wall).toLocaleString() }}
          </td>
          <td class="py-1">{{ m.detail }}</td>
        </tr>
      </tbody>
    </table>
  </ScrollArea>
</template>
