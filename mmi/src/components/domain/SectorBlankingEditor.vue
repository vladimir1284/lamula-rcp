<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import type { SectorBlankingProfile } from '@/types/mmi'

const props = defineProps<{
  profile: SectorBlankingProfile
  busy?: boolean
  selectedIndex?: number | null
}>()

const emit = defineEmits<{
  (e: 'update:profile', profile: SectorBlankingProfile): void
  (e: 'set', profile: SectorBlankingProfile): void
  (e: 'save', profile: SectorBlankingProfile): void
  (e: 'select-sector', index: number): void
}>()

const draft = ref<SectorBlankingProfile>(JSON.parse(JSON.stringify(props.profile)))
const draftTouched = ref(false)

function ensureEightSectors() {
  if (!draft.value.sectors) draft.value.sectors = []
  while (draft.value.sectors.length < 8) {
    draft.value.sectors.push({
      in_use: false,
      az_start_deg: 0,
      az_end_deg: 45,
      el_start_deg: -90,
      el_end_deg: 90,
    })
  }
}

watch(
  () => props.profile,
  (newProf) => {
    if (!draftTouched.value && newProf) {
      draft.value = JSON.parse(JSON.stringify(newProf))
      ensureEightSectors()
    }
  },
  { deep: true, immediate: true },
)

function handleInput() {
  draftTouched.value = true
  emit('update:profile', draft.value)
}

function toggleEnabled() {
  draft.value.enabled = !draft.value.enabled
  handleInput()
}

function toggleInUse(index: number) {
  if (draft.value.sectors[index]) {
    draft.value.sectors[index].in_use = !draft.value.sectors[index].in_use
    handleInput()
  }
}

const validationIssues = computed(() => {
  const issues: string[] = []
  if (!draft.value?.sectors) return issues
  draft.value.sectors.forEach((sec, idx) => {
    if (!sec.in_use) return
    if (sec.az_start_deg < 0 || sec.az_start_deg > 360) {
      issues.push(`Sector ${idx + 1}: AZ Start fuera de rango (0° a 360°).`)
    }
    if (sec.az_end_deg < 0 || sec.az_end_deg > 360) {
      issues.push(`Sector ${idx + 1}: AZ End fuera de rango (0° a 360°).`)
    }
    if (sec.el_start_deg < -90 || sec.el_start_deg > 90) {
      issues.push(`Sector ${idx + 1}: EL Start fuera de rango (-90° a 90°).`)
    }
    if (sec.el_end_deg < -90 || sec.el_end_deg > 90) {
      issues.push(`Sector ${idx + 1}: EL End fuera de rango (-90° a 90°).`)
    }
    if (sec.el_start_deg > sec.el_end_deg) {
      issues.push(`Sector ${idx + 1}: EL Start no puede ser mayor que EL End.`)
    }
  })
  return issues
})

const isValid = computed(() => validationIssues.value.length === 0)

function doSet() {
  if (!isValid.value) return
  draftTouched.value = false
  emit('set', JSON.parse(JSON.stringify(draft.value)))
}

function doSave() {
  if (!isValid.value) return
  draftTouched.value = false
  emit('save', JSON.parse(JSON.stringify(draft.value)))
}
</script>

<template>
  <Card class="w-full">
    <CardHeader class="pb-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <CardTitle class="text-base font-semibold">Configuración de Sectores (8 Sectores)</CardTitle>
        <div class="flex items-center gap-2">
          <span class="text-xs font-medium text-muted-foreground">Blanking Global:</span>
          <Button
            size="sm"
            :variant="draft.enabled ? 'default' : 'outline'"
            class="h-7 text-xs"
            @click="toggleEnabled"
          >
            {{ draft.enabled ? 'Habilitado' : 'Deshabilitado' }}
          </Button>
        </div>
      </div>
    </CardHeader>

    <CardContent>
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="border-b bg-muted/50 text-muted-foreground">
            <tr>
              <th class="p-2 font-medium">Sector</th>
              <th class="p-2 font-medium">InUse</th>
              <th class="p-2 font-medium">AZ Start (°)</th>
              <th class="p-2 font-medium">AZ End (°)</th>
              <th class="p-2 font-medium">EL Start (°)</th>
              <th class="p-2 font-medium">EL End (°)</th>
            </tr>
          </thead>
          <tbody class="divide-y">
            <tr
              v-for="(sec, i) in draft.sectors"
              :key="i"
              class="transition-colors hover:bg-muted/30"
              :class="{
                'bg-muted/40 font-medium': selectedIndex === i,
                'opacity-60': !sec.in_use
              }"
              @click="emit('select-sector', i)"
            >
              <td class="p-2 font-mono text-muted-foreground">Sector {{ i + 1 }}</td>
              <td class="p-2">
                <input
                  type="checkbox"
                  :checked="sec.in_use"
                  class="h-4 w-4 rounded border-border accent-primary cursor-pointer"
                  @change="toggleInUse(i)"
                />
              </td>
              <td class="p-2">
                <Input
                  v-model.number="sec.az_start_deg"
                  type="number"
                  min="0"
                  max="360"
                  step="0.1"
                  class="h-7 w-20 text-xs font-mono"
                  :disabled="!sec.in_use"
                  @input="handleInput"
                />
              </td>
              <td class="p-2">
                <Input
                  v-model.number="sec.az_end_deg"
                  type="number"
                  min="0"
                  max="360"
                  step="0.1"
                  class="h-7 w-20 text-xs font-mono"
                  :disabled="!sec.in_use"
                  @input="handleInput"
                />
              </td>
              <td class="p-2">
                <Input
                  v-model.number="sec.el_start_deg"
                  type="number"
                  min="-90"
                  max="90"
                  step="0.1"
                  class="h-7 w-20 text-xs font-mono"
                  :disabled="!sec.in_use"
                  @input="handleInput"
                />
              </td>
              <td class="p-2">
                <Input
                  v-model.number="sec.el_end_deg"
                  type="number"
                  min="-90"
                  max="90"
                  step="0.1"
                  class="h-7 w-20 text-xs font-mono"
                  :disabled="!sec.in_use"
                  @input="handleInput"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="validationIssues.length > 0" class="mt-3 rounded border border-destructive/40 bg-destructive/10 p-2 text-xs text-destructive">
        <ul class="list-disc pl-4 space-y-0.5">
          <li v-for="(issue, idx) in validationIssues" :key="idx">{{ issue }}</li>
        </ul>
      </div>

      <div class="mt-4 flex items-center gap-2">
        <Button size="sm" :disabled="busy || !isValid" @click="doSet">
          Set (Aplicar Local)
        </Button>
        <Button size="sm" variant="outline" :disabled="busy || !isValid" @click="doSave">
          Save (Persistir RCP)
        </Button>
      </div>
    </CardContent>
  </Card>
</template>
