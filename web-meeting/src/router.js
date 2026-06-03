import { createRouter, createWebHashHistory } from 'vue-router'
import { getToken, getUser, getGuestCtx, useAuth } from './composables/useAuth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('./views/Login.vue'),
    meta: { title: '登录', public: true },
  },
  {
    path: '/invite/:token',
    name: 'invite',
    component: () => import('./views/Invite.vue'),
    meta: { title: '受邀加入会议', public: true },
    props: true,
  },
  {
    path: '/',
    name: 'workbench',
    component: () => import('./views/Workbench.vue'),
    meta: { title: '工作台', owner: true },
  },
  {
    path: '/mini',
    name: 'mini',
    component: () => import('./views/MiniProgram.vue'),
    meta: { title: '小程序演示', immersive: true },
  },
  {
    path: '/voice',
    name: 'voice',
    component: () => import('./views/VoiceHome.vue'),
    meta: { title: '会议秘书', hideFooter: true },
  },
  {
    path: '/douyin',
    name: 'douyin',
    component: () => import('./views/DouyinFeed.vue'),
    meta: { title: '移动秘书', immersive: true },
  },
  {
    path: '/meetings',
    name: 'meetings',
    component: () => import('./views/Meetings.vue'),
    meta: { title: '会议管理', owner: true },
  },
  {
    path: '/meetings/:id',
    name: 'meeting-detail',
    component: () => import('./views/MeetingDetail.vue'),
    meta: { title: '会议详情' },
    props: true,
  },
  {
    path: '/history',
    name: 'history',
    component: () => import('./views/History.vue'),
    meta: { title: '历史查询' },
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
  // 公开路径直接放行
  if (to.meta.public) return true

  // 首次进入时尝试用 localStorage 的 token 拉一次 /me 校验
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

  if (to.meta.owner && user.role !== 'owner') {
    // 嘉宾访问 owner-only (工作台 / 会议管理): 跳回自己被邀请的会议
    const gc = getGuestCtx()
    if (gc && gc.meeting_id) {
      return {
        name: 'meeting-detail',
        params: { id: String(gc.meeting_id) },
        replace: true,
      }
    }
    if (gc && gc.share_token) {
      return {
        name: 'invite',
        params: { token: gc.share_token },
        replace: true,
      }
    }
    // 没有 guest 上下文 (脏数据), 回登录页
    return { name: 'login', replace: true }
  }

  return true
})

router.afterEach((to) => {
  document.title = `${to.meta.title || ''} · 会议秘书`
})

export default router
