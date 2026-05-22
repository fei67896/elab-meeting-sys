<template>
  <div class="dy-video">
    <video
      ref="videoEl"
      class="dy-video__el"
      autoplay
      playsinline
      :muted="muted"
    />
    <button
      v-if="needsUnmute"
      type="button"
      class="dy-video__unmute"
      @click="unmute"
    >
      🔇 点击开声
    </button>
    <div v-if="state !== 'connected'" class="dy-video__mask">
      <p v-if="state === 'connecting'" class="dy-video__hint">连接数字人中…</p>
      <button
        v-else
        type="button"
        class="dy-video__connect"
        @click="connect"
      >
        {{ state === 'failed' ? '重新连接' : '连接数字人' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useWebRTC } from '../../composables/useWebRTC'
const props = defineProps({
  active: { type: Boolean, default: false },
})

const emit = defineEmits(['session', 'state'])

const videoEl = ref(null)
const muted = ref(true)
const needsUnmute = ref(false)

const {
  connectionState, sessionId, sharedStream,
  startPlay, stopPlay, attachVideo,
} = useWebRTC()

const state = computed(() => connectionState.value)
let detach = null

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
  if (s) setTimeout(unmute, 300)
})

// 进入 active 时, 如果还没连就连一下; 离开 active 不再断连接
// (全局共享, 工作台 / 其他页面也在用)
watch(
  () => props.active,
  async (on) => {
    if (on && state.value !== 'connected' && state.value !== 'connecting') {
      await connect()
    }
  },
  { immediate: true }
)

async function connect() {
  try {
    const sid = await startPlay()
    emit('session', sid)
  } catch (_) {}
}

watch(sessionId, (v) => emit('session', v))
watch(state, (v) => emit('state', v))

onMounted(() => {
  detach = attachVideo(videoEl)
})

onBeforeUnmount(() => {
  // 切走只解除附着, 不关 WebRTC
  if (detach) { detach(); detach = null }
})
</script>

<style scoped>
.dy-video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  background: #0a0a0a;
}
.dy-video__el {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
}
.dy-video__mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(250, 251, 252, 0.92);
}
.dy-video__hint {
  color: var(--color-text-2);
  font-size: var(--fs-body);
  font-family: var(--font-sans);
}
.dy-video__connect {
  padding: 10px 24px;
  border: 0;
  border-radius: var(--radius);
  background: var(--color-primary);
  color: var(--color-text-inverse);
  font-size: var(--fs-body);
  font-weight: 600;
  font-family: var(--font-sans);
  cursor: pointer;
}
.dy-video__connect:hover {
  background: var(--color-primary-hover);
}
.dy-video__unmute {
  position: absolute;
  left: 50%;
  bottom: 120px;
  transform: translateX(-50%);
  z-index: 5;
  padding: 8px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  background: var(--color-bg);
  color: var(--color-primary);
  font-size: var(--fs-small);
  cursor: pointer;
  box-shadow: var(--shadow-1);
}
</style>
