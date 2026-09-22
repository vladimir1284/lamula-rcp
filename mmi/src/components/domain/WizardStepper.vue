<script setup lang="ts">
export interface WizardStepItem {
  title: string
  description?: string
  status: 'pending' | 'active' | 'completed' | 'failed'
}

defineProps<{
  steps: WizardStepItem[]
}>()
</script>

<template>
  <div class="flex flex-col gap-4">
    <ol class="relative border-l border-border ml-3 flex flex-col gap-6">
      <li v-for="(step, idx) in steps" :key="idx" class="ml-6">
        <!-- Ícono del indicador del paso -->
        <span
          class="absolute -left-3.5 flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold transition-colors"
          :class="{
            'bg-primary text-primary-foreground ring-4 ring-primary/20': step.status === 'active',
            'bg-state-ok text-primary-foreground': step.status === 'completed',
            'bg-destructive text-destructive-foreground': step.status === 'failed',
            'bg-muted text-muted-foreground border border-border': step.status === 'pending',
          }"
        >
          <template v-if="step.status === 'completed'">✓</template>
          <template v-else-if="step.status === 'failed'">✗</template>
          <template v-else>{{ idx + 1 }}</template>
        </span>

        <!-- Contenido del paso -->
        <div class="flex flex-col gap-0.5">
          <h3
            class="text-sm font-semibold leading-none"
            :class="{
              'text-foreground font-bold': step.status === 'active',
              'text-state-ok': step.status === 'completed',
              'text-destructive': step.status === 'failed',
              'text-muted-foreground': step.status === 'pending',
            }"
          >
            Paso {{ idx + 1 }}: {{ step.title }}
          </h3>
          <p v-if="step.description" class="text-xs text-muted-foreground mt-1">
            {{ step.description }}
          </p>
        </div>
      </li>
    </ol>
  </div>
</template>
