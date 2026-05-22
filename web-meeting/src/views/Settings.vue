<template>
  <div class="settings">
    <div class="container">
      <header class="page-head">
        <div>
          <h1 class="page-title">设置</h1>
          <p class="page-sub">查看当前后端连接、数字人与语音识别能力。</p>
        </div>
      </header>

      <div class="grid">
        <section class="card">
          <h3 class="md__h3">后端连接</h3>
          <dl class="dl">
            <dt>API 健康检查</dt>
            <dd>
              <span class="tag" :class="health.code === 0 ? 'is-success' : 'is-danger'">
                {{ health.code === 0 ? '正常' : '异常' }}
              </span>
              <span class="text-tiny text-dim mono">{{ JSON.stringify(health.raw) }}</span>
            </dd>
            <dt>前端地址</dt>
            <dd class="mono text-small">{{ frontendUrl }}</dd>
            <dt>后端代理目标</dt>
            <dd class="mono text-small">由 Vite proxy 转发, /api → 后端 :3080</dd>
            <dt>当前用户</dt>
            <dd>
              <span v-if="user" class="tag" :class="user.role === 'owner' ? 'is-primary' : 'is-accent'">
                {{ user.role }}
              </span>
              <span class="text-small">{{ user?.display_name || user?.username || '匿名' }}</span>
            </dd>
          </dl>
          <button class="btn btn-sm" @click="checkHealth">重新检查</button>
        </section>

        <section class="card">
          <h3 class="md__h3">浏览器能力</h3>
          <dl class="dl">
            <dt>语音识别</dt>
            <dd>
              <span class="tag" :class="speechSupported ? 'is-success' : 'is-accent'">
                {{ speechModeLabel }}
              </span>
              <span v-if="speechApiPresent && !speechSupported" class="text-tiny text-dim">
                (检测到 API, Edge 已自动走服务端)
              </span>
            </dd>
            <dt>WebRTC</dt>
            <dd>
              <span class="tag" :class="webrtcSupported ? 'is-success' : 'is-danger'">
                {{ webrtcSupported ? '支持' : '不支持' }}
              </span>
            </dd>
            <dt>麦克风</dt>
            <dd>
              <span class="tag" :class="micSupported ? 'is-success' : 'is-danger'">
                {{ micSupported ? '可用' : '不可用' }}
              </span>
            </dd>
          </dl>
        </section>

        <section class="card">
          <h3 class="md__h3">使用提示</h3>
          <ul class="tips">
            <li>语音推荐 <strong>Chrome</strong>（浏览器本地识别）；<strong>Edge</strong> 请用服务端 Whisper（录音后识别），需允许麦克风。</li>
            <li>HTTPS 自签名证书首次访问需在浏览器手动信任。</li>
            <li>"预订会议"目前是本地登记，会议链接为占位符。</li>
            <li>数字人播报依赖后端 <code>state.avatar_streams[sessionid]</code>；如未连接 WebRTC，会自动跳过播报。</li>
          </ul>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import client from '../api/client'
import { useAuth } from '../composables/useAuth'
import { canUseBrowserSpeech, speechEngineLabel } from '../utils/speech'

const { user } = useAuth()
const health = ref({ code: -1, raw: null })

const checkHealth = async () => {
  try {
    const resp = await client.get('/health')
    // /health 不走 {code, msg, data} 包装, axios 拦截器把它当成 data 透传
    health.value = {
      code: resp?.code ?? 0,
      raw: resp,
    }
  } catch (err) {
    health.value = { code: -1, raw: { error: err.message } }
  }
}

const speechApiPresent = computed(() =>
  'SpeechRecognition' in window || 'webkitSpeechRecognition' in window
)
const speechSupported = computed(() => canUseBrowserSpeech())
const speechModeLabel = computed(() => speechEngineLabel())
const webrtcSupported = computed(() => typeof RTCPeerConnection !== 'undefined')
const micSupported = computed(() =>
  !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)
)

const frontendUrl = computed(() => window.location.origin)

onMounted(checkHealth)
</script>

<style scoped>
.settings { padding: var(--space-5) 0 var(--space-7); }
.page-head { margin-bottom: var(--space-5); }
.page-title { font-family: var(--font-serif); font-size: var(--fs-h1); margin: 0 0 4px; }
.page-sub { margin: 0; color: var(--color-text-2); font-size: var(--fs-small); }

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-4);
}
.md__h3 { font-family: var(--font-serif); font-size: var(--fs-h4); margin: 0 0 var(--space-3); }

.dl {
  margin: 0;
  display: grid;
  grid-template-columns: 130px 1fr;
  gap: 6px 14px;
  font-size: var(--fs-small);
}
.dl dt { color: var(--color-text-2); }
.dl dd {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.tips {
  margin: 0;
  padding-left: 18px;
  color: var(--color-text-2);
  font-size: var(--fs-small);
  line-height: var(--lh-loose);
}
.tips code {
  background: var(--color-surface-2);
  padding: 1px 4px;
  border-radius: 3px;
}
</style>
