<template>
  <VoiceLiveRoom
    ref="liveRoomRef"
    :messages="messages"
    :status="status"
    :listening="listening"
    :busy="micBusy"
    :avatar-ready="avatarReady"
    :level="micLevel"
    :live-text="liveText"
    :mic-error="micError"
    @session="onSession"
    @toggle-mic="toggleMic"
    @interrupt="onInterrupt"
    @logout="onLogout"
  />
</template>

<script setup>
import { computed, watch, onMounted, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import VoiceLiveRoom from '../components/VoiceLiveRoom.vue'
import { useScheduledMeetings } from '../composables/useScheduledMeetings'
import { useAuth } from '@shared/composables/useAuth'
import { useSecretary } from '@shared/composables/useSecretary'
import { useWebRTC } from '@shared/composables/useWebRTC'
import { useRecorder } from '@shared/composables/useRecorder'
import { useSpeechRecognition } from '@shared/composables/useSpeechRecognition'
import { useMicLevel } from '@shared/composables/useMicLevel'
import { canUseBrowserSpeech } from '@shared/utils/speech'
import { avatarApi } from '@shared/api/meeting'

const router = useRouter()
const { logout } = useAuth()
const { messages, status, lastResult, sendCommand, setSessionId } = useSecretary()
const { sessionId, connectionState } = useWebRTC()
const liveRoomRef = ref(null)
const { loadScheduledMeetings } = useScheduledMeetings()

const browserAsr = canUseBrowserSpeech()
const recorder = useRecorder()
const speech = useSpeechRecognition({ language: 'zh-CN', continuous: false })
const { level: micLevel, start: startLevel, stop: stopLevel, errorMsg: levelError } = useMicLevel()

const avatarReady = computed(() => connectionState.value === 'connected')
const listening = computed(() =>
  browserAsr ? speech.isRecording.value : recorder.isRecording.value
)
const micBusy = computed(() =>
  status.value === 'thinking' || status.value === 'speaking' || recorder.isUploading.value
)
const liveText = computed(() =>
  listening.value ? (browserAsr ? speech.transcript.value : '') : ''
)
const micError = computed(() => levelError.value || recorder.errorMsg.value || '')

function onSession(sid) {
  if (sid) setSessionId(sid)
}

async function onSendText(text) {
  const t = (text || '').trim()
  if (!t || micBusy.value) return
  try {
    await sendCommand(t, { speak: true })
  } catch (_) {}
}

const MEETING_INTENTS = new Set([
  'create_meeting',
  'add_regular_meeting',
  'cancel_meeting',
  'add_agenda',
  'add_participant',
  'set_attendance',
])

watch(lastResult, (r) => {
  if (!r) return
  if (MEETING_INTENTS.has(r.intent)) {
    loadScheduledMeetings()
    liveRoomRef.value?.refreshSidebars?.()
  }
})

async function finishListeningAndSend() {
  let text = ''
  if (browserAsr) {
    speech.stop()
    text = (speech.transcript.value || '').trim()
    speech.reset()
  } else {
    text = (await recorder.stop()) || ''
  }
  if (text) await onSendText(text)
}

async function toggleMic() {
  if (micBusy.value || !avatarReady.value) return
  if (listening.value) {
    await finishListeningAndSend()
    return
  }
  if (browserAsr) {
    speech.reset()
    speech.start()
  } else {
    await recorder.start()
  }
}

async function onInterrupt() {
  const sid = sessionId.value
  if (!sid) return
  try {
    await avatarApi.interrupt(sid)
  } catch (_) {}
}

const onLogout = async () => {
  await logout()
  router.replace({ name: 'login' })
}

watch(status, (s) => {
  if ((s === 'speaking' || s === 'thinking') && listening.value) {
    if (browserAsr) speech.stop()
    else if (recorder.isRecording.value) recorder.stop().catch(() => {})
  }
})

onMounted(() => {
  startLevel().catch(() => {})
})

onBeforeUnmount(() => {
  stopLevel()
  if (browserAsr && speech.isRecording.value) speech.stop()
})
</script>
