<template>
  <PhoneShell>
    <div ref="scrollerRef" class="sm-feed">
      <DouyinSlide
        v-for="(item, index) in feeds"
        :key="item.id"
        :item="item"
        :active="activeIndex === index"
        :busy="status === 'thinking' || status === 'speaking'"
        :reply="activeIndex === index ? lastReply : ''"
        :toast="toast"
        @session="onSession"
        @send="onSend"
        @action="onAction"
      />
    </div>
  </PhoneShell>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import PhoneShell from '../components/douyin/PhoneShell.vue'
import DouyinSlide from '../components/douyin/DouyinSlide.vue'
import { useSecretary } from '../composables/useSecretary'
import { avatarApi } from '../api/meeting'

const router = useRouter()
const { sendCommand, setSessionId, status, messages, sessionId } = useSecretary()

const feeds = ref([
  {
    id: 'live',
    live: true,
    author: '@会议秘书',
    desc: '连接数字人后，可用语音或文字下达订会、查日程、加议程等指令。',
    poster: '',
  },
])

const scrollerRef = ref(null)
const activeIndex = ref(0)
const lastReply = ref('')
const toast = ref('')
let observer = null
let toastTimer = null

function showToast(msg) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 2200)
}

function onSession(sid) {
  if (sid) setSessionId(sid)
}

async function onSend(text) {
  try {
    const result = await sendCommand(text, { speak: true })
    lastReply.value = result?.reply_text || ''
  } catch (e) {
    lastReply.value = ''
    showToast(e?.message || '发送失败')
  }
}

async function onAction(act) {
  if (!act) return
  if (act.type === 'route') {
    router.push(act.to)
    return
  }
  if (act.type === 'interrupt') {
    try {
      await avatarApi.interrupt(sessionId.value)
      showToast('已打断播报')
    } catch (_) {
      showToast('打断失败')
    }
    return
  }
  if (act.type === 'command' && act.text) {
    showToast(`执行：${act.label}`)
    await onSend(act.text)
  }
}

onMounted(() => {
  const root = scrollerRef.value
  if (!root) return
        const slides = root.querySelectorAll('.ai-slide')
  if (slides.length <= 1) {
    activeIndex.value = 0
    return
  }
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && entry.intersectionRatio >= 0.6) {
          const idx = Array.from(slides).indexOf(entry.target)
          if (idx >= 0) activeIndex.value = idx
        }
      })
    },
    { root, threshold: [0.6] }
  )
  slides.forEach((el) => observer.observe(el))

  const last = [...messages].reverse().find((m) => m.role === 'secretary')
  if (last) lastReply.value = last.content
})

watch(
  () => messages.length,
  () => {
    const last = [...messages].reverse().find((m) => m.role === 'secretary')
    if (last?.content) lastReply.value = last.content
  }
)

onBeforeUnmount(() => {
  observer?.disconnect()
  clearTimeout(toastTimer)
})
</script>

<style scoped>
.sm-feed {
  display: block;
}
</style>
