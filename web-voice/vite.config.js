import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import fs from 'fs'
import path from 'path'

const PORT = Number(process.env.VOICE_PORT || 3001)
const BACKEND = process.env.VOICE_BACKEND || 'https://localhost:3080'
const sharedRoot = path.resolve(__dirname, '../web-meeting/src')

const sslDir = path.resolve(__dirname, '../ssl_certs')
const sslKey = path.join(sslDir, 'localhost.key')
const sslCrt = path.join(sslDir, 'localhost.crt')
const useHttps = fs.existsSync(sslKey) && fs.existsSync(sslCrt)

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
console.log('│  会议秘书前端 - web-voice [已停用]            │')
console.log('├─────────────────────────────────────────────┤')
console.log(`│  端口:   ${String(PORT).padEnd(34)} │`)
console.log(`│  HTTPS:  ${(useHttps ? '是 (自签名)' : '否').padEnd(34)} │`)
console.log(`│  后端:   ${BACKEND.padEnd(34)} │`)
console.log('└─────────────────────────────────────────────┘')

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@shared': sharedRoot,
    },
  },
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
