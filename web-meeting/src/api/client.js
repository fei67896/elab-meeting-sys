// 统一的 axios 实例。
// - 自动注入 Authorization: Bearer <token>
// - 后端返回 {code, msg, data}; code !== 0 抛出错误
// - 401 自动清 session 并跳转到登录页
import axios from 'axios'

const client = axios.create({
  baseURL: '/',
  timeout: 30000,
  withCredentials: false,
})

const TOKEN_KEY = 'mtsec_token'

client.interceptors.request.use((config) => {
  const t = localStorage.getItem(TOKEN_KEY)
  if (t) {
    config.headers = config.headers || {}
    config.headers['Authorization'] = `Bearer ${t}`
  }
  return config
})

client.interceptors.response.use(
  (resp) => {
    const data = resp.data
    if (data && typeof data === 'object' && 'code' in data) {
      if (data.code === 0) return data.data
      const err = new Error(data.msg || '请求失败')
      err.code = data.code
      err.payload = data
      throw err
    }
    return data
  },
  (err) => {
    const status = err.response?.status
    if (status === 401) {
      // token 失效或匿名访问受保护接口
      localStorage.removeItem('mtsec_token')
      localStorage.removeItem('mtsec_user')
      // 软跳转, 避免在登录页里再次跳
      if (!location.hash.startsWith('#/login') && !location.hash.startsWith('#/invite')) {
        const next = encodeURIComponent(location.hash.slice(1) || '/')
        location.hash = `#/login?next=${next}`
      }
    }
    const msg = err.response?.data?.msg || err.message || '网络错误'
    err.message = msg
    return Promise.reject(err)
  }
)

export default client
