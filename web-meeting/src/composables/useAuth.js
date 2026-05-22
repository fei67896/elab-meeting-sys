// 全局认证状态 (单例)。
// - token / user 持久化到 localStorage, 启动时自动恢复
// - axios 拦截器在 client.js 里读取 token
// - 路由守卫调用 fetchMe 校验 token 时效

import { ref, computed, readonly } from 'vue'
import client from '../api/client'

const TOKEN_KEY = 'mtsec_token'
const USER_KEY = 'mtsec_user'
const GUEST_CTX_KEY = 'mtsec_guest_ctx'  // {meeting_id, share_token, display_name}

const _token = ref(localStorage.getItem(TOKEN_KEY) || '')
const _user = ref((() => {
  try { return JSON.parse(localStorage.getItem(USER_KEY)) || null }
  catch { return null }
})())
const _guestCtx = ref((() => {
  try { return JSON.parse(localStorage.getItem(GUEST_CTX_KEY)) || null }
  catch { return null }
})())

function setSession(token, user, guestCtx) {
  _token.value = token || ''
  _user.value = user || null
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user))
  else localStorage.removeItem(USER_KEY)
  // guestCtx === undefined: 不动; null: 清掉; object: 写入
  if (guestCtx === null) {
    _guestCtx.value = null
    localStorage.removeItem(GUEST_CTX_KEY)
  } else if (guestCtx) {
    _guestCtx.value = guestCtx
    localStorage.setItem(GUEST_CTX_KEY, JSON.stringify(guestCtx))
  }
}

async function login(username, password) {
  const data = await client.post('/api/auth/login', { username, password })
  // owner 登录会清掉之前残留的 guest 上下文
  setSession(data.token, data.user, null)
  return data.user
}

async function loginByShare(shareToken, displayName) {
  const data = await client.post('/api/auth/login-by-share', {
    share_token: shareToken,
    display_name: displayName || '',
  })
  setSession(data.token, data.user, {
    meeting_id: data.meeting_id,
    share_token: shareToken,
    display_name: displayName || '',
  })
  return data
}

async function fetchMe() {
  if (!_token.value) return null
  try {
    const data = await client.get('/api/auth/me')
    _user.value = data.user
    localStorage.setItem(USER_KEY, JSON.stringify(data.user))
    return data.user
  } catch (err) {
    // token 失效, 清掉
    setSession('', null)
    return null
  }
}

async function logout() {
  try { await client.post('/api/auth/logout') } catch (_) {}
  setSession('', null, null)
}

export function useAuth() {
  return {
    token: readonly(_token),
    user: readonly(_user),
    guestCtx: readonly(_guestCtx),
    isAuthed: computed(() => !!_token.value && !!_user.value),
    isOwner: computed(() => _user.value?.role === 'owner'),
    isGuest: computed(() => _user.value?.role === 'guest'),
    login,
    loginByShare,
    logout,
    fetchMe,
    setSession,
  }
}

// 给非组件代码 (router/axios 拦截器) 用的同步取值
export function getToken() {
  return _token.value
}
export function getUser() {
  return _user.value
}
export function getGuestCtx() {
  return _guestCtx.value
}
