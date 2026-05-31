<template>
  <div class="live-room">
    <div class="live-room__cluster">
      <div class="live-room__anchor">
        <aside
          v-if="meetPanelMounted"
          class="live-room__side live-room__side--left"
          :class="{ 'is-open': showMeetings }"
          :aria-hidden="!showMeetings"
        >
          <ScheduledMeetingsStrip ref="meetStripRef" />
        </aside>

        <div class="live-room__center">
        <div class="live-room__stage-wrap">
          <button
            type="button"
            class="live-panel-btn live-panel-btn--left"
            :class="{ 'is-open': showMeetings }"
            :aria-expanded="showMeetings"
            :title="showMeetings ? '收起已定会议' : '展开已定会议'"
            @click="toggleMeetings"
          >
            <span class="live-panel-btn__label">已定会议</span>
            <svg class="live-panel-btn__chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M15 18l-6-6 6-6" />
            </svg>
          </button>

          <div class="live-stage" :style="frameStyle()">
        <div class="live-stage__media" @click="onStageClick">
          <video
            ref="videoEl"
            class="live-stage__video"
            autoplay
            playsinline
            :muted="muted"
            @loadedmetadata="onVideoMetadata"
          />
        </div>

        <div class="live-stage__shade live-stage__shade--top" aria-hidden="true" />
        <div class="live-stage__shade live-stage__shade--bottom" aria-hidden="true" />

        <header class="live-stage__top">
          <div class="live-stage__brand">
            <LiveBrandMark size="sm" alt="会议秘书" />
            <span class="live-stage__title">会议秘书</span>
          </div>
          <div class="live-stage__toolbar">
            <button
              v-if="state === 'connected' && needsUnmute"
              type="button"
              class="live-action-btn live-action-btn--accent"
              @click="unmute"
            >
              <span class="live-action-btn__icon" aria-hidden="true">🔊</span>
              开声
            </button>
            <router-link to="/settings" custom v-slot="{ navigate }">
              <button
                type="button"
                class="live-action-btn live-action-btn--ghost"
                aria-label="设置"
                title="设置"
                @click="navigate"
              >
                <svg class="live-action-btn__svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                  <circle cx="12" cy="12" r="3"/>
                  <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>
                </svg>
              </button>
            </router-link>
            <button
              type="button"
              class="live-action-btn live-action-btn--ghost"
              aria-label="退出"
              title="退出"
              @click="$emit('logout')"
            >
              <svg class="live-action-btn__svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>
              </svg>
            </button>
          </div>
        </header>

        <div class="live-stage__copy">
          <VoiceDanmu
            :messages="messages"
            :status="status"
            :live-text="liveText"
          />
        </div>

        <div class="live-stage__dock">
          <div v-if="state !== 'connected' && state !== 'connecting'" class="live-stage__controls">
            <button
              type="button"
              class="live-ctrl__btn live-ctrl__btn--primary"
              @click="connect"
            >
              {{ state === 'failed' ? '重新连接' : '连接数字人' }}
            </button>
          </div>

          <form v-else class="dy-composer" @submit.prevent="onTextSubmit">
            <div class="dy-composer__box" :class="{ 'is-busy': busy && !listening }">
              <input
                v-model="draft"
                class="dy-composer__input"
                type="text"
                enterkeyhint="send"
                autocomplete="off"
                placeholder="说点什么…"
                :disabled="inputDisabled"
              />
              <button
                v-if="hasDraft"
                type="submit"
                class="dy-composer__send"
                :disabled="inputDisabled"
              >
                发送
              </button>
            </div>

            <button
              v-if="showInterruptBtn"
              type="button"
              class="dy-composer__fab dy-composer__fab--stop"
              title="打断播报"
              @click="onInterruptClick"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <rect x="6" y="6" width="12" height="12" rx="2" />
              </svg>
            </button>

            <button
              v-else
              type="button"
              class="dy-composer__fab"
              :class="{ 'is-recording': listening, 'is-disabled': micDisabled }"
              :disabled="micDisabled"
              :title="micTitle"
              @click="onMicClick"
            >
              <span v-if="listening" class="dy-composer__pulse" :style="ringStyle" aria-hidden="true" />
              <svg v-if="listening" width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <rect x="6" y="6" width="12" height="12" rx="2" />
              </svg>
              <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true">
                <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="22" />
              </svg>
            </button>
          </form>
        </div>

        <button
          v-if="state === 'connected' && needsUnmute"
          type="button"
          class="live-stage__unmute"
          @click="unmute"
        >
          🔇 点击开启数字人声音
        </button>

        <div v-if="state !== 'connected'" class="live-stage__mask">
          <p>{{ state === 'connecting' ? '连接数字人中…' : '连接后即可语音对话' }}</p>
          <button
            v-if="state !== 'connecting'"
            type="button"
            class="btn btn-primary"
            @click="connect"
          >
            连接数字人
          </button>
        </div>

        <p v-if="micError" class="live-stage__err">{{ micError }}</p>
          </div>

          <button
            type="button"
            class="live-panel-btn live-panel-btn--right"
            :class="{ 'is-open': showFocus }"
            :aria-expanded="showFocus"
            :title="showFocus ? '收起专注历史' : '展开专注历史'"
            @click="toggleFocus"
          >
            <span class="live-panel-btn__label">专注历史</span>
            <svg class="live-panel-btn__chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M9 18l6-6-6-6" />
            </svg>
          </button>
        </div>
        </div>

        <aside
          v-if="focusPanelMounted"
          class="live-room__side live-room__side--right"
          :class="{ 'is-open': showFocus }"
          :aria-hidden="!showFocus"
        >
          <FocusHistoryCharts ref="focusStripRef" />
        </aside>
      </div>
    </div>
    <footer class="live-room__credit" aria-label="演示说明与致谢">
      <div class="live-room__credit-row">
        <span class="live-room__credit-tag">DEMO</span>
        <span class="live-room__credit-sep" aria-hidden="true">·</span>
        <span>复旦大学</span>
        <span class="live-room__credit-sep" aria-hidden="true">·</span>
        <span>非商用</span>
        <span class="live-room__credit-sep" aria-hidden="true">·</span>
        <span>赵一飞信息</span>
      </div>
      <p class="live-room__thanks">
        <span class="live-room__thanks-label">感谢本项目用到的库：</span>
        <template v-for="(lib, index) in ackLibraries" :key="lib">
          <span>{{ lib }}</span>
          <span v-if="index < ackLibraries.length - 1" class="live-room__credit-sep" aria-hidden="true">·</span>
        </template>
      </p>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import LiveBrandMark from './LiveBrandMark.vue'
import VoiceDanmu from './VoiceDanmu.vue'
import ScheduledMeetingsStrip from './ScheduledMeetingsStrip.vue'
import FocusHistoryCharts from './FocusHistoryCharts.vue'
import { useWebRTC } from '@shared/composables/useWebRTC'
import { useAvatarFrameAspect } from '@shared/composables/useAvatarFrameAspect'
import { useAvatarVideoAudio } from '@shared/composables/useAvatarVideoAudio'

const meetStripRef = ref(null)
const focusStripRef = ref(null)

const ackLibraries = [
  'Linly-Talker-Stream',
  'Linly-Talker',
  'LiveTalking',
  'Vue 3',
  'Vite',
  'aiohttp',
  'aiortc',
  'Wav2Lip',
  'Whisper',
  'edge-tts',
  '通义千问',
]

const showMeetings = ref(false)
const showFocus = ref(false)
const meetPanelMounted = ref(false)
const focusPanelMounted = ref(false)

function toggleMeetings() {
  showMeetings.value = !showMeetings.value
  if (showMeetings.value) meetPanelMounted.value = true
}

function toggleFocus() {
  showFocus.value = !showFocus.value
  if (showFocus.value) focusPanelMounted.value = true
}

defineExpose({
  async refreshSidebars() {
    meetPanelMounted.value = true
    await nextTick()
    meetStripRef.value?.refresh?.()
  },
})

const props = defineProps({
  messages: { type: Array, default: () => [] },
  status: { type: String, default: 'idle' },
  listening: { type: Boolean, default: false },
  busy: { type: Boolean, default: false },
  avatarReady: { type: Boolean, default: false },
  level: { type: Number, default: 0 },
  liveText: { type: String, default: '' },
  micError: { type: String, default: '' },
})

const emit = defineEmits(['session', 'state', 'toggle-mic', 'send-text', 'interrupt', 'logout'])

const draft = ref('')
const hasDraft = computed(() => draft.value.trim().length > 0)

const videoEl = ref(null)
const { onVideoMetadata, frameStyle } = useAvatarFrameAspect(videoEl)
const { muted, needsUnmute, unmute, checkAudioState, scheduleAutoUnmute } = useAvatarVideoAudio(videoEl)

const {
  connectionState, sessionId, sharedStream,
  startPlay, stopPlay, attachVideo,
} = useWebRTC()

const state = computed(() => connectionState.value)
let detach = null

/** 说完发送后 → 思考/播报/上传阶段，主按钮变为打断 */
const showInterruptBtn = computed(
  () => props.avatarReady && !props.listening && props.busy
)
const micDisabled = computed(() => !props.avatarReady)
const inputDisabled = computed(() => !props.avatarReady || (props.busy && !props.listening))
const micTitle = computed(() => {
  if (!props.avatarReady) return '请先连接数字人'
  return props.listening ? '结束并发送' : '语音输入'
})
const ringStyle = computed(() => ({
  transform: `scale(${1 + props.level * 0.4})`,
  opacity: props.listening ? 0.5 + props.level * 0.5 : 0.25,
}))

function onMicClick() {
  unmute()
  emit('toggle-mic')
}

function onInterruptClick() {
  unmute()
  emit('interrupt')
}

function onTextSubmit() {
  const t = draft.value.trim()
  if (!t || inputDisabled.value) return
  draft.value = ''
  unmute()
  emit('send-text', t)
}

function onStageClick() {
  if (needsUnmute.value) unmute()
}

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

const connect = async () => {
  try {
    const sid = await startPlay()
    emit('session', sid)
    await unmute()
  } catch (_) {}
}

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
.live-room {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--color-surface);
  padding: env(safe-area-inset-top) env(safe-area-inset-right)
    env(safe-area-inset-bottom) env(safe-area-inset-left);
}

.live-room__credit {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  width: 100%;
  padding: var(--space-2) var(--space-3);
  font-size: 11px;
  color: var(--color-text-3);
  letter-spacing: 0.02em;
  user-select: none;
}
.live-room__credit-row {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 6px;
}
.live-room__thanks {
  margin: 0;
  max-width: min(920px, 100%);
  text-align: center;
  line-height: 1.5;
  font-size: 10px;
  color: var(--color-text-3);
}
.live-room__thanks-label {
  color: var(--color-text-2);
}
.live-room__credit-tag {
  display: inline-flex;
  align-items: center;
  padding: 1px 7px;
  border-radius: var(--radius-pill);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--color-text-2);
  background: rgba(0, 0, 0, 0.05);
  border: 1px solid var(--color-border);
}
.live-room__credit-sep {
  opacity: 0.45;
}

/* 数字人居中固定，侧栏向左右外侧展开 */
.live-room__cluster {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  padding: 0 var(--space-2);
}

.live-room__anchor {
  position: relative;
  flex-shrink: 0;
  width: fit-content;
  max-width: min(calc(100vw - var(--space-4)), 520px);
}

.live-room__side {
  position: absolute;
  top: 50%;
  width: 0;
  max-height: min(78dvh, 720px);
  overflow: hidden;
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transform: translateY(-50%);
  transition:
    width 0.28s var(--ease),
    opacity 0.22s var(--ease),
    visibility 0.28s var(--ease);
  z-index: 1;
}
.live-room__side.is-open {
  width: min(220px, 28vw);
  opacity: 1;
  visibility: visible;
  pointer-events: auto;
}
.live-room__side--left {
  right: calc(100% + var(--space-3));
  transform-origin: right center;
}
.live-room__side--right {
  left: calc(100% + var(--space-3));
  transform-origin: left center;
}
.live-room__side :deep(.meet-strip),
.live-room__side :deep(.focus-strip) {
  width: min(220px, 28vw);
  min-width: min(220px, 28vw);
}

.live-room__center {
  position: relative;
  z-index: 2;
  width: fit-content;
  max-width: 100%;
}

/* 数字人 + 外侧贴边切换钮（不在画面内） */
.live-room__stage-wrap {
  display: flex;
  align-items: stretch;
  width: min(calc(100vw - var(--space-4)), 480px);
  max-width: 480px;
  margin: 0 auto;
}

.live-panel-btn {
  flex-shrink: 0;
  align-self: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-height: 72px;
  padding: 10px 5px;
  border: 1px solid var(--color-border);
  background: rgba(255, 255, 255, 0.96);
  color: var(--color-text-2);
  cursor: pointer;
  box-shadow: var(--shadow-1);
  transition: background var(--dur-fast) var(--ease), border-color var(--dur-fast) var(--ease), color var(--dur-fast) var(--ease);
}
.live-panel-btn:hover {
  background: #fff;
  border-color: var(--color-accent);
  color: var(--color-text);
}
.live-panel-btn.is-open {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: #fff;
}
.live-panel-btn--left {
  margin-right: -1px;
  border-radius: var(--radius-lg) 0 0 var(--radius-lg);
}
.live-panel-btn--right {
  margin-left: -1px;
  border-radius: 0 var(--radius-lg) var(--radius-lg) 0;
}

.live-room__stage-wrap .live-stage {
  flex: 1 1 auto;
  min-width: 0;
  min-height: 280px;
  margin: 0;
}
.live-panel-btn__label {
  font-size: 10px;
  font-weight: 600;
  line-height: 1.2;
  letter-spacing: 0.04em;
}
.live-panel-btn--left .live-panel-btn__label,
.live-panel-btn--right .live-panel-btn__label {
  writing-mode: vertical-rl;
}
.live-panel-btn__chev {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  transition: transform 0.2s var(--ease);
}
/* 左：收起时 ← 展开，展开后 → 收起 */
.live-panel-btn--left.is-open .live-panel-btn__chev {
  transform: rotate(180deg);
}
/* 右：收起时 → 展开，展开后 ← 收起 */
.live-panel-btn--right.is-open .live-panel-btn__chev {
  transform: rotate(180deg);
}

@media (max-width: 960px) {
  .live-room__side {
    top: auto;
    transform: none;
    max-height: 200px;
    width: 100%;
    left: 0;
    right: 0;
  }
  .live-room__side--left {
    right: auto;
    bottom: calc(100% + var(--space-2));
    transform-origin: bottom center;
  }
  .live-room__side--right {
    left: 0;
    top: calc(100% + var(--space-2));
    transform-origin: top center;
  }
  .live-room__side:not(.is-open) {
    max-height: 0;
  }
  .live-room__side.is-open {
    width: 100%;
    max-height: 200px;
  }
  .live-room__side :deep(.meet-strip),
  .live-room__side :deep(.focus-strip) {
    width: 100%;
    min-width: 0;
    max-height: 200px;
    min-height: 160px;
  }
  .live-room__anchor {
    max-width: min(100vw, 420px);
  }
  .live-room__stage-wrap {
    width: min(100vw, 420px);
  }
  .live-room__center {
    max-width: min(100vw, 420px);
  }
  .live-room__stage-wrap {
    flex-wrap: wrap;
    justify-content: center;
    gap: var(--space-2);
    max-width: 100%;
  }
  .live-room__stage-wrap .live-stage {
    flex: 1 1 100%;
    order: 0;
  }
  .live-panel-btn {
    flex-direction: row;
    min-height: 0;
    padding: 8px 12px;
    border-radius: var(--radius-pill);
    margin: 0;
  }
  .live-panel-btn--left {
    order: 1;
  }
  .live-panel-btn--right {
    order: 2;
  }
  .live-panel-btn__label {
    writing-mode: horizontal-tb;
  }
}

.live-stage {
  position: relative;
  margin: 0 auto;
  border-radius: var(--radius-xl);
  overflow: hidden;
  background: #0a0a0a;
  box-shadow: var(--shadow-3);
}

.live-stage__media {
  position: absolute;
  inset: 0;
  background: #0a0a0a;
}
.live-stage__video {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
}

.live-stage__shade {
  position: absolute;
  left: 0;
  right: 0;
  pointer-events: none;
  z-index: 1;
}
.live-stage__shade--top {
  top: 0;
  height: 88px;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.5) 0%, transparent 100%);
}
.live-stage__shade--bottom {
  bottom: 0;
  height: 50%;
  background: linear-gradient(0deg, rgba(0, 0, 0, 0.72) 0%, transparent 100%);
}

/* 顶栏 */
.live-stage__top {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 4;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
}
.live-stage__brand {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  font-size: var(--fs-h4);
  line-height: 1;
}
.live-stage__title {
  font-size: inherit;
  font-weight: 600;
  color: #fff;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.55);
  letter-spacing: -0.02em;
}
.live-stage__toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.live-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 36px;
  padding: 0 14px;
  border-radius: var(--radius);
  border: 1px solid rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.96);
  color: var(--color-text);
  font-family: var(--font-sans);
  font-size: var(--fs-tiny);
  font-weight: 600;
  line-height: 1;
  cursor: pointer;
  text-decoration: none;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.18);
  transition: background var(--dur-fast) var(--ease), transform var(--dur-fast) var(--ease);
}
.live-action-btn:hover {
  background: #fff;
  transform: translateY(-1px);
}
.live-action-btn:active {
  transform: translateY(0);
}
/* 半透明图标按钮（设置 / 退出） */
.live-action-btn--ghost {
  width: 40px;
  height: 40px;
  min-height: 40px;
  padding: 0;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.32);
  color: rgba(255, 255, 255, 0.92);
  box-shadow: none;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}
.live-action-btn--ghost:hover {
  background: rgba(0, 0, 0, 0.48);
  border-color: rgba(255, 255, 255, 0.38);
  color: #fff;
  transform: none;
}
.live-action-btn--ghost .live-action-btn__svg {
  width: 18px;
  height: 18px;
}
.live-action-btn--accent {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: #fff;
}
.live-action-btn--accent:hover {
  background: var(--color-accent-2);
  color: #fff;
}
.live-action-btn__svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}
.live-action-btn__icon {
  font-size: 14px;
  line-height: 1;
}

/* 底部：对话在上、按钮居中在下 */
.live-stage__dock {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 5;
  padding: 0 var(--space-3) max(10px, env(safe-area-inset-bottom));
}

/* 对话区：自下向上，超过画面中线处淡出 */
.live-stage__copy {
  position: absolute;
  left: var(--space-4);
  right: var(--space-4);
  top: 42%;
  bottom: 56px;
  z-index: 3;
  pointer-events: none;
  overflow: hidden;
  -webkit-mask-image: linear-gradient(
    to bottom,
    transparent 0%,
    rgba(0, 0, 0, 0.25) 12%,
    black 32%,
    black 100%
  );
  mask-image: linear-gradient(
    to bottom,
    transparent 0%,
    rgba(0, 0, 0, 0.25) 12%,
    black 32%,
    black 100%
  );
}

.live-stage__controls {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: var(--space-4);
  min-height: 44px;
  padding-bottom: 2px;
}

/* 抖音风底部：深色胶囊输入 + 右侧圆形麦 */
.dy-composer {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.dy-composer__box {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  height: 38px;
  padding: 0 4px 0 14px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.38);
  border: 1px solid rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  transition: background 0.2s ease, border-color 0.2s ease;
}
.dy-composer__box:focus-within {
  background: rgba(0, 0, 0, 0.48);
  border-color: rgba(255, 255, 255, 0.22);
}
.dy-composer__box.is-busy {
  opacity: 0.72;
}

.dy-composer__input {
  flex: 1;
  min-width: 0;
  height: 100%;
  padding: 0;
  border: 0;
  background: transparent;
  color: rgba(255, 255, 255, 0.96);
  font-family: var(--font-sans);
  font-size: 14px;
  outline: none;
}
.dy-composer__input::placeholder {
  color: rgba(255, 255, 255, 0.48);
}
.dy-composer__input:disabled {
  cursor: not-allowed;
}

.dy-composer__send {
  flex-shrink: 0;
  height: 30px;
  padding: 0 12px;
  margin-right: 2px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: #fe2c55;
  font-family: var(--font-sans);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s ease;
}
.dy-composer__send:hover:not(:disabled) {
  opacity: 0.85;
}
.dy-composer__send:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.dy-composer__fab {
  position: relative;
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.38);
  border: 1px solid rgba(255, 255, 255, 0.14);
  color: rgba(255, 255, 255, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  transition: transform 0.15s ease, background 0.15s ease;
}
.dy-composer__fab:hover:not(:disabled) {
  transform: scale(1.06);
  background: rgba(0, 0, 0, 0.5);
}
.dy-composer__fab.is-recording {
  background: #fe2c55;
  border-color: #fe2c55;
  color: #fff;
  box-shadow: 0 0 0 3px rgba(254, 44, 85, 0.28);
}
.dy-composer__fab--stop {
  background: rgba(254, 44, 85, 0.92);
  border-color: rgba(254, 44, 85, 0.92);
  color: #fff;
}
.dy-composer__fab.is-disabled,
.dy-composer__fab:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
}

.dy-composer__pulse {
  position: absolute;
  inset: -5px;
  border-radius: 50%;
  border: 2px solid rgba(254, 44, 85, 0.75);
  pointer-events: none;
  transition: transform 80ms linear, opacity 80ms linear;
}
.live-ctrl__btn {
  border: 0;
  cursor: pointer;
  font-family: var(--font-sans);
}
.live-ctrl__btn--primary {
  align-self: center;
  padding: 12px 20px;
  border-radius: var(--radius-pill);
  background: #fff;
  color: var(--color-text);
  font-size: var(--fs-small);
  font-weight: 600;
}

.live-stage__unmute {
  position: absolute;
  left: 50%;
  bottom: 160px;
  transform: translateX(-50%);
  z-index: 20;
  padding: 8px 16px;
  border: 0;
  border-radius: var(--radius-pill);
  background: rgba(255, 255, 255, 0.92);
  color: var(--color-text);
  font-size: var(--fs-tiny);
  font-weight: 600;
  cursor: pointer;
}

.live-stage__mask {
  position: absolute;
  inset: 0;
  z-index: 7;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  background: rgba(252, 252, 250, 0.88);
  color: var(--color-text-2);
  font-size: var(--fs-small);
}

.live-stage__err {
  position: absolute;
  left: var(--space-4);
  right: var(--space-4);
  bottom: calc(56px + env(safe-area-inset-bottom));
  z-index: 6;
  margin: 0;
  padding: 8px 12px;
  border-radius: var(--radius);
  background: rgba(220, 38, 38, 0.88);
  color: #fff;
  font-size: var(--fs-tiny);
  text-align: center;
}
</style>
