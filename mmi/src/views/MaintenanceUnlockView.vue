<script setup lang="ts">
// Vista A4 MaintenanceUnlockView (docs/diseno/inventario-ui.md):
// Conecta MaintenanceUnlockCard con useGateway() para gestionar el nivel
// de acceso MANT en vivo contra el backend del RCP.
import { ref } from 'vue'
import MaintenanceUnlockCard from '@/components/domain/MaintenanceUnlockCard.vue'
import { useGateway } from '@/composables/useGateway'

const { maintenance, unlockMaintenance, lockMaintenance } = useGateway()

const busy = ref(false)
const error = ref<string | null>(null)

async function handleUnlock(payload: { password: string; actor: string; duration_s: number }) {
  busy.value = true
  error.value = null
  try {
    await unlockMaintenance(payload)
  } catch (err: unknown) {
    if (err instanceof Error) {
      error.value = err.message
    } else {
      error.value = 'Error al desbloquear mantenimiento'
    }
  } finally {
    busy.value = false
  }
}

async function handleLock() {
  busy.value = true
  error.value = null
  try {
    await lockMaintenance()
  } catch (err: unknown) {
    if (err instanceof Error) {
      error.value = err.message
    } else {
      error.value = 'Error al bloquear mantenimiento'
    }
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="flex h-full min-h-0 flex-col items-center justify-center p-4">
    <MaintenanceUnlockCard
      :maintenance="maintenance"
      :busy="busy"
      :error="error"
      @unlock="handleUnlock"
      @lock="handleLock"
    />
  </div>
</template>
