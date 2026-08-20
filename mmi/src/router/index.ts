import { createRouter, createWebHistory } from 'vue-router'
import AntennaControlView from '@/views/AntennaControlView.vue'
import ControlCenterView from '@/views/ControlCenterView.vue'
import ScanWorksheetView from '@/views/ScanWorksheetView.vue'
import SystemInformationView from '@/views/SystemInformationView.vue'
import SystemStatusView from '@/views/SystemStatusView.vue'
import SystemVisualizationView from '@/views/SystemVisualizationView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'control-center', component: ControlCenterView },
    { path: '/system-status', name: 'system-status', component: SystemStatusView },
    { path: '/system-visualization', name: 'system-visualization', component: SystemVisualizationView },
    { path: '/scan-worksheet', name: 'scan-worksheet', component: ScanWorksheetView },
    { path: '/antenna-control', name: 'antenna-control', component: AntennaControlView },
    { path: '/system-information', name: 'system-information', component: SystemInformationView },
  ],
})

export default router
