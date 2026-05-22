import { createRouter, createWebHistory } from 'vue-router'
import Meetings from '../views/Meetings.vue'

const routes = [
  { path: '/', redirect: '/meetings' },
  { path: '/meetings', name: 'Meetings', component: Meetings },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
