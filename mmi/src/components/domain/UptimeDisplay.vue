<script setup lang="ts">
// Uptime en vivo desde started_at_wall -- antes calculado inline en
// SystemInformationView.vue con un ref `now` propio. El timer sigue viviendo
// acá (no es llamada de red ni de store, así que sigue siendo válido como
// presentacional: una story le pasa un `startedAtWall` fijo y se ve tickear
// solo, sin mocks).
import { onMounted, onUnmounted, ref } from 'vue'

const props = defineProps<{
  startedAtWall: string
}>()

const now = ref(Date.now())
let timer: ReturnType<typeof setInterval> | undefined

onMounted(() => {
  timer = setInterval(() => {
    now.value = Date.now()
  }, 1000)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})

function formatUptime(startedAtWall: string, nowMs: number): string {
  const totalS = Math.max(0, Math.floor((nowMs - new Date(startedAtWall).getTime()) / 1000))
  const h = Math.floor(totalS / 3600)
  const m = Math.floor((totalS % 3600) / 60)
  const s = totalS % 60
  return `${h}h ${m}m ${s}s`
}
</script>

<template>
  <span>{{ formatUptime(props.startedAtWall, now) }}</span>
</template>
