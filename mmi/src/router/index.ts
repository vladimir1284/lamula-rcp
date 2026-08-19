import { createRouter, createWebHistory } from 'vue-router'
import ControlCenterView from '@/views/ControlCenterView.vue'
import SystemStatusView from '@/views/SystemStatusView.vue'
import SystemVisualizationView from '@/views/SystemVisualizationView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'control-center', component: ControlCenterView },
    { path: '/system-status', name: 'system-status', component: SystemStatusView },
    { path: '/system-visualization', name: 'system-visualization', component: SystemVisualizationView },
  ],
})

export default router
