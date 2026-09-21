<script setup lang="ts">
import { ref, watch } from 'vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

const props = withDefaults(
  defineProps<{
    open: boolean
    title: string
    description: string
    actionLabel?: string
    consequences?: string[]
    loading?: boolean
    requireTyping?: string
  }>(),
  {
    actionLabel: 'Confirmar',
    consequences: () => [],
    loading: false,
  },
)

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

const typedText = ref('')

watch(
  () => props.open,
  (newVal) => {
    if (newVal) {
      typedText.value = ''
    }
  },
)

function handleConfirm() {
  if (props.requireTyping && typedText.value !== props.requireTyping) {
    return
  }
  emit('confirm')
}

function handleCancel() {
  emit('update:open', false)
  emit('cancel')
}
</script>

<template>
  <div
    v-if="props.open"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
  >
    <Card class="w-full max-w-md shadow-lg border-destructive/50 bg-background">
      <CardHeader>
        <CardTitle class="text-base font-semibold text-destructive">
          {{ props.title }}
        </CardTitle>
      </CardHeader>
      <CardContent class="space-y-3 text-xs">
        <p class="text-muted-foreground">{{ props.description }}</p>

        <div
          v-if="props.consequences && props.consequences.length > 0"
          class="rounded border border-destructive/20 bg-destructive/10 p-2.5 text-destructive"
        >
          <span class="font-semibold block mb-1">Consecuencias de esta acción:</span>
          <ul class="list-disc list-inside space-y-0.5">
            <li v-for="(item, idx) in props.consequences" :key="idx">
              {{ item }}
            </li>
          </ul>
        </div>

        <div v-if="props.requireTyping" class="space-y-1 pt-1">
          <label class="text-xs font-medium text-muted-foreground">
            Escriba <span class="font-mono font-bold text-foreground">{{ props.requireTyping }}</span> para confirmar:
          </label>
          <Input
            v-model="typedText"
            type="text"
            class="h-8 text-xs font-mono"
            :placeholder="props.requireTyping"
          />
        </div>
      </CardContent>
      <CardFooter class="flex justify-end gap-2 pt-2">
        <Button variant="outline" size="sm" :disabled="props.loading" @click="handleCancel">
          Cancelar
        </Button>
        <Button
          variant="destructive"
          size="sm"
          :disabled="
            props.loading ||
            (!!props.requireTyping && typedText !== props.requireTyping)
          "
          @click="handleConfirm"
        >
          <span v-if="props.loading">Procesando...</span>
          <span v-else>{{ props.actionLabel }}</span>
        </Button>
      </CardFooter>
    </Card>
  </div>
</template>
