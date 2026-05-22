// 会议秘书 API 封装。所有接口走后端 /api/* (Vite 代理到 :3080)。
import client from './client'

export const meetingApi = {
  // ---- 会议 CRUD ----
  list(params = {}) {
    return client.get('/api/meetings', { params })
  },
  get(id) {
    return client.get(`/api/meetings/${id}`)
  },
  create(payload) {
    return client.post('/api/meetings', payload)
  },
  update(id, payload) {
    return client.patch(`/api/meetings/${id}`, payload)
  },
  remove(id) {
    return client.delete(`/api/meetings/${id}`)
  },
  addAgenda(id, payload) {
    return client.post(`/api/meetings/${id}/agendas`, payload)
  },
  addParticipant(id, payload) {
    return client.post(`/api/meetings/${id}/participants`, payload)
  },
  icsUrl(id) {
    return `/api/meetings/${id}/ics`
  },
  setAttendance(id, payload) {
    return client.post(`/api/meetings/${id}/attendance`, payload)
  },
  listAttendance(id) {
    return client.get(`/api/meetings/${id}/attendance`)
  },
  createShare(id) {
    return client.post(`/api/meetings/${id}/share`, {})
  },
  listShares(id) {
    return client.get(`/api/meetings/${id}/shares`)
  },
}

export const secretaryApi = {
  command(text, opts = {}) {
    return client.post('/api/secretary/command', {
      text,
      sessionid: opts.sessionid ?? 0,
      speak: opts.speak ?? true,
      meeting_id: opts.meetingId ?? undefined,
    })
  },
  history(limit = 50) {
    return client.get('/api/secretary/history', { params: { limit } })
  },
  mcpCards() {
    return client.get('/api/secretary/mcp-cards')
  },
}

export const authApi = {
  login(username, password) {
    return client.post('/api/auth/login', { username, password })
  },
  loginByShare(shareToken, displayName) {
    return client.post('/api/auth/login-by-share', {
      share_token: shareToken,
      display_name: displayName || '',
    })
  },
  logout() {
    return client.post('/api/auth/logout')
  },
  me() {
    return client.get('/api/auth/me')
  },
}

// ---- 数字人对话播报 (复用原有 /human echo 链路, 可选) ----
export const avatarApi = {
  echo(text, sessionid = 0) {
    return client.post('/human', { text, type: 'echo', sessionid })
  },
  interrupt(sessionid = 0) {
    return client.post('/interrupt_talk', { sessionid })
  },
  isSpeaking(sessionid = 0) {
    return client.post('/is_speaking', { sessionid })
  },
}
