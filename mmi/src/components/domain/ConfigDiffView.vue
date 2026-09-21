<script setup lang="ts">
import { computed, ref } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import type { RcpConfigProfile } from '@/types/mmi'

export interface DiffItem {
  path: string
  keyLabel: string
  currentValue: string
  savedValue: string
  status: 'modified' | 'added' | 'deleted' | 'unchanged'
}

const props = defineProps<{
  current: RcpConfigProfile | null
  saved: RcpConfigProfile | null
}>()

const searchFilter = ref('')
const onlyDiffs = ref(false)

function flattenObj(obj: Record<string, unknown> | null, prefix = ''): Record<string, unknown> {
  if (!obj || typeof obj !== 'object') return {}
  const res: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(obj)) {
    const path = prefix ? `${prefix}.${key}` : key
    if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
      Object.assign(res, flattenObj(value as Record<string, unknown>, path))
    } else if (Array.isArray(value)) {
      res[path] = JSON.stringify(value)
    } else {
      res[path] = value
    }
  }
  return res
}

const diffItems = computed<DiffItem[]>(() => {
  const currentFlat = flattenObj(props.current as unknown as Record<string, unknown>)
  const savedFlat = flattenObj(props.saved as unknown as Record<string, unknown>)

  const allKeys = Array.from(new Set([...Object.keys(currentFlat), ...Object.keys(savedFlat)])).sort()

  return allKeys.map((key) => {
    const hasCurrent = key in currentFlat
    const hasSaved = key in savedFlat
    const curVal = currentFlat[key]
    const savVal = savedFlat[key]

    let status: DiffItem['status'] = 'unchanged'
    if (hasCurrent && !hasSaved) {
      status = 'added'
    } else if (!hasCurrent && hasSaved) {
      status = 'deleted'
    } else if (JSON.stringify(curVal) !== JSON.stringify(savVal)) {
      status = 'modified'
    }

    const curStr = hasCurrent ? (curVal === null ? 'null' : String(curVal)) : '—'
    const savStr = hasSaved ? (savVal === null ? 'null' : String(savVal)) : '—'

    return {
      path: key,
      keyLabel: key.replace(/\./g, ' → '),
      currentValue: curStr,
      savedValue: savStr,
      status,
    }
  })
})

const filteredDiffs = computed(() => {
  return diffItems.value.filter((item) => {
    if (onlyDiffs.value && item.status === 'unchanged') return false
    if (!searchFilter.value) return true
    const q = searchFilter.value.toLowerCase()
    return (
      item.path.toLowerCase().includes(q) ||
      item.currentValue.toLowerCase().includes(q) ||
      item.savedValue.toLowerCase().includes(q)
    )
  })
})

const modifiedCount = computed(() => diffItems.value.filter((i) => i.status !== 'unchanged').length)
</script>

<template>
  <div class="space-y-3 font-mono text-xs">
    <div class="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-2">
      <div class="flex items-center gap-2">
        <Input
          v-model="searchFilter"
          placeholder="Filtrar parámetros..."
          class="h-8 w-56 text-xs font-mono"
        />
        <label class="flex items-center gap-1.5 text-xs text-muted-foreground font-sans cursor-pointer">
          <input
            v-model="onlyDiffs"
            type="checkbox"
            class="rounded border-border bg-background"
          />
          Sólo diferencias
        </label>
      </div>

      <div class="flex items-center gap-2">
        <Badge v-if="modifiedCount > 0" variant="secondary" class="bg-amber-950 text-amber-300 border-amber-800">
          {{ modifiedCount }} cambio{{ modifiedCount === 1 ? '' : 's' }} sin guardar
        </Badge>
        <Badge v-else variant="outline" class="text-emerald-400 border-emerald-800">
          Sincronizado con guardado
        </Badge>
      </div>
    </div>

    <div class="rounded-md border border-border bg-card/50 overflow-hidden">
      <table class="w-full text-left border-collapse text-xs">
        <thead>
          <tr class="border-b border-border bg-muted/50 text-muted-foreground uppercase text-[10px]">
            <th class="py-2 px-3">Parámetro (Clave)</th>
            <th class="py-2 px-3">Estado Actual (Current)</th>
            <th class="py-2 px-3">Guardado (Saved)</th>
            <th class="py-2 px-3 text-right">Diferencia</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-border/50">
          <tr
            v-for="item in filteredDiffs"
            :key="item.path"
            :class="[
              item.status === 'modified' ? 'bg-amber-950/20' : '',
              item.status === 'added' ? 'bg-emerald-950/20' : '',
              item.status === 'deleted' ? 'bg-red-950/20' : '',
              item.status === 'unchanged' ? 'opacity-70' : ''
            ]"
          >
            <td class="py-1.5 px-3 font-semibold text-foreground/90">
              {{ item.keyLabel }}
            </td>
            <td
              class="py-1.5 px-3"
              :class="item.status === 'modified' || item.status === 'added' ? 'text-amber-300 font-bold' : ''"
            >
              {{ item.currentValue }}
            </td>
            <td class="py-1.5 px-3 text-muted-foreground">
              {{ item.savedValue }}
            </td>
            <td class="py-1.5 px-3 text-right">
              <Badge
                v-if="item.status === 'modified'"
                variant="outline"
                class="border-amber-700 bg-amber-950/60 text-amber-300 text-[10px]"
              >
                MODIFICADO
              </Badge>
              <Badge
                v-else-if="item.status === 'added'"
                variant="outline"
                class="border-emerald-700 bg-emerald-950/60 text-emerald-300 text-[10px]"
              >
                AÑADIDO
              </Badge>
              <Badge
                v-else-if="item.status === 'deleted'"
                variant="outline"
                class="border-red-700 bg-red-950/60 text-red-300 text-[10px]"
              >
                ELIMINADO
              </Badge>
              <span v-else class="text-muted-foreground/50 text-[10px]">—</span>
            </td>
          </tr>
          <tr v-if="filteredDiffs.length === 0">
            <td colspan="4" class="py-6 text-center text-muted-foreground italic">
              No hay parámetros que coincidan con los filtros.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
