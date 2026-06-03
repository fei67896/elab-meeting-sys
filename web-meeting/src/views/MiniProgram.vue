<template>
  <MiniProgramShell active-tab="secretary">
    <p class="wx-banner">
      文字交互 · 服务端大模型 · 数字人由服务端播报（无需端侧语音识别）
    </p>

    <div class="wx-stage">
      <div class="wx-stage__top">
        <button
          v-for="item in menuTop"
          :key="item.id"
          type="button"
          class="wx-chip"
          :disabled="busy && item.type === 'command'"
          @click="onMenu(item)"
        >
          <span class="wx-chip__icon">{{ item.icon }}</span>
          {{ item.label }}
        </button>
      </div>

      <div class="wx-stage__mid">
        <div class="wx-menu-col wx-menu-col--left">
          <button
            v-for="item in menuLeft"
            :key="item.id"
            type="button"
            class="wx-menu-btn"
            :disabled="busy && item.type === 'command'"
            @click="onMenu(item)"
          >
            <span class="wx-menu-btn__icon">{{ item.icon }}</span>
            <span class="wx-menu-btn__label">{{ item.label }}</span>
          </button>
        </div>

        <div class="wx-avatar" :style="frameStyle()">
          <video
            ref="videoEl"
            class="wx-avatar__video"
            autoplay
            playsinline
            :muted="muted"
            @loadedmetadata="onVideoMetadata"
          />
          <div v-if="state !== 'connected'" class="wx-avatar__mask">
            <p v-if="state === 'connecting'">连接中…</p>
            <button v-else type="button" class="wx-btn wx-btn--green" @click="connect">
              连接数字人
            </button>
          </div>
          <button
            v-if="needsUnmute"
            type="button"
            class="wx-avatar__unmute"
            @click="unmute"
          >
            🔊 开声
          </button>
          <span class="wx-avatar__badge">{{ statusLabel }}</span>
        </div>

        <div class="wx-menu-col wx-menu-col--right">
          <button
            v-for="item in menuRight"
            :key="item.id"
            type="button"
            class="wx-menu-btn"
            :disabled="busy && item.type === 'command'"
            @click="onMenu(item)"
          >
            <span class="wx-menu-btn__icon">{{ item.icon }}</span>
            <span class="wx-menu-btn__label">{{ item.label }}</span>
          </button>
        </div>
      </div>

      <div class="wx-stage__bottom">
        <button
          v-for="item in menuBottom"
          :key="item.id"
          type="button"
          class="wx-chip"
          :disabled="busy && item.type === 'command'"
          @click="onMenu(item)"
        >
          <span class="wx-chip__icon">{{ item.icon }}</span>
          {{ item.label }}
        </button>
      </div>
    </div>

    <div ref="chatEl" class="wx-chat">
      <p v-if="!visibleMessages.length" class="wx-chat__empty">
        输入文字或点周围菜单，秘书会通过数字人回复
      </p>
      <div
        v-for="m in visibleMessages"
        :key="m.id"
        class="wx-bubble"
        :class="`is-${m.role}`"
      >
        <p class="wx-bubble__text">{{ m.content || '…' }}</p>
      </div>
    </div>

    <form class="wx-composer" @submit.prevent="onSend">
      <input
        v-model="draft"
        class="wx-composer__input"
        type="text"
        enterkeyhint="send"
        placeholder="输入指令，无需语音…"
        :disabled="busy"
      />
      <button
        v-if="showInterrupt"
        type="button"
        class="wx-composer__send wx-composer__send--warn"
        @click="onInterrupt"
      >
        打断
      </button>
      <button
        v-else
        type="submit"
        class="wx-composer__send"
        :disabled="!draft.trim() || busy"
      >
        发送
      </button>
    </form>
  </MiniProgramShell>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import MiniProgramShell from '../components/miniprogram/MiniProgramShell.vue'
import { MINI_MENU } from '../components/miniprogram/miniActions'
import { useSecretary } from '../composables/useSecretary'
import { useWebRTC } from '../composables/useWebRTC'
import { useAvatarFrameAspect } from '../composables/useAvatarFrameAspect'
import { useAvatarVideoAudio } from '../composables/useAvatarVideoAudio'
import { avatarApi } from '../api/meeting'

const router = useRouter()
const { messages, status, sendCommand, setSessionId } = useSecretary()
const { sessionId, connectionState, startPlay, attachVideo } = useWebRTC()

const videoEl = ref(null)
const chatEl = ref(null)
const draft = ref('')
const { onVideoMetadata, frameStyle } = useAvatarFrameAspect(videoEl)
const { muted, needsUnmute, unmute, scheduleAutoUnmute } = useAvatarVideoAudio(videoEl)

const menuLeft = MINI_MENU.left
const menuRight = MINI_MENU.right
const menuTop = MINI_MENU.top
const menuBottom = MINI_MENU.bottom

const state = computed(() => connectionState.value)
const busy = computed(() => status.value === 'thinking' || status.value === 'speaking')
const showInterrupt = computed(() => busy.value && state.value === 'connected')
const visibleMessages = computed(() =>
  messages.filter((m) => m.role !== 'system' || m.isError).slice(-6)
)

const statusLabel = computed(() => {
  if (state.value !== 'connected') return '未连接'
  if (status.value === 'thinking') return '思考中'
  if (status.value === 'speaking') return '播报中'
  return '在线'
})

let detach = null

async function connect() {
  try {
    const sid = await startPlay()
    if (sid) setSessionId(sid)
    await unmute()
  } catch (_) {}
}

async function onSend() {
  const t = draft.value.trim()
  if (!t || busy.value) return
  draft.value = ''
  if (state.value !== 'connected') await connect()
  try {
    await sendCommand(t, { speak: true })
  } catch (_) {}
}

async function onMenu(item) {
  if (item.type === 'route') {
    router.push(item.to)
    return
  }
  if (item.type === 'command') {
    if (state.value !== 'connected') await connect()
    try {
      await sendCommand(item.text, { speak: true })
    } catch (_) {}
  }
}

async function onInterrupt() {
  const sid = sessionId.value
  if (!sid) return
  try {
    await avatarApi.interrupt(sid)
  } catch (_) {}
}

watch(state, (s) => {
  if (s === 'connected') scheduleAutoUnmute(500)
})

watch(
  () => messages.length,
  async () => {
    await nextTick()
    const el = chatEl.value
    if (el) el.scrollTop = el.scrollHeight
  }
)

onMounted(() => {
  detach = attachVideo(videoEl)
  if (state.value !== 'connected' && state.value !== 'connecting') {
    setTimeout(connect, 400)
  }
})

onBeforeUnmount(() => {
  if (detach) {
    detach()
    detach = null
  }
})
</script>

<style scoped>
.wx-banner {
  margin: 0;
  padding: 8px 12px;
  font-size: 11px;
  line-height: 1.4;
  color: #576b95;
  background: #ecf5ff;
  border-bottom: 1px solid rgba(7, 193, 96, 0.15);
  text-align: center;
}

.wx-stage {
  flex-shrink: 0;
  padding: 10px 8px 8px;
}

.wx-stage__top,
.wx-stage__bottom {
  display: flex;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}
.wx-stage__bottom {
  margin-bottom: 0;
  margin-top: 8px;
}

.wx-stage__mid {
  display: grid;
  grid-template-columns: 72px 1fr 72px;
  gap: 6px;
  align-items: center;
}

.wx-menu-col {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.wx-menu-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 4px;
  border: 0;
  border-radius: var(--wx-radius);
  background: var(--wx-card);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  color: var(--wx-text);
  font-size: 11px;
  line-height: 1.2;
}
.wx-menu-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.wx-menu-btn__icon {
  font-size: 20px;
  line-height: 1;
}
.wx-menu-btn__label {
  font-weight: 500;
}

.wx-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: 0;
  border-radius: 999px;
  background: var(--wx-card);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  font-size: 12px;
  color: var(--wx-text);
  cursor: pointer;
}
.wx-chip:disabled {
  opacity: 0.5;
}
.wx-chip__icon {
  font-size: 14px;
}

.wx-avatar {
  position: relative;
  width: 100%;
  max-height: 280px;
  border-radius: 12px;
  overflow: hidden;
  background: #1a1a1a;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
}
.wx-avatar__video {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
}
.wx-avatar__mask {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: rgba(247, 247, 247, 0.92);
  font-size: 13px;
  color: var(--wx-text-2);
}
.wx-btn--green {
  padding: 8px 16px;
  border: 0;
  border-radius: 6px;
  background: var(--wx-green);
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}
.wx-avatar__unmute {
  position: absolute;
  left: 50%;
  bottom: 36px;
  transform: translateX(-50%);
  padding: 4px 10px;
  border: 0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  font-size: 11px;
  cursor: pointer;
}
.wx-avatar__badge {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.45);
  color: #fff;
  font-size: 10px;
}

.wx-chat {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.wx-chat__empty {
  margin: auto 0;
  text-align: center;
  font-size: 12px;
  color: var(--wx-text-2);
  line-height: 1.5;
}

.wx-bubble {
  max-width: 88%;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.45;
  word-break: break-word;
}
.wx-bubble.is-user {
  align-self: flex-end;
  background: var(--wx-green);
  color: #fff;
  border-top-right-radius: 2px;
}
.wx-bubble.is-secretary {
  align-self: flex-start;
  background: var(--wx-card);
  color: var(--wx-text);
  border-top-left-radius: 2px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}
.wx-bubble.is-system {
  align-self: center;
  background: #fff3f3;
  color: #cf1322;
  font-size: 12px;
}
.wx-bubble__text {
  margin: 0;
}

.wx-composer {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  padding-bottom: max(8px, env(safe-area-inset-bottom));
  background: #f7f7f7;
  border-top: 1px solid var(--wx-border);
}
.wx-composer__input {
  flex: 1;
  min-width: 0;
  height: 36px;
  padding: 0 12px;
  border: 0;
  border-radius: 6px;
  background: var(--wx-card);
  font-size: 14px;
  color: var(--wx-text);
  outline: none;
}
.wx-composer__input::placeholder {
  color: var(--wx-text-2);
}
.wx-composer__send {
  flex-shrink: 0;
  height: 36px;
  padding: 0 14px;
  border: 0;
  border-radius: 6px;
  background: var(--wx-green);
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}
.wx-composer__send:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.wx-composer__send--warn {
  background: #fa5151;
}
</style>
