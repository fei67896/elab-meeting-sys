<template>
  <div class="danmu" ref="scrollEl">
    <div
      v-for="m in lines"
      :key="m.id"
      class="danmu__line"
      :class="`is-${m.role}`"
    >
      <span class="danmu__name">{{ roleName(m.role) }}</span>
      <span class="danmu__text">{{ m.content || '…' }}</span>
    </div>
    <p v-if="liveText" class="danmu__live">
      <span class="danmu__name">你</span>
      <span class="danmu__text danmu__text--live">{{ liveText }}</span>
    </p>
    <p v-if="statusHint" class="danmu__status">{{ statusHint }}</p>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  status: { type: String, default: 'idle' },
  liveText: { type: String, default: '' },
  maxLines: { type: Number, default: 8 },
})

const scrollEl = ref(null)

const lines = computed(() => {
  const list = props.messages.filter((m) => m.role !== 'system' || m.isError)
  return list.slice(-props.maxLines)
})

const statusHint = computed(() => {
  if (props.status === 'thinking') return '秘书正在思考…'
  return ''
})

function roleName(role) {
  if (role === 'user') return '你'
  if (role === 'secretary') return '秘书'
  return '系统'
}

watch(
  () => [props.messages.length, props.liveText, props.status],
  async () => {
    await nextTick()
    const el = scrollEl.value
    if (el) el.scrollTop = el.scrollHeight
  }
)
</script>

<style scoped>
.danmu {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  gap: 10px;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 4px;
  padding-top: 24px;
  scrollbar-width: none;
}
.danmu::-webkit-scrollbar { display: none; }

.danmu__line,
.danmu__live {
  margin: 0;
  font-size: 14px;
  line-height: 1.45;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.55);
  word-break: break-word;
}
.danmu__name {
  font-weight: 700;
  margin-right: 6px;
}
.danmu__line.is-user .danmu__name { color: #a5f3fc; }
.danmu__line.is-secretary .danmu__name { color: #fde68a; }
.danmu__line.is-system .danmu__name { color: #fca5a5; }
.danmu__text {
  color: rgba(255, 255, 255, 0.95);
}
.danmu__line.is-secretary .danmu__text {
  color: #fff;
  font-weight: 500;
}
.danmu__text--live {
  font-style: italic;
  opacity: 0.9;
}
.danmu__status {
  margin: 4px 0 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.75);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}
</style>
