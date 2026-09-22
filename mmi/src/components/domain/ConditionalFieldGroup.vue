<script setup lang="ts">
import { Badge } from '@/components/ui/badge'

defineProps<{
  title?: string
  description?: string
  supported?: boolean
  badgeLabel?: string
}>()
</script>

<template>
  <div class="rounded-md border border-border/70 bg-card/50 p-3.5 space-y-2.5">
    <div v-if="title || supported === false" class="flex items-center justify-between gap-2 border-b border-border/40 pb-2">
      <div>
        <h4 v-if="title" class="text-xs font-semibold tracking-wide text-foreground uppercase">
          {{ title }}
        </h4>
        <p v-if="description" class="text-xs text-muted-foreground">
          {{ description }}
        </p>
      </div>
      <Badge
        v-if="supported === false"
        variant="outline"
        class="border-amber-500/50 bg-amber-500/10 text-amber-500 text-[10px] font-medium px-2 py-0.5"
      >
        {{ badgeLabel || 'Sin backend' }}
      </Badge>
    </div>
    <div :class="{ 'opacity-75': supported === false }">
      <slot />
    </div>
  </div>
</template>
