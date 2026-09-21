<!--
  ConfigProfilesView.vue: Vista E11 — Config Profiles & ConfigDiffView.
  Origen legacy: RVP900 §4.1.1 (comandos F/S/R).
  Generaliza el patrón Set/Save/Restore/Factory sobre los campos bajo
  control directo del RCP (B7 límites, step config C2/E5, sectores C5, umbrales E3).
  Muestra la diferencia JSON entre el estado actual (current) y el guardado (saved).
-->
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import ConfigDiffView from '@/components/domain/ConfigDiffView.vue'
import { useGateway } from '@/composables/useGateway'
import type { RcpConfigProfile } from '@/types/mmi'

const {
  maintenance,
  fetchConfigProfileCurrent,
  fetchConfigProfileSaved,
  setConfigProfile,
  saveConfigProfile,
  restoreConfigProfile,
  factoryConfigProfile,
  fetchPowerMonitor,
} = useGateway()

const currentProfile = ref<RcpConfigProfile | null>(null)
const savedProfile = ref<RcpConfigProfile | null>(null)
const radiating = ref<boolean>(false)
const busy = ref<boolean>(false)
const error = ref<string | null>(null)
const successMsg = ref<string | null>(null)

async function loadData() {
  error.value = null
  try {
    const [cur, sav, pmon] = await Promise.all([
      fetchConfigProfileCurrent(),
      fetchConfigProfileSaved(),
      fetchPowerMonitor().catch(() => null),
    ])
    currentProfile.value = cur
    savedProfile.value = sav
    if (pmon) radiating.value = pmon.radiating
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

async function doSave() {
  busy.value = true
  error.value = null
  successMsg.value = null
  try {
    savedProfile.value = await saveConfigProfile()
    currentProfile.value = await fetchConfigProfileCurrent()
    successMsg.value = 'Configuración guardada persistentemente (Save OK).'
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    busy.value = false
  }
}

async function doRestore() {
  busy.value = true
  error.value = null
  successMsg.value = null
  try {
    currentProfile.value = await restoreConfigProfile()
    successMsg.value = 'Estado actual restaurado desde la configuración guardada (Restore OK).'
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    busy.value = false
  }
}

async function doFactory() {
  busy.value = true
  error.value = null
  successMsg.value = null
  try {
    currentProfile.value = await factoryConfigProfile()
    successMsg.value = 'Valores por defecto de fábrica cargados en el estado actual (Factory OK).'
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    busy.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 overflow-auto p-3">
    <div class="flex items-center justify-between border-b border-border pb-2">
      <div>
        <h2 class="text-lg font-semibold text-foreground">E11 Config Profiles</h2>
        <p class="text-xs text-muted-foreground">
          Gestión de perfiles locales de configuración RCP (límites B7, paso C2/E5, sectores C5, umbrales E3 y filtros E4).
        </p>
      </div>
      <div class="flex items-center gap-2">
        <span
          v-if="maintenance?.level === 'MANT'"
          class="rounded bg-emerald-950 px-2 py-1 font-mono text-[11px] font-medium text-emerald-400 border border-emerald-800"
        >
          Acceso MANT Desbloqueado
        </span>
        <span
          v-else
          class="rounded bg-amber-950 px-2 py-1 font-mono text-[11px] font-medium text-amber-400 border border-amber-800"
        >
          Solo Lectura (Modo OP)
        </span>
      </div>
    </div>

    <p v-if="error" class="text-xs font-medium text-destructive">{{ error }}</p>
    <p v-if="successMsg" class="text-xs font-medium text-emerald-400">{{ successMsg }}</p>

    <Card>
      <CardHeader class="flex flex-row items-center justify-between py-3">
        <CardTitle class="text-sm font-medium">Acciones de Perfil (Profile Actions)</CardTitle>

        <div class="flex flex-wrap items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            :disabled="busy || maintenance?.level !== 'MANT'"
            @click="doRestore"
          >
            Restore (R)
          </Button>

          <Button
            size="sm"
            variant="outline"
            :disabled="busy || maintenance?.level !== 'MANT'"
            @click="doFactory"
          >
            Factory (F)
          </Button>

          <Button
            size="sm"
            :disabled="busy || maintenance?.level !== 'MANT' || radiating"
            @click="doSave"
          >
            Save (S)
          </Button>
        </div>
      </CardHeader>
      <CardContent class="pt-0">
        <p v-if="radiating" class="text-xs text-amber-400/90 font-mono">
          ⚠ Radiación encendida: la acción "Save" (persistir en NVRAM/disco) está bloqueada hasta apagar la radiación.
        </p>
        <p v-else-if="maintenance?.level !== 'MANT'" class="text-xs text-muted-foreground">
          Modo MANT requerido para modificar, restaurar o guardar perfiles de configuración.
        </p>
      </CardContent>
    </Card>

    <Card class="flex-1 min-h-0 flex flex-col">
      <CardHeader class="py-3">
        <CardTitle class="text-sm font-medium">
          Diferencias entre Estado Actual (Current) y Guardado (Saved) — ConfigDiffView
        </CardTitle>
      </CardHeader>
      <CardContent class="flex-1 min-h-0 overflow-auto pt-0">
        <ConfigDiffView :current="currentProfile" :saved="savedProfile" />
      </CardContent>
    </Card>
  </div>
</template>
