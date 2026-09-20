<script setup lang="ts">
// Componente InfoTree (docs/diseno/inventario-ui.md, A7):
// Estructura de árbol de dos niveles (Root Item -> Leaf Item -> KeyValueTable).
// Permite expandir/colapsar ramas y muestra etiquetas de gap explícitas.
import { ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import KeyValueTable, { type KeyValueItem } from './KeyValueTable.vue'

export interface TreeNode {
  id: string
  label: string
  items?: KeyValueItem[]
  gap?: string
  children?: TreeNode[]
}

defineProps<{
  nodes: TreeNode[]
}>()

const expanded = ref<Record<string, boolean>>({})

function toggleNode(id: string) {
  expanded.value[id] = !(expanded.value[id] ?? true)
}

function isExpanded(id: string): boolean {
  return expanded.value[id] ?? true
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <div
      v-for="root in nodes"
      :key="root.id"
      class="rounded-md border border-border bg-card p-3 shadow-xs"
    >
      <div
        class="flex cursor-pointer items-center justify-between font-semibold text-sm"
        @click="toggleNode(root.id)"
      >
        <div class="flex items-center gap-2">
          <span class="text-xs text-muted-foreground">{{ isExpanded(root.id) ? '▼' : '▶' }}</span>
          <span>{{ root.label }}</span>
          <Badge
            v-if="root.gap"
            variant="outline"
            class="text-[10px] py-0 px-1 text-amber-500 border-amber-500/50"
          >
            Gap: {{ root.gap }}
          </Badge>
        </div>
      </div>

      <div v-if="isExpanded(root.id)" class="mt-2 pl-3 border-l-2 border-border/40 flex flex-col gap-3">
        <!-- Direct items under root -->
        <KeyValueTable v-if="root.items && root.items.length > 0" :items="root.items" />

        <!-- Leaf children -->
        <div
          v-for="child in root.children"
          :key="child.id"
          class="flex flex-col gap-1 rounded bg-muted/20 p-2"
        >
          <div
            class="flex cursor-pointer items-center justify-between text-xs font-medium text-foreground/90"
            @click="toggleNode(child.id)"
          >
            <div class="flex items-center gap-2">
              <span class="text-[10px] text-muted-foreground">{{ isExpanded(child.id) ? '▼' : '▶' }}</span>
              <span>{{ child.label }}</span>
              <Badge
                v-if="child.gap"
                variant="outline"
                class="text-[10px] py-0 px-1 text-amber-500 border-amber-500/50"
              >
                Gap: {{ child.gap }}
              </Badge>
            </div>
          </div>

          <div v-if="isExpanded(child.id) && child.items" class="mt-1 pl-2">
            <KeyValueTable :items="child.items" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
