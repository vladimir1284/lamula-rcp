<script setup lang="ts">
// Componente KeyValueTable (docs/diseno/inventario-ui.md, A7):
// Renderiza una tabla compacta de pares clave-valor. Si la propiedad lleva un
// comentario de gap (gap: string), muestra una indicación visual explícita.
import { Badge } from '@/components/ui/badge'

export interface KeyValueItem {
  key: string
  label: string
  value: string | number | boolean | null
  gap?: string
}

defineProps<{
  items: KeyValueItem[]
}>()
</script>

<template>
  <table class="w-full text-left text-xs">
    <tbody>
      <tr
        v-for="item in items"
        :key="item.key"
        class="border-b border-border/50 last:border-0 hover:bg-muted/30"
      >
        <td class="w-1/3 py-1.5 pr-2 font-medium text-muted-foreground">
          {{ item.label }}
        </td>
        <td class="py-1.5 font-mono text-foreground">
          <template v-if="item.gap">
            <span class="text-muted-foreground italic mr-2">{{ item.value ?? 'N/A' }}</span>
            <Badge variant="outline" class="text-[10px] py-0 px-1 text-amber-500 border-amber-500/50">
              Gap: {{ item.gap }}
            </Badge>
          </template>
          <template v-else-if="typeof item.value === 'boolean'">
            <Badge :variant="item.value ? 'default' : 'secondary'">
              {{ item.value ? 'Sí / Real' : 'No / Simulado' }}
            </Badge>
          </template>
          <template v-else>
            {{ item.value ?? '—' }}
          </template>
        </td>
      </tr>
    </tbody>
  </table>
</template>
