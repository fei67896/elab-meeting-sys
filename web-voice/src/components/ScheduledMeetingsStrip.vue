<template>
  <aside class="meet-strip" aria-label="已定会议">
    <header class="meet-strip__head">
      <h2 class="meet-strip__title">已定会议</h2>
      <button type="button" class="meet-strip__refresh" title="刷新" @click="loadScheduledMeetings()">
        ↻
      </button>
    </header>
    <p v-if="loading" class="meet-strip__hint">加载中…</p>
    <p v-else-if="!meetings.length" class="meet-strip__hint">暂无已排期会议</p>
    <ul v-else class="meet-strip__list hidden-scroll">
      <li v-for="m in meetings" :key="m.id">
        <a
          class="meet-strip__item"
          :href="meetingLink(m.id)"
          target="_blank"
          rel="noopener noreferrer"
        >
          <span class="meet-strip__time">{{ formatTime(m.start_time) }}</span>
          <span class="meet-strip__date">{{ formatDateShort(m.start_time) }}</span>
          <span class="meet-strip__name">{{ m.title }}</span>
          <span class="meet-strip__tag" :class="`is-${m.status}`">{{ statusLabel(m.status) }}</span>
        </a>
      </li>
    </ul>
    <a
      class="meet-strip__more"
      :href="meetingsHomeUrl"
      target="_blank"
      rel="noopener noreferrer"
    >
      在会议台查看全部 →
    </a>
  </aside>
</template>

<script setup>
import { onMounted } from 'vue'
import { useScheduledMeetings } from '../composables/useScheduledMeetings'

const MEETING_ORIGIN = import.meta.env.VITE_MEETING_ORIGIN || 'https://localhost:3000'

const { meetings, loading, loadScheduledMeetings, ensureLoaded } = useScheduledMeetings()

defineExpose({ refresh: loadScheduledMeetings })

const meetingsHomeUrl = `${MEETING_ORIGIN}/meetings`
const meetingLink = (id) => `${MEETING_ORIGIN}/meetings/${id}`

function pad(n) {
  return String(n).padStart(2, '0')
}

function formatTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function formatDateShort(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

const statusLabel = (s) =>
  ({ scheduled: '已排期', ongoing: '进行中', completed: '已完成', cancelled: '已取消' }[s] || s)

onMounted(() => ensureLoaded())
</script>

<style scoped>
@import '../styles/hidden-scroll.css';

.meet-strip {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: min(78dvh, 720px);
  min-height: 280px;
  padding: var(--space-3);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-1);
}

.meet-strip__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
  flex-shrink: 0;
}

.meet-strip__title {
  margin: 0;
  font-size: var(--fs-small);
  font-weight: 600;
  color: var(--color-text);
}

.meet-strip__refresh {
  border: 0;
  background: transparent;
  color: var(--color-text-3);
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  padding: 4px;
  border-radius: var(--radius-sm);
}
.meet-strip__refresh:hover {
  color: var(--color-text);
  background: var(--color-surface-2);
}

.meet-strip__hint {
  margin: 0;
  font-size: var(--fs-tiny);
  color: var(--color-text-3);
}

.meet-strip__list {
  list-style: none;
  margin: 0;
  padding: 0;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.meet-strip__item {
  display: grid;
  grid-template-columns: 42px 1fr;
  grid-template-rows: auto auto auto;
  gap: 2px 8px;
  padding: 10px;
  border-radius: var(--radius);
  text-decoration: none;
  color: inherit;
  background: var(--color-surface);
  border: 1px solid transparent;
  transition: border-color var(--dur-fast) var(--ease), background var(--dur-fast) var(--ease);
}
.meet-strip__item:hover {
  border-color: var(--color-border);
  background: var(--color-surface-2);
}

.meet-strip__time {
  grid-row: 1 / 3;
  grid-column: 1;
  align-self: center;
  font-size: var(--fs-small);
  font-weight: 700;
  color: var(--color-accent);
  font-variant-numeric: tabular-nums;
}

.meet-strip__date {
  grid-column: 2;
  font-size: 11px;
  color: var(--color-text-3);
}

.meet-strip__name {
  grid-column: 2;
  font-size: var(--fs-tiny);
  font-weight: 600;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meet-strip__tag {
  grid-column: 2;
  justify-self: start;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: var(--radius-pill);
  background: var(--color-surface-2);
  color: var(--color-text-3);
}
.meet-strip__tag.is-scheduled {
  background: rgba(37, 99, 235, 0.1);
  color: #2563eb;
}
.meet-strip__tag.is-ongoing {
  background: rgba(22, 163, 74, 0.12);
  color: #16a34a;
}

.meet-strip__more {
  flex-shrink: 0;
  margin-top: var(--space-2);
  font-size: 11px;
  color: var(--color-text-3);
  text-decoration: none;
}
.meet-strip__more:hover {
  color: var(--color-accent);
}
</style>
