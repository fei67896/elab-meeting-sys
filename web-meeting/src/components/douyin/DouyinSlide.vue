<template>
  <section class="ai-slide feed-light" :class="{ 'is-active': active }">
    <nav class="ai-segmented" aria-label="导航">
      <button
        type="button"
        class="ai-segmented__btn"
        :class="{ 'is-active': topTab === 'secretary' }"
        @click="topTab = 'secretary'"
      >
        秘书
      </button>
      <button type="button" class="ai-segmented__btn" @click="onTabMeetings">会议</button>
      <button type="button" class="ai-segmented__btn" @click="onTabMine">我的</button>
    </nav>

    <div class="ai-slide__video">
      <DouyinAvatarVideo
        v-if="item.live"
        :active="active"
        @session="$emit('session', $event)"
      />
      <div
        v-else
        class="ai-slide__poster"
        :style="{ backgroundImage: `url(${item.poster})` }"
      />
      <span v-if="busy" class="ai-slide__pill">
        <span class="ai-status-dot" aria-hidden="true"></span>
        思考中
      </span>
    </div>

    <div class="ai-slide__copy">
      <p class="ai-slide__name">{{ item.author }}</p>
      <p class="ai-inset">{{ item.desc }}</p>
      <p v-if="reply" class="ai-callout">{{ reply }}</p>
    </div>

    <SecretaryActionRail
      v-if="item.live && active"
      :busy="busy"
      @action="$emit('action', $event)"
    />

    <form v-if="active && item.live" class="ai-slide__bar" @submit.prevent="onSend">
      <input
        v-model="draft"
        class="input ai-slide__input"
        placeholder="对秘书说点什么…"
        :disabled="busy"
      />
      <button
        type="button"
        class="btn btn-sm"
        :class="{ 'is-active': recording }"
        :disabled="busy"
        @click="toggleRecord"
      >
        {{ recording ? '停止' : '语音' }}
      </button>
      <button type="submit" class="btn btn-sm btn-primary" :disabled="!draft.trim() || busy">
        发送
      </button>
    </form>

    <p v-if="toast" class="ai-slide__toast" role="status">{{ toast }}</p>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import DouyinAvatarVideo from './DouyinAvatarVideo.vue'
import SecretaryActionRail from './SecretaryActionRail.vue'
import { useRecorder } from '../../composables/useRecorder'
import { useSpeechRecognition } from '../../composables/useSpeechRecognition'
import { canUseBrowserSpeech } from '../../utils/speech'

defineProps({
  item: { type: Object, required: true },
  active: { type: Boolean, default: false },
  busy: { type: Boolean, default: false },
  reply: { type: String, default: '' },
  toast: { type: String, default: '' },
})

const emit = defineEmits(['session', 'send', 'action'])

const router = useRouter()
const topTab = ref('secretary')
const draft = ref('')
const recorder = useRecorder()
const speech = useSpeechRecognition({ language: 'zh-CN', continuous: false })
const browserAsr = computed(() => canUseBrowserSpeech())
const recording = computed(() =>
  browserAsr.value ? speech.isRecording.value : recorder.isRecording.value
)

function onTabMeetings() {
  router.push('/meetings')
}

function onTabMine() {
  router.push('/settings')
}

function appendDraft(text) {
  const t = (text || '').trim()
  if (!t) return
  draft.value = draft.value ? `${draft.value} ${t}` : t
}

async function toggleRecord() {
  if (browserAsr.value) {
    if (speech.isRecording.value) {
      speech.stop()
      appendDraft(speech.transcript.value)
      speech.reset()
    } else {
      speech.reset()
      speech.start()
    }
    return
  }
  if (recorder.isRecording.value) {
    const text = await recorder.stop()
    appendDraft(text)
  } else {
    await recorder.start()
  }
}

function onSend() {
  const text = draft.value.trim()
  if (!text) return
  draft.value = ''
  emit('send', text)
}
</script>

<style src="./feed-light.css"></style>

<style scoped>
.ai-slide {
  display: flex;
  flex-direction: column;
  min-height: min(640px, calc(100dvh - 140px));
  background: var(--color-bg);
}

.ai-slide__video {
  position: relative;
  margin: var(--space-4) auto;
  border-radius: var(--radius);
  overflow: hidden;
  background: #0a0a0a;
  width: calc(100% - var(--space-8));
  max-width: 420px;
  max-height: min(72vh, 720px);
  aspect-ratio: var(--avatar-aspect);
  border: 1px solid var(--color-border);
}
.ai-slide__poster {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center;
}
.ai-slide__pill {
  position: absolute;
  top: var(--space-3);
  right: var(--space-3);
  z-index: 5;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  background: rgba(10, 10, 10, 0.6);
  backdrop-filter: blur(8px);
  color: #fff;
  font-size: var(--fs-tiny);
  font-weight: 500;
}
.ai-slide__pill .ai-status-dot {
  background: #fff;
}
.ai-slide__pill .ai-status-dot::after {
  border-color: #fff;
}

.ai-slide__copy {
  padding: 0 var(--space-4);
}
.ai-slide__name {
  margin: 0 0 var(--space-2);
  font-size: var(--fs-h4);
  font-weight: 600;
  color: var(--color-text);
  letter-spacing: -0.01em;
}

.ai-slide__bar {
  display: flex;
  gap: var(--space-2);
  align-items: center;
  margin-top: auto;
  padding: var(--space-3) var(--space-4) var(--space-4);
  background: var(--color-surface);
  border-top: 1px solid var(--color-border);
}
.ai-slide__input {
  flex: 1;
  min-width: 0;
  margin: 0;
}
.ai-slide__bar .btn.is-active {
  background: var(--color-danger);
  border-color: var(--color-danger);
  color: #fff;
}

.ai-slide__toast {
  position: fixed;
  left: 50%;
  bottom: max(24px, env(safe-area-inset-bottom));
  transform: translateX(-50%);
  z-index: 200;
  margin: 0;
  padding: 10px 18px;
  border-radius: var(--radius-pill);
  background: var(--color-text);
  color: var(--color-text-inverse);
  font-size: var(--fs-small);
  font-weight: 500;
  box-shadow: var(--shadow-2);
  animation: ai-toast 2.2s ease forwards;
}
@keyframes ai-toast {
  0%, 72% { opacity: 1; }
  100% { opacity: 0; }
}

:deep(.dy-video) {
  position: absolute;
  inset: 0;
  width: 100%;
  height: auto;
  max-height: none;
  margin: 0;
}
:deep(.dy-video__el) {
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
}
:deep(.dy-video__mask) {
  background: rgba(10, 10, 10, 0.7);
}
:deep(.dy-video__connect) {
  border-radius: var(--radius);
  padding: 10px 22px;
  font-weight: 500;
  background: #fff;
  border: none;
  color: var(--color-text);
}
:deep(.dy-video__unmute) {
  bottom: var(--space-4);
  border-radius: var(--radius-pill);
  background: rgba(255, 255, 255, 0.92);
  border: 0;
  color: var(--color-text);
  font-size: var(--fs-tiny);
  font-weight: 500;
  padding: 6px 12px;
}
</style>
