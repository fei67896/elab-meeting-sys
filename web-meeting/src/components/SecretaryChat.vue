<template>
  <section class="chat card">
    <header class="chat__header">
      <div>
        <h3 class="chat__title">指令对话</h3>
        <p class="chat__hint text-tiny text-dim">
          文字或语音下达指令 · {{ asrModeHint }}
        </p>
      </div>
      <button class="btn btn-sm btn-ghost" @click="clearMessages">清空</button>
    </header>

    <ol class="chat__messages" ref="listEl">
      <li v-if="messages.length === 0" class="chat__empty">
        <p class="text-muted">
          试试这样说：<br />
          <span class="text-mono text-small">
            "明天下午 3 点开技术评审会，张三李四参加，议程是回顾上周进度。"
          </span>
        </p>
      </li>
      <li
        v-for="m in messages"
        :key="m.id"
        :class="['chat__msg', `chat__msg--${m.role}`, { 'is-error': m.isError }]"
      >
        <div class="chat__bubble">
          <span class="chat__role">{{ roleLabel(m.role) }}</span>
          <p class="chat__content">{{ m.content }}</p>
          <div v-if="m.intent" class="chat__meta text-tiny">
            <span class="tag is-primary">{{ m.intent }}</span>
            <span class="text-dim">{{ formatTime(m.ts) }}</span>
          </div>
        </div>
      </li>
    </ol>

    <div class="chat__input">
      <div v-if="isRecording" class="chat__listening">
        <div class="chat__listening-row">
          <span class="dot" aria-hidden="true"></span>
          <span v-if="browserAsr">正在听写… 说完点 <kbd>停止</kbd>，文字实时出现（浏览器识别）</span>
          <span v-else>正在录音… 说完点 <kbd>停止</kbd>，由服务端 Whisper 识别</span>
        </div>
        <div class="meter" :title="`音量 ${(level * 100).toFixed(0)}%`">
          <div
            v-for="i in 16"
            :key="i"
            class="meter__bar"
            :class="{ 'is-on': level * 16 >= i - 0.4 }"
          ></div>
        </div>
      </div>
      <div v-if="isUploading" class="chat__listening">
        <div class="chat__listening-row">
          <span class="dot" aria-hidden="true"></span>
          <span>识别中… 正在调用服务器 Whisper, 请稍候</span>
        </div>
      </div>
      <div v-if="speechError" class="chat__alert">
        {{ speechErrorLabel }}
      </div>

      <textarea
        v-model="draft"
        class="textarea"
        rows="2"
        :placeholder="placeholder"
        :disabled="status === 'thinking'"
        @keydown.enter.prevent.exact="submit"
      />
      <div class="chat__actions">
        <span class="chat__status text-tiny" :class="`is-${status}`">
          {{ statusLabel }}
        </span>
        <div class="flex gap-2">
          <button
            class="btn btn-sm"
            :class="{ 'is-active': isRecording }"
            :disabled="!speechSupported || isUploading"
            :title="speechSupported ? asrModeHint : '当前浏览器不支持录音'"
            @click="toggleRecord"
          >
            <span v-if="isRecording">
              <span class="rec-dot" aria-hidden="true"></span>
              停止录音
            </span>
            <span v-else-if="isUploading">识别中…</span>
            <span v-else>开始录音</span>
          </button>
          <button
            class="btn btn-sm btn-primary"
            :disabled="!draft.trim() || status === 'thinking'"
            @click="submit"
          >
            发送
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import { useSecretary } from '../composables/useSecretary'
import { useRecorder } from '../composables/useRecorder'
import { useSpeechRecognition } from '../composables/useSpeechRecognition'
import { useMicLevel } from '../composables/useMicLevel'
import { formatTime } from '../utils/format'
import { canUseBrowserSpeech, speechEngineLabel } from '../utils/speech'

const { messages, status, sendCommand, clearMessages } = useSecretary()

const draft = ref('')
const listEl = ref(null)
const speechError = ref('')

const statusLabel = computed(() => {
  switch (status.value) {
    case 'thinking': return '思考中…'
    case 'speaking': return '数字人播报中…'
    case 'error': return '出错了，请重试'
    default: return ''
  }
})

// Chrome 等: 浏览器 Web Speech API (低延迟, 边说边出字)
// Edge 等: MediaRecorder + 服务端 Whisper tiny
// 用户在本页手动切到服务端后, 本会话内不再尝试浏览器识别
const forceServerAsr = ref(false)

const speech = useSpeechRecognition({
  language: 'zh-CN',
  continuous: false,
  onChange: (text) => {
    if (speech.isRecording.value && text) liveDraft.value = text
  },
  onError: (err) => {
    const code = String(err || '')
    if (['network', 'service-not-allowed', 'aborted'].includes(code)) {
      forceServerAsr.value = true
      speechError.value =
        '浏览器语音不可用 (Edge 常见), 已切换为服务端识别, 请再点一次麦克风'
      return
    }
    speechError.value = `语音识别: ${code}`
  },
})
const recorder = useRecorder()
const mic = useMicLevel()
const liveDraft = ref('')

const browserAsr = computed(
  () => canUseBrowserSpeech() && !forceServerAsr.value
)
const asrModeHint = computed(() => speechEngineLabel())
const isRecording = computed(() =>
  browserAsr.value ? speech.isRecording.value : recorder.isRecording.value
)
const isUploading = computed(() => !browserAsr.value && recorder.isUploading.value)
const level = computed(() => mic.level.value)
const speechSupported = computed(() =>
  browserAsr.value
    || (typeof window !== 'undefined'
      && !!window.MediaRecorder
      && !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia))
)

const placeholder = computed(() => {
  if (isUploading.value) return '服务端识别中…'
  if (isRecording.value && browserAsr.value) return '正在听写… 停止后文字会填入输入框'
  if (isRecording.value) return '正在录音… 停止后由服务端转写'
  return '输入你的指令, 按 Enter 发送; Shift+Enter 换行'
})

const speechErrorLabel = computed(() => speechError.value)

function appendDraft(text) {
  const t = (text || '').trim()
  if (!t) return false
  draft.value = (draft.value ? `${draft.value} ` : '') + t
  return true
}

async function toggleRecord() {
  if (!speechSupported.value) return

  if (browserAsr.value) {
    if (speech.isRecording.value) {
      speech.stop()
      mic.stop()
      const text = (liveDraft.value || speech.transcript.value).trim()
      liveDraft.value = ''
      speech.reset()
      if (!appendDraft(text)) {
        speechError.value = '没有识别到内容, 请靠近麦克风再试'
      }
    } else {
      speechError.value = ''
      liveDraft.value = ''
      speech.reset()
      speech.start()
      mic.start().catch((e) => {
        console.warn('[chat] mic level start failed:', mic.errorMsg.value, e)
      })
    }
    return
  }

  if (isRecording.value) {
    try {
      const text = await recorder.stop()
      mic.stop()
      if (!appendDraft(text)) {
        speechError.value = '没有识别到内容, 请靠近麦克风再试'
      }
    } catch (e) {
      mic.stop()
      const msg = recorder.errorMsg.value || (e && (e.message || String(e)))
      speechError.value = `转写失败: ${msg}`
    }
  } else {
    speechError.value = ''
    try {
      await recorder.start()
      mic.start().catch((e) => {
        console.warn('[chat] mic level start failed:', mic.errorMsg.value, e)
      })
    } catch (e) {
      const msg = recorder.errorMsg.value || (e && (e.message || String(e)))
      speechError.value = `录音启动失败: ${msg}`
    }
  }
}

const submit = async () => {
  const text = draft.value.trim()
  if (!text || status.value === 'thinking') return
  draft.value = ''
  // 发送时如果还在录音, 取消掉; 避免数字人播报时还在听自己
  if (speech.isRecording.value) {
    speech.stop()
    speech.reset()
    liveDraft.value = ''
    mic.stop()
  } else if (isRecording.value) {
    recorder.cancel()
    mic.stop()
  }
  try {
    await sendCommand(text)
  } catch (_) {
    // useSecretary 内已 push system message, 无需重复
  }
}

const roleLabel = (r) => {
  if (r === 'user') return '我'
  if (r === 'secretary') return '秘书'
  if (r === 'system') return '系统'
  return r
}

// 浏览器识别时实时填入输入框
watch(liveDraft, (t) => {
  if (speech.isRecording.value && t) draft.value = t
})

// 自动滚到底
watch(() => messages.length, async () => {
  await nextTick()
  const el = listEl.value
  if (el) el.scrollTop = el.scrollHeight
})

defineExpose({ submit })
</script>

<style scoped>
.chat {
  display: flex;
  flex-direction: column;
  min-height: 480px;
  padding: 0;
}
.chat__header {
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}
.chat__title {
  font-size: var(--fs-h3);
  font-weight: 600;
  margin: 0 0 2px;
  letter-spacing: -0.01em;
}
.chat__hint { margin: 0; }

.chat__messages {
  list-style: none;
  margin: 0;
  padding: var(--space-4) var(--space-5);
  flex: 1;
  overflow-y: auto;
  max-height: 60vh;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.chat__empty {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: var(--space-5);
  text-align: center;
}

.chat__msg {
  display: flex;
}
.chat__msg--user { justify-content: flex-end; }
.chat__msg--system { justify-content: center; }

.chat__bubble {
  max-width: 78%;
  padding: 10px 14px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}
.chat__msg--user .chat__bubble {
  background: var(--color-text);
  border-color: var(--color-text);
  color: var(--color-text-inverse);
  border-bottom-right-radius: 4px;
}
.chat__msg--user .chat__bubble .chat__role,
.chat__msg--user .chat__bubble .chat__content {
  color: var(--color-text-inverse);
}
.chat__msg--user .chat__bubble .chat__meta .text-dim {
  color: rgba(255, 255, 255, 0.6);
}
.chat__msg--secretary .chat__bubble {
  background: var(--color-bg);
  border-bottom-left-radius: 4px;
}
.chat__msg--system .chat__bubble {
  background: var(--color-surface-2);
  border-color: transparent;
  color: var(--color-text-2);
  font-size: var(--fs-small);
  border-radius: var(--radius-pill);
  padding: 6px 14px;
}
.chat__msg.is-error .chat__bubble {
  background: var(--color-danger-soft);
  border-color: transparent;
  color: var(--color-danger);
}
.chat__role { display: none; }
.chat__content {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: var(--fs-body);
  line-height: 1.55;
}
.chat__meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-top: 6px;
}

.chat__input {
  border-top: 1px solid var(--color-border);
  padding: var(--space-3) var(--space-4) var(--space-4);
  background: var(--color-surface);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.chat__actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}
.chat__status {
  color: var(--color-text-3);
  font-size: var(--fs-tiny);
}
.chat__status.is-thinking { color: var(--color-warning); }
.chat__status.is-speaking { color: var(--color-live); }
.chat__status.is-error    { color: var(--color-danger); }

.btn.is-active {
  background: var(--color-danger);
  border-color: var(--color-danger);
  color: #fff;
}
.btn.is-active:hover:not([disabled]) {
  background: #b91c1c;
  border-color: #b91c1c;
  color: #fff;
}

.chat__listening {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px 12px;
  border-radius: var(--radius);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  color: var(--color-text-2);
  font-size: var(--fs-small);
}
.chat__listening-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.chat__listening kbd {
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 0 5px;
  font-family: var(--font-mono);
  font-size: var(--fs-tiny);
  color: var(--color-text);
}

.meter {
  display: flex;
  align-items: stretch;
  gap: 3px;
  height: 16px;
  width: max-content;
}
.meter__bar {
  flex: 0 0 auto;
  width: 3px;
  height: 100%;
  border-radius: 2px;
  background: var(--color-surface-3);
  transition: background var(--dur-fast) var(--ease);
}
.meter__bar.is-on { background: var(--color-text); }

.dot, .rec-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-danger);
  display: inline-block;
  animation: chat-pulse 1.1s infinite ease-in-out;
}
.rec-dot { vertical-align: middle; margin-right: 4px; }
@keyframes chat-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%      { opacity: 0.4; transform: scale(0.7); }
}

.chat__alert {
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  background: var(--color-danger-soft);
  color: var(--color-danger);
  font-size: var(--fs-small);
}

.chat__debug {
  padding: 6px 10px;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  color: var(--color-text-2);
  word-break: break-all;
}
.chat__debug .text-danger { color: var(--color-danger); }
</style>
