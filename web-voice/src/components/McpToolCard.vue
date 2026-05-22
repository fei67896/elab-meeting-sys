<template>
  <article
    class="mcp-card"
    :class="`mcp-card--${card.status || 'idle'}`"
  >
    <header class="mcp-card__head">
      <span class="mcp-card__dot" aria-hidden="true" />
      <h3 class="mcp-card__title">{{ card.title }}</h3>
    </header>
    <p v-if="card.status === 'idle' && !hasLines" class="mcp-card__hint">
      {{ card.description }}
    </p>
    <ul v-else class="mcp-card__lines">
      <li v-for="(line, i) in displayLines" :key="i">{{ line }}</li>
    </ul>
    <p v-if="card.tool && card.status !== 'idle'" class="mcp-card__tool">
      {{ toolLabel }}
    </p>
  </article>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  card: { type: Object, required: true },
})

const TOOL_LABELS = {
  create_meeting: '创建会议',
  add_regular_meeting: '添加例会',
  add_agenda: '添加议程',
  add_participant: '添加参会人',
  set_attendance: '出席登记',
  cancel_meeting: '取消会议',
  list_command_history: '指令历史',
  list_meetings: '列表查询',
  get_meeting: '会议详情',
}

const hasLines = computed(() => (props.card.lines || []).length > 0)

const displayLines = computed(() => {
  if (props.card.status === 'running') {
    return props.card.lines?.length ? props.card.lines : ['处理中…']
  }
  return props.card.lines || []
})

const toolLabel = computed(() => TOOL_LABELS[props.card.tool] || props.card.tool)
</script>

<style scoped>
.mcp-card {
  padding: var(--space-3);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-1);
  transition: border-color var(--dur-fast) var(--ease), box-shadow var(--dur-fast) var(--ease);
}

.mcp-card--success {
  border-color: rgba(22, 163, 74, 0.35);
  box-shadow: 0 0 0 1px rgba(22, 163, 74, 0.08);
}
.mcp-card--error {
  border-color: rgba(220, 38, 38, 0.4);
  background: rgba(254, 242, 242, 0.96);
}
.mcp-card--running,
.mcp-card--running.mcp-card--idle,
.mcp-card--running.mcp-card--running {
  border-color: rgba(37, 99, 235, 0.35);
}

.mcp-card__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: var(--space-2);
}
.mcp-card__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-text-3);
  flex-shrink: 0;
}
.mcp-card--success .mcp-card__dot {
  background: #16a34a;
}
.mcp-card--error .mcp-card__dot {
  background: #dc2626;
}
.mcp-card--running .mcp-card__dot,
.mcp-card--running .mcp-card__dot {
  background: #2563eb;
  animation: mcp-pulse 1s ease-in-out infinite;
}

.mcp-card__title {
  margin: 0;
  font-size: var(--fs-small);
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.3;
}

.mcp-card__hint {
  margin: 0;
  font-size: var(--fs-tiny);
  color: var(--color-text-3);
  line-height: 1.45;
}

.mcp-card__lines {
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: var(--fs-tiny);
  color: var(--color-text-2);
  line-height: 1.5;
}
.mcp-card__lines li + li {
  margin-top: 4px;
}

.mcp-card__tool {
  margin: var(--space-2) 0 0;
  font-size: 11px;
  color: var(--color-text-3);
}

@keyframes mcp-pulse {
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.15);
  }
}
</style>
