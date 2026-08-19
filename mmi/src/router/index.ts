import { createRouter, createWebHistory } from 'vue-router'
import ControlCenterView from '@/views/ControlCenterView.vue'
import SystemStatusView from '@/views/SystemStatusView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'control-center', component: ControlCenterView },
    { path: '/system-status', name: 'system-status', component: SystemStatusView },
  ],
})

export default router
