<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export interface SetupHubItem {
  id: string
  code: string
  title: string
  family: 'Setup DSP' | 'Ajuste' | 'Perfil'
  description: string
  dirty: boolean
  access: 'OP' | 'MANT'
  available: boolean
}

const props = defineProps<{
  items: SetupHubItem[]
}>()

const emit = defineEmits<{
  (e: 'select', itemId: string): void
}>()
</script>

<template>
  <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
    <div
      v-for="item in props.items"
      :key="item.id"
      class="flex flex-col justify-between rounded-lg border bg-card p-3 shadow-sm transition-colors hover:border-primary/50"
      :class="{ 'opacity-60': !item.available }"
    >
      <div class="space-y-1.5">
        <div class="flex items-center justify-between gap-1.5">
          <div class="flex items-center gap-1.5">
            <span class="font-mono text-xs font-bold text-primary">{{ item.code }}</span>
            <Badge variant="outline" class="text-[10px] uppercase font-mono px-1 py-0">
              {{ item.access }}
            </Badge>
          </div>
          <div class="flex items-center gap-1">
            <Badge v-if="item.dirty" variant="destructive" class="text-[10px] px-1 py-0 font-medium">
              ● Modificado
            </Badge>

            <Badge v-if="!item.available" variant="secondary" class="text-[10px] px-1 py-0">
              No dispon.
            </Badge>
          </div>
        </div>

        <div>
          <h4 class="text-xs font-semibold leading-tight text-card-foreground">
            {{ item.title }}
          </h4>
          <p class="mt-1 text-[11px] text-muted-foreground line-clamp-2">
            {{ item.description }}
          </p>
        </div>
      </div>

      <div class="mt-3 flex items-center justify-between border-t pt-2">
        <span class="text-[10px] uppercase text-muted-foreground font-mono">
          {{ item.family }}
        </span>
        <Button
          size="sm"
          variant="secondary"
          class="h-7 text-xs px-2.5"
          :disabled="!item.available"
          @click="emit('select', item.id)"
        >
          Abrir &rarr;
        </Button>
      </div>
    </div>
  </div>
</template>
