<template>
  <div class="settings">
    <header class="settings__head">
      <router-link to="/" class="btn btn-sm btn-ghost">← 返回对话</router-link>
      <h1 class="settings__h1">设置</h1>
    </header>

    <div class="settings__body card">
      <h2 class="settings__h2">语音输入</h2>
      <p class="text-small">{{ engineLabel }}</p>
      <p class="text-tiny text-muted">
        <template v-if="isEdge">
          Microsoft Edge 使用<strong>服务端 Whisper</strong>转写（录音结束后识别），不用浏览器内置语音。
          说完再松手，识别中按钮会稍等片刻。
        </template>
        <template v-else>
          Chrome 推荐使用浏览器语音识别；其它浏览器将走服务端 Whisper 转写。
        </template>
      </p>

      <h2 class="settings__h2">数字人连接</h2>
      <p class="text-small">
        状态：<strong>{{ connectionState }}</strong>
        <span v-if="sessionId" class="mono text-muted"> · session {{ sessionId }}</span>
      </p>

      <h2 class="settings__h2">后端</h2>
      <p class="text-small text-muted">
        开发时 Vite 代理到 <code>https://localhost:3080</code>，与会议秘书共用同一后端。
      </p>

      <h2 class="settings__h2">其它入口</h2>
      <p class="text-small">
        <a href="https://localhost:3000/" target="_blank" rel="noopener">会议秘书工作台</a>
        （端口 3000）
      </p>
    </div>
  </div>
</template>

<script setup>
import { useWebRTC } from '@shared/composables/useWebRTC'
import { speechEngineLabel } from '@shared/utils/speech'

const engineLabel = speechEngineLabel()
const isEdge = typeof navigator !== 'undefined' && /Edg\//i.test(navigator.userAgent || '')
const { connectionState, sessionId } = useWebRTC()
</script>

<style scoped>
.settings {
  max-width: 560px;
  margin: 0 auto;
  padding: var(--space-5);
}
.settings__head {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}
.settings__h1 {
  margin: 0;
  font-size: var(--fs-h2);
}
.settings__body {
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.settings__h2 {
  margin: var(--space-4) 0 0;
  font-size: var(--fs-h4);
}
.settings__h2:first-child { margin-top: 0; }
</style>
