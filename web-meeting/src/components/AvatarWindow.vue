<template>
  <div class="avatar-window card">
    <header class="avatar-window__header">
      <div>
        <h3 class="avatar-window__title">数字人秘书</h3>
        <span class="avatar-window__status text-tiny" :class="`is-${state}`">
          {{ stateLabel }}
        </span>
      </div>
      <div class="flex gap-2">
        <button
          v-if="state === 'failed' || state === 'closed' || (!autoConnect && state === 'idle')"
          class="btn btn-sm btn-primary"
          @click="connect"
        >
          {{ state === 'failed' ? '重连' : '连接' }}
        </button>
        <button
          v-else-if="state === 'connected'"
          class="btn btn-sm btn-ghost"
          @click="disconnect"
          title="断开数字人 (会影响所有页面)"
        >
          断开
        </button>
      </div>
    </header>

    <div class="avatar-window__stage-wrap">
    <div class="avatar-window__stage" :style="frameStyle()">
      <video
        ref="videoEl"
        class="avatar-window__video"
        autoplay
        playsinline
        :muted="muted"
        @loadedmetadata="onVideoMetadata"
      />
      <button
        v-if="needsUnmute"
        type="button"
        class="avatar-window__unmute"
        @click="unmute"
        title="浏览器已自动静音, 点击恢复声音"
      >
        <span aria-hidden="true">🔇</span>
        点击恢复声音
      </button>
      <div v-if="state !== 'connected'" class="avatar-window__placeholder">
        <div class="placeholder-figure">
          <svg viewBox="0 0 64 64" width="56" height="56" aria-hidden="true">
            <circle cx="32" cy="24" r="12" fill="none"
                    stroke="currentColor" stroke-width="2"/>
            <path d="M12 56c2-12 11-18 20-18s18 6 20 18"
                  fill="none" stroke="currentColor" stroke-width="2"/>
          </svg>
        </div>
        <p class="text-small text-muted">
          {{ state === 'connecting' ? '正在连接数字人服务…' : '点击连接以唤起数字人' }}
        </p>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useWebRTC } from '../composables/useWebRTC'
import { useAvatarFrameAspect } from '../composables/useAvatarFrameAspect'
import { useAvatarVideoAudio } from '../composables/useAvatarVideoAudio'

const props = defineProps({
  autoConnect: { type: Boolean, default: true },
})

const emit = defineEmits(['session', 'state'])

const videoEl = ref(null)
const { onVideoMetadata, frameStyle } = useAvatarFrameAspect(videoEl)
const { muted, needsUnmute, unmute, checkAudioState, scheduleAutoUnmute } = useAvatarVideoAudio(videoEl)

const {
  connectionState, sessionId, sharedStream,
  startPlay, stopPlay, attachVideo,
} = useWebRTC()

const state = computed(() => connectionState.value)
let detach = null

watch(state, (s) => {
  if (s === 'connected') scheduleAutoUnmute(500)
})
watch(sharedStream, (s) => {
  if (s) {
    scheduleAutoUnmute(300)
    setTimeout(onVideoMetadata, 200)
    setTimeout(checkAudioState, 900)
  }
})

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

const connect = async () => {
  try {
    const sid = await startPlay()
    emit('session', sid)
    await unmute()
  } catch (_) {}
}

const disconnect = () => {
  stopPlay()
}

watch(sessionId, (v) => emit('session', v))
watch(state, (v) => emit('state', v))

onMounted(() => {
  // 把本地 <video> 附着到全局共享流; 已连接就立刻显示, 未连接等连上自动 attach
  detach = attachVideo(videoEl)
  if (props.autoConnect && state.value !== 'connected' && state.value !== 'connecting') {
    setTimeout(() => connect(), 200)
  }
})

onBeforeUnmount(() => {
  // 离开页面只解除附着, 不关 WebRTC 连接
  // (这样切到移动秘书 / 设置等页面时, 数字人 TTS 不被打断)
  if (detach) { detach(); detach = null }
})
</script>

<style scoped>
.avatar-window {
  padding: var(--space-3) var(--space-4) var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.avatar-window__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}
.avatar-window__title {
  font-size: var(--fs-h3);
  font-weight: 600;
  margin: 0;
  letter-spacing: -0.01em;
}
.avatar-window__status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--color-text-3);
  font-size: var(--fs-tiny);
}
.avatar-window__status::before {
  content: '';
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--color-text-3);
}
.avatar-window__status.is-connecting::before { background: var(--color-warning); animation: pulse 1.2s infinite; }
.avatar-window__status.is-connected::before  { background: var(--color-live); }
.avatar-window__status.is-failed::before     { background: var(--color-danger); }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.avatar-window__stage-wrap {
  display: flex;
  justify-content: center;
  width: 100%;
}
.avatar-window__stage {
  position: relative;
  background: #0a0a0a;
  border-radius: var(--radius);
  overflow: hidden;
  border: 1px solid var(--color-border);
}
.avatar-window__video {
  position: absolute;
  inset: 0;
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
}
.avatar-window__placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  color: var(--color-text-3);
  background: var(--color-surface-2);
}
.avatar-window__unmute {
  position: absolute;
  left: 50%;
  bottom: 12px;
  transform: translateX(-50%);
  padding: 6px 14px;
  background: var(--color-text);
  color: var(--color-text-inverse);
  border: 0;
  border-radius: var(--radius-pill);
  font-size: var(--fs-tiny);
  font-weight: 500;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  z-index: 2;
  box-shadow: var(--shadow-2);
}
.avatar-window__unmute:hover { background: var(--color-primary-hover); }
.placeholder-figure {
  color: var(--color-text-3);
  opacity: 0.6;
}
</style>
