<template>
  <div class="mic-bar">
    <p class="mic-bar__status" :class="`is-${statusKind}`">{{ statusText }}</p>

    <div class="mic-bar__main">
      <button
        type="button"
        class="mic-bar__btn"
        :class="{
          'is-listening': listening,
          'is-busy': busy,
        }"
        :disabled="busy || !avatarReady"
        :title="micTitle"
        @click="onMicClick"
      >
        <span class="mic-bar__ring" :style="ringStyle" aria-hidden="true" />
        <span class="mic-bar__icon" aria-hidden="true">
          <svg v-if="listening" width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
            <rect x="6" y="6" width="12" height="12" rx="2" />
          </svg>
          <svg v-else width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="22" />
          </svg>
        </span>
      </button>

      <div class="mic-bar__side">
        <button
          v-if="canInterrupt"
          type="button"
          class="btn btn-sm"
          @click="$emit('interrupt')"
        >
          打断播报
        </button>
        <span class="text-tiny text-muted">{{ engineHint }}</span>
      </div>
    </div>

    <form class="mic-bar__text" @submit.prevent="onTextSubmit">
      <input
        v-model="draft"
        class="input"
        placeholder="或输入文字发送…"
        :disabled="busy"
      />
      <button type="submit" class="btn btn-primary" :disabled="busy || !draft.trim()">
        发送
      </button>
    </form>

    <p v-if="liveText" class="mic-bar__live text-small">
      <span class="text-muted">识别中：</span>{{ liveText }}
    </p>
    <p v-if="error" class="mic-bar__err text-tiny">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { speechEngineLabel } from '@shared/utils/speech'

const props = defineProps({
  busy: { type: Boolean, default: false },
  listening: { type: Boolean, default: false },
  avatarReady: { type: Boolean, default: false },
  status: { type: String, default: 'idle' },
  level: { type: Number, default: 0 },
  liveText: { type: String, default: '' },
  error: { type: String, default: '' },
  canInterrupt: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle-mic', 'send-text', 'interrupt'])

const draft = ref('')
const engineHint = speechEngineLabel()

const statusKind = computed(() => {
  if (props.listening) return 'listen'
  return props.status
})

const statusText = computed(() => {
  if (!props.avatarReady) return '请先连接数字人'
  if (props.listening) return '正在聆听，再次点击结束并发送'
  switch (props.status) {
    case 'thinking': return '秘书思考中…'
    case 'speaking': return '数字人播报中…'
    case 'error': return '出错了，请重试'
    default: return '点击麦克风开始说话'
  }
})

const micTitle = computed(() => {
  if (!props.avatarReady) return '数字人未连接'
  if (props.busy) return '请等待当前回复结束'
  return props.listening ? '结束录音并发送' : '开始说话'
})

const ringStyle = computed(() => ({
  transform: `scale(${1 + props.level * 0.35})`,
  opacity: props.listening ? 0.35 + props.level * 0.5 : 0.2,
}))

function onMicClick() {
  if (props.busy || !props.avatarReady) return
  emit('toggle-mic')
}

function onTextSubmit() {
  const t = draft.value.trim()
  if (!t || props.busy) return
  draft.value = ''
  emit('send-text', t)
}
</script>

<style scoped>
.mic-bar {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.mic-bar__status {
  margin: 0;
  text-align: center;
  font-size: var(--fs-small);
  font-weight: 500;
  color: var(--color-text-2);
}
.mic-bar__status.is-listen { color: var(--color-accent); }
.mic-bar__status.is-speaking { color: var(--color-live); }
.mic-bar__status.is-thinking { color: var(--color-warning); }

.mic-bar__main {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
}
.mic-bar__btn {
  position: relative;
  width: 88px;
  height: 88px;
  border: 0;
  border-radius: 50%;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform var(--dur-fast) var(--ease),
    background var(--dur-fast) var(--ease);
  box-shadow: var(--shadow-2);
}
.mic-bar__btn:hover:not(:disabled) {
  transform: scale(1.04);
  background: var(--color-primary-hover);
}
.mic-bar__btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.mic-bar__btn.is-listening {
  background: var(--color-accent);
}
.mic-bar__btn.is-busy:not(.is-listening) {
  background: var(--color-text-3);
}
.mic-bar__ring {
  position: absolute;
  inset: -10px;
  border-radius: 50%;
  border: 2px solid var(--color-accent);
  pointer-events: none;
  transition: transform 80ms linear, opacity 80ms linear;
}
.mic-bar__btn:not(.is-listening) .mic-bar__ring {
  border-color: var(--color-border-strong);
}
.mic-bar__side {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-2);
  max-width: 140px;
}

.mic-bar__text {
  display: flex;
  gap: var(--space-2);
  align-items: center;
}
.mic-bar__text .input {
  flex: 1;
  min-width: 0;
  margin: 0;
}
.mic-bar__live {
  margin: 0;
  padding: var(--space-2) var(--space-3);
  background: var(--color-accent-soft);
  border-radius: var(--radius);
  color: var(--color-text);
}
.mic-bar__err {
  margin: 0;
  color: var(--color-danger);
  text-align: center;
}
</style>
