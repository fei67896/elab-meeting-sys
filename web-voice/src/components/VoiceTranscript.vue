<template>
  <div class="transcript" ref="scrollEl">
    <div v-if="!messages.length" class="transcript__empty">
      <p class="transcript__empty-title">开始对话</p>
      <p class="text-small text-muted">
        点击下方麦克风说话，例如：「帮我约明天下午三点的项目评审会」
      </p>
    </div>
    <article
      v-for="m in messages"
      :key="m.id"
      class="transcript__row"
      :class="`is-${m.role}`"
    >
      <span class="transcript__role">{{ roleLabel(m.role) }}</span>
      <div class="transcript__bubble">
        <p class="transcript__text">{{ m.content || '…' }}</p>
        <time class="transcript__time text-tiny text-muted mono">{{ formatTs(m.ts) }}</time>
      </div>
    </article>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  messages: { type: Array, default: () => [] },
})

const scrollEl = ref(null)

function roleLabel(role) {
  if (role === 'user') return '你'
  if (role === 'secretary') return '秘书'
  return '系统'
}

function formatTs(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

watch(
  () => props.messages.length,
  async () => {
    await nextTick()
    const el = scrollEl.value
    if (el) el.scrollTop = el.scrollHeight
  }
)
</script>

<style scoped>
.transcript {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.transcript__empty {
  margin: auto 0;
  text-align: center;
  padding: var(--space-6) var(--space-4);
}
.transcript__empty-title {
  font-size: var(--fs-h3);
  font-weight: 600;
  margin: 0 0 var(--space-2);
}
.transcript__row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 92%;
}
.transcript__row.is-user {
  align-self: flex-end;
  align-items: flex-end;
}
.transcript__row.is-secretary,
.transcript__row.is-system {
  align-self: flex-start;
  align-items: flex-start;
}
.transcript__role {
  font-size: var(--fs-tiny);
  font-weight: 600;
  color: var(--color-text-3);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.transcript__bubble {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
}
.is-user .transcript__bubble {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-text-inverse);
}
.is-user .transcript__time { color: rgba(250, 250, 250, 0.65); }
.is-system .transcript__bubble {
  border-color: var(--color-danger-soft);
  background: var(--color-danger-soft);
}
.transcript__text {
  margin: 0 0 var(--space-2);
  white-space: pre-wrap;
  word-break: break-word;
  line-height: var(--lh-body);
}
.transcript__time { display: block; }
</style>
