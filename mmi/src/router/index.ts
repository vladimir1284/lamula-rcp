import { createRouter, createWebHistory } from 'vue-router'
import ControlCenterView from '@/views/ControlCenterView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [{ path: '/', name: 'control-center', component: ControlCenterView }],
})

export default router
