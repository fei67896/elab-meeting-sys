import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import fs from 'fs'
import path from 'path'

// 会议秘书前端是主入口, 端口固定 3000。
// 后端默认 3080 (HTTPS), 与原 web/ (3100) 错开, 整体落在 3000-3100 区间。
// HTTPS 复用仓库根目录的 ssl_certs/（若存在）。
const PORT = Number(process.env.MEETING_PORT || 3000)
const BACKEND = process.env.MEETING_BACKEND || 'https://localhost:3080'

const sslDir = path.resolve(__dirname, '../ssl_certs')
const sslKey = path.join(sslDir, 'localhost.key')
const sslCrt = path.join(sslDir, 'localhost.crt')
const useHttps = fs.existsSync(sslKey) && fs.existsSync(sslCrt)

// 所有需要代理到后端的路径前缀
const proxyPaths = [
  '/api',
  '/health',
  '/offer',
  '/human',
  '/humanaudio',
  '/asr',
  '/record',
  '/interrupt_talk',
  '/is_speaking',
  '/set_audiotype',
  '/clear_history',
  '/download',
]

const proxy = Object.fromEntries(
  proxyPaths.map((p) => [p, { target: BACKEND, changeOrigin: true, secure: false }])
)

console.log('┌─────────────────────────────────────────────┐')
console.log('│  会议秘书前端 - web-meeting                 │')
console.log('├─────────────────────────────────────────────┤')
console.log(`│  端口:   ${String(PORT).padEnd(34)} │`)
console.log(`│  HTTPS:  ${(useHttps ? '是 (自签名)' : '否').padEnd(34)} │`)
console.log(`│  后端:   ${BACKEND.padEnd(34)} │`)
console.log('└─────────────────────────────────────────────┘')

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: PORT,
    strictPort: true,
    ...(useHttps && {
      https: {
        key: fs.readFileSync(sslKey),
        cert: fs.readFileSync(sslCrt),
      },
    }),
    proxy,
  },
  build: {
    outDir: 'dist',
  },
})
