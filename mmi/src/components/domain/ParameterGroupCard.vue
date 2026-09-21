<script setup lang="ts">
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

defineProps<{
  title: string
  description?: string
}>()
</script>

<template>
  <Card class="border-border/80 bg-card/80 shadow-xs">
    <CardHeader class="border-b border-border/50 pb-2.5 pt-3.5">
      <CardTitle class="text-sm font-semibold tracking-wide text-foreground">
        {{ title }}
      </CardTitle>
      <p v-if="description" class="text-xs text-muted-foreground">
        {{ description }}
      </p>
    </CardHeader>
    <CardContent class="p-4">
      <slot />
    </CardContent>
  </Card>
</template>
