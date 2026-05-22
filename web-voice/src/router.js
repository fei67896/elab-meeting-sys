import { createRouter, createWebHashHistory } from 'vue-router'
import { getToken, getUser, useAuth } from '@shared/composables/useAuth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('./views/Login.vue'),
    meta: { title: '登录', public: true },
  },
  {
    path: '/',
    name: 'home',
    component: () => import('./views/VoiceHome.vue'),
    meta: { title: '会议秘书', immersive: true },
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('./views/Settings.vue'),
    meta: { title: '设置' },
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

let _meChecked = false

router.beforeEach(async (to) => {
  if (to.meta.public) return true

  const { fetchMe } = useAuth()
  if (!_meChecked && getToken()) {
    _meChecked = true
    await fetchMe()
  }

  const token = getToken()
  const user = getUser()
  if (!token || !user) {
    return { name: 'login', query: { next: to.fullPath } }
  }
  return true
})

router.afterEach((to) => {
  document.title = `${to.meta.title || ''} · 会议秘书`
})

export default router
