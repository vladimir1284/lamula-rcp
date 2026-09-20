<script setup lang="ts">
// Vista A7 System Information (docs/diseno/inventario-ui.md):
// Muestra la información del sistema organizada en un árbol de dos niveles:
// RCP, Contrato DSP, MMI, Radar, ACU y LCU.
// Documenta explícitamente los gaps conocidos para ramas sin backend aún.
import { computed, onMounted, ref } from 'vue'
import { Button } from '@/components/ui/button'
import InfoTree, { type TreeNode } from '@/components/domain/InfoTree.vue'
import { useGateway } from '@/composables/useGateway'

const props = withDefaults(
  defineProps<{
    simulated?: boolean
  }>(),
  { simulated: false },
)

const { control, sessionInfo, systemInfo, fetchStatus, fetchSystemInfo } = useGateway()

const copied = ref(false)

const mmiVersion = typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : '0.0.0'
const userAgent = typeof navigator !== 'undefined' ? navigator.userAgent : 'Mantenimiento MMI / Browser Environment'

onMounted(() => {
  fetchStatus().catch(() => {})
  fetchSystemInfo().catch(() => {})
})

const treeData = computed<TreeNode[]>(() => [
  {
    id: 'rcp',
    label: 'RCP (Radar Control Processor)',
    children: [
      {
        id: 'rcp-config',
        label: 'Configuración & Estado',
        items: [
          { key: 'version', label: 'Versión del RCP', value: systemInfo.value?.rcp_version ?? sessionInfo.value?.rcp_version ?? '0.0.0' },
          { key: 'started', label: 'Arrancado', value: sessionInfo.value?.started_at_wall ? new Date(sessionInfo.value.started_at_wall).toLocaleString() : 'esperando...' },
          { key: 'authority_mode', label: 'Modo de Control', value: control.value?.mode ?? 'desconocido' },
          { key: 'authority_actor', label: 'Actor de Control', value: control.value?.actor ?? 'ninguno' },
        ],
      },
    ],
  },
  {
    id: 'dsp',
    label: 'Contrato DSP (LAMULA DSP)',
    children: [
      {
        id: 'dsp-contract',
        label: 'Ancla y Procedencia de Contrato',
        items: [
          { key: 'dsp_ver', label: 'Versión del Contrato', value: systemInfo.value?.dsp_contract_version ?? 'v1.3' },
          { key: 'dsp_commit', label: 'Commit del Contrato', value: systemInfo.value?.dsp_contract_commit ?? '6a09656' },
          { key: 'dsp_date', label: 'Fecha del Commit', value: systemInfo.value?.dsp_contract_commit_date ?? '2026-09-16' },
        ],
      },
    ],
  },
  {
    id: 'mmi',
    label: 'MMI (Interface Operador)',
    children: [
      {
        id: 'mmi-env',
        label: 'Entorno de Ejecución',
        items: [
          { key: 'mmi_version', label: 'Versión MMI', value: mmiVersion },
          { key: 'user_agent', label: 'User Agent (Navegador)', value: userAgent },
        ],
      },
    ],
  },
  {
    id: 'radar',
    label: 'Radar & Clientes',
    children: [
      {
        id: 'radar-clients',
        label: 'Clientes de Estado',
        items: [
          { key: 'clients', label: 'Clientes Conectados (WS)', value: systemInfo.value?.connected_clients ?? 0 },
        ],
      },
      {
        id: 'radar-hal',
        label: 'HAL (Hardware Abstraction Layer)',
        items: [
          { key: 'simulated', label: 'HAL Simulado (radar_emulator)', value: props.simulated },
        ],
      },
      {
        id: 'radar-components',
        label: 'Componentes & Subsistemas',
        gap: 'sin backend de estado por componente',
        items: [
          { key: 'comp_status', label: 'Estado Subsistemas', value: 'Pendiente de telemetría detallada', gap: 'sin backend' },
        ],
      },
      {
        id: 'radar-location',
        label: 'Ubicación Geográfica',
        gap: 'sin backend de coordenadas GPS/geográficas',
        items: [
          { key: 'location', label: 'Coordenadas Radar', value: 'No configurado', gap: 'sin backend' },
        ],
      },
    ],
  },
  {
    id: 'acu',
    label: 'ACU (Antenna Control Unit)',
    gap: 'módulos de ACU sin backend',
    children: [
      {
        id: 'acu-modules',
        label: 'Module Info',
        gap: 'sin backend ACU',
        items: [
          { key: 'acu_info', label: 'Módulos ACU', value: 'No disponible', gap: 'sin backend' },
        ],
      },
    ],
  },
  {
    id: 'lcu',
    label: 'LCU (Local Control Unit)',
    gap: 'módulos de LCU sin backend',
    children: [
      {
        id: 'lcu-modules',
        label: 'Module Info',
        gap: 'sin backend LCU',
        items: [
          { key: 'lcu_info', label: 'Módulos LCU', value: 'No disponible', gap: 'sin backend' },
        ],
      },
    ],
  },
])

function copyAsJson() {
  const jsonStr = JSON.stringify(treeData.value, null, 2)
  if (navigator.clipboard) {
    navigator.clipboard.writeText(jsonStr).then(() => {
      copied.value = true
      setTimeout(() => {
        copied.value = false
      }, 2000)
    })
  }
}
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-3 overflow-auto p-3 text-sm">
    <div class="flex items-center justify-between border-b border-border/60 pb-2">
      <div class="flex items-center gap-2">
        <h2 class="font-semibold text-base">Información del Sistema (A7)</h2>
        <span class="text-xs text-muted-foreground">Estructura de dos niveles (RAVIS §13)</span>
      </div>
      <Button size="sm" variant="outline" @click="copyAsJson">
        {{ copied ? '¡Copiado!' : 'Copiar JSON' }}
      </Button>
    </div>

    <InfoTree :nodes="treeData" />
  </div>
</template>
