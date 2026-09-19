<script setup lang="ts">
// A1: "reloj UTC + local". Dos relojes, no uno -- mismo principio que el
// contrato DSP (AGENTS.md, "Dos relojes, no uno"): la hora de pared UTC es
// la que importa para observación meteorológica, la local es para el
// operador. Timer local, igual que UptimeDisplay -- no es dato de red.
import { onMounted, onUnmounted, ref } from 'vue'

const now = ref(new Date())
let timer: ReturnType<typeof setInterval> | undefined

onMounted(() => {
  timer = setInterval(() => {
    now.value = new Date()
  }, 1000)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})

function hhmmss(d: Date, utc: boolean): string {
  const h = utc ? d.getUTCHours() : d.getHours()
  const m = utc ? d.getUTCMinutes() : d.getMinutes()
  const s = utc ? d.getUTCSeconds() : d.getSeconds()
  return [h, m, s].map((v) => String(v).padStart(2, '0')).join(':')
}
</script>

<template>
  <div class="flex items-center gap-3 text-xs tabular-nums text-muted-foreground">
    <span>{{ hhmmss(now, true) }} UTC</span>
    <span>{{ hhmmss(now, false) }} local</span>
  </div>
</template>
