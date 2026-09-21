<script setup lang="ts">
// ColorTableEditor.vue (mmi/src/components/domain/) -- D6
// Tabla editable de puntos de control (stops) para una paleta de datos.
// Permite modificar L, C y H de cada fila con preview instantáneo y botón de eliminación/adición.

import { computed } from 'vue'
import { Button } from '@/components/ui/button'
import { parseOklch, formatOklch, type OklchColor } from '@/lib/colorScales'

const props = defineProps<{
  stops: string[]
}>()

const emit = defineEmits<{
  'update:stops': [stops: string[]]
}>()

const parsedStops = computed<OklchColor[]>(() => {
  return props.stops.map((s, idx) => {
    const parsed = parseOklch(s)
    return parsed ?? { l: 0.5, c: 0.1, h: idx * 45 }
  })
})

function updateStop(index: number, key: keyof OklchColor, value: number) {
  const current = [...parsedStops.value]
  const target = current[index]
  if (!target) return

  let val = Number(value)
  if (isNaN(val)) val = 0

  if (key === 'l') val = Math.max(0, Math.min(1, val))
  if (key === 'c') val = Math.max(0, Math.min(0.4, val))
  if (key === 'h') val = ((val % 360) + 360) % 360

  const updated: OklchColor = { ...target, [key]: val }
  current[index] = updated

  const newStops = current.map((c) => formatOklch(c))
  emit('update:stops', newStops)
}

function addStop() {
  const current = [...parsedStops.value]
  const last = current[current.length - 1] ?? { l: 0.5, c: 0.15, h: 180 }
  const newColor: OklchColor = {
    l: Math.min(0.95, last.l + 0.05),
    c: last.c,
    h: (last.h + 30) % 360,
  }
  current.push(newColor)
  emit('update:stops', current.map((c) => formatOklch(c)))
}

function removeStop(index: number) {
  if (props.stops.length <= 2) return // Mantener al menos 2 stops para interpolación
  const current = [...parsedStops.value]
  current.splice(index, 1)
  emit('update:stops', current.map((c) => formatOklch(c)))
}
</script>

<template>
  <div class="space-y-2 text-xs">
    <div class="flex items-center justify-between border-b border-border pb-1">
      <span class="font-medium text-foreground">Control Points (Stops OKLCH)</span>
      <Button size="xs" variant="outline" @click="addStop">+ Agregar Stop</Button>
    </div>

    <div class="max-h-60 overflow-y-auto pr-1">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="text-[10px] text-muted-foreground border-b border-border/50">
            <th class="py-1 px-1">#</th>
            <th class="py-1 px-1">Swatch</th>
            <th class="py-1 px-1">Lightness (L)</th>
            <th class="py-1 px-1">Chroma (C)</th>
            <th class="py-1 px-1">Hue (H°)</th>
            <th class="py-1 px-1 text-right">Acción</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(stop, idx) in parsedStops"
            :key="idx"
            class="border-b border-border/30 hover:bg-muted/30"
          >
            <td class="py-1 px-1 text-[10px] text-muted-foreground font-mono">{{ idx + 1 }}</td>
            <td class="py-1 px-1">
              <div
                class="h-5 w-7 rounded-xs border border-border shadow-xs"
                :style="{ backgroundColor: formatOklch(stop) }"
                :title="formatOklch(stop)"
              />
            </td>
            <td class="py-1 px-1">
              <input
                type="number"
                min="0"
                max="1"
                step="0.02"
                class="w-16 rounded-xs border border-border bg-background px-1 py-0.5 font-mono text-[11px]"
                :value="stop.l"
                @input="updateStop(idx, 'l', Number(($event.target as HTMLInputElement).value))"
              />
            </td>
            <td class="py-1 px-1">
              <input
                type="number"
                min="0"
                max="0.4"
                step="0.01"
                class="w-16 rounded-xs border border-border bg-background px-1 py-0.5 font-mono text-[11px]"
                :value="stop.c"
                @input="updateStop(idx, 'c', Number(($event.target as HTMLInputElement).value))"
              />
            </td>
            <td class="py-1 px-1">
              <input
                type="number"
                min="0"
                max="360"
                step="5"
                class="w-16 rounded-xs border border-border bg-background px-1 py-0.5 font-mono text-[11px]"
                :value="stop.h"
                @input="updateStop(idx, 'h', Number(($event.target as HTMLInputElement).value))"
              />
            </td>
            <td class="py-1 px-1 text-right">
              <Button
                size="xs"
                variant="ghost"
                class="h-6 px-1.5 text-[10px] text-destructive hover:bg-destructive/10"
                :disabled="stops.length <= 2"
                title="Eliminar stop"
                @click="removeStop(idx)"
              >
                ✕
              </Button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
