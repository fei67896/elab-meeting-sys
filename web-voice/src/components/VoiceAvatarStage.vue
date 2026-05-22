<template>
  <div class="voice-stage">
    <div class="voice-stage__meta">
      <span class="voice-stage__pill" :class="`is-${state}`">
        <span class="voice-stage__dot" aria-hidden="true" />
        {{ stateLabel }}
      </span>
      <button
        v-if="state === 'connected'"
        type="button"
        class="btn btn-sm btn-ghost"
        @click="disconnect"
      >
        断开
      </button>
      <button
        v-else-if="state === 'failed' || state === 'closed' || state === 'idle'"
        type="button"
        class="btn btn-sm btn-primary"
        @click="connect"
      >
        {{ state === 'failed' ? '重连' : '连接数字人' }}
      </button>
    </div>

    <div class="voice-stage__frame-wrap">
    <div class="voice-stage__frame" :style="frameStyle()">
      <video
        ref="videoEl"
        class="voice-stage__video"
        autoplay
        playsinline
        :muted="muted"
        @loadedmetadata="onVideoMetadata"
      />
      <button
        v-if="needsUnmute"
        type="button"
        class="voice-stage__unmute"
        @click="unmute"
      >
        🔇 点击恢复声音
      </button>
      <div v-if="state !== 'connected'" class="voice-stage__placeholder">
        <p class="text-small text-muted">
          {{ state === 'connecting' ? '正在连接数字人…' : '连接后即可语音对话' }}
        </p>
      </div>
    </div>
    </div>

    <p class="voice-stage__hint text-tiny text-muted">
      对着麦克风说话，秘书会通过数字人语音回复
    </p>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useWebRTC } from '@shared/composables/useWebRTC'
import { useAvatarFrameAspect } from '@shared/composables/useAvatarFrameAspect'

const emit = defineEmits(['session', 'state'])

const videoEl = ref(null)
const { onVideoMetadata, frameStyle } = useAvatarFrameAspect(videoEl)
const muted = ref(true)
const needsUnmute = ref(false)

const {
  connectionState, sessionId, sharedStream,
  startPlay, stopPlay, attachVideo,
} = useWebRTC()

const state = computed(() => connectionState.value)
let detach = null

const stateLabel = computed(() => {
  switch (state.value) {
    case 'idle': return '未连接'
    case 'connecting': return '连接中'
    case 'connected': return '已连接'
    case 'failed': return '连接失败'
    case 'closed': return '已断开'
    default: return state.value
  }
})

async function unmute() {
  const v = videoEl.value
  if (!v) return
  v.muted = false
  muted.value = false
  try {
    await v.play()
    needsUnmute.value = false
  } catch (_) {
    needsUnmute.value = true
  }
}

watch(state, (s) => {
  if (s === 'connected') setTimeout(unmute, 500)
})
watch(sharedStream, (s) => {
  if (s) {
    setTimeout(unmute, 300)
    setTimeout(onVideoMetadata, 200)
  }
})

const connect = async () => {
  try {
    const sid = await startPlay()
    emit('session', sid)
  } catch (_) {}
}

const disconnect = () => stopPlay()

watch(sessionId, (v) => emit('session', v))
watch(state, (v) => emit('state', v))

onMounted(() => {
  detach = attachVideo(videoEl)
  if (state.value !== 'connected' && state.value !== 'connecting') {
    setTimeout(() => connect(), 300)
  }
})

onBeforeUnmount(() => {
  if (detach) { detach(); detach = null }
})
</script>

<style scoped>
.voice-stage {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.voice-stage__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}
.voice-stage__pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  border-radius: var(--radius-pill);
  font-size: var(--fs-tiny);
  font-weight: 500;
  background: var(--color-surface-2);
  color: var(--color-text-2);
}
.voice-stage__pill.is-connected {
  background: var(--color-live-soft);
  color: var(--color-live);
}
.voice-stage__pill.is-connecting {
  background: var(--color-warning-soft);
  color: var(--color-warning);
}
.voice-stage__pill.is-failed {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}
.voice-stage__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}
.voice-stage__pill.is-connecting .voice-stage__dot {
  animation: pulse 1.2s ease infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}

.voice-stage__frame-wrap {
  flex: 1;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
}
.voice-stage__frame {
  position: relative;
  margin: 0;
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--color-border);
  background: #0a0a0a;
  box-shadow: var(--shadow-2);
}
.voice-stage__video {
  position: absolute;
  inset: 0;
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
}
.voice-stage__placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface-2);
}
.voice-stage__unmute {
  position: absolute;
  left: 50%;
  bottom: 16px;
  transform: translateX(-50%);
  z-index: 2;
  padding: 8px 16px;
  border: 0;
  border-radius: var(--radius-pill);
  background: var(--color-text);
  color: var(--color-text-inverse);
  font-size: var(--fs-tiny);
  cursor: pointer;
  box-shadow: var(--shadow-2);
}
.voice-stage__hint {
  text-align: center;
  margin: 0;
}
</style>
