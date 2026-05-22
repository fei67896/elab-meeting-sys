<template>
  <aside class="focus-strip" aria-label="会议专注度历史">
    <header class="focus-strip__head">
      <h2 class="focus-strip__title">专注度</h2>
      <button type="button" class="focus-strip__refresh" title="刷新" @click="loadFocusHistory()">
        ↻
      </button>
    </header>
    <p v-if="loading" class="focus-strip__hint">加载中…</p>
    <p v-else-if="!items.length" class="focus-strip__hint">暂无检测会议数据</p>
    <ul v-else class="focus-strip__list hidden-scroll">
      <li v-for="card in items" :key="card.groupId">
        <article class="focus-card">
          <header class="focus-card__head">
            <span class="focus-card__id">会议 #{{ card.groupId }}</span>
            <span v-if="card.meanFocus != null" class="focus-card__avg">均 {{ card.meanFocus }}</span>
          </header>
          <p class="focus-card__meta text-tiny">
            {{ formatRange(card.startedAt, card.endedAt) }}
            · {{ card.studentCount }} 人
          </p>
          <div class="focus-card__chart">
            <svg
              v-if="card.points.length"
              class="focus-card__svg"
              viewBox="0 0 400 72"
              preserveAspectRatio="none"
            >
              <polyline
                class="focus-card__line"
                :points="polyline(card.points, 400, 72)"
              />
            </svg>
            <p v-else class="focus-strip__hint">无曲线数据</p>
          </div>
        </article>
      </li>
    </ul>
    <a
      class="focus-strip__more"
      :href="historyUrl"
      target="_blank"
      rel="noopener noreferrer"
    >
      在历史查询查看全部 →
    </a>
  </aside>
</template>

<script setup>
import { onMounted } from 'vue'
import { useFocusHistory } from '../composables/useFocusHistory'
import { concPolyline } from '../utils/chart'

const MEETING_ORIGIN = import.meta.env.VITE_MEETING_ORIGIN || 'https://localhost:3000'
const historyUrl = `${MEETING_ORIGIN}/#/history`

const { items, loading, loadFocusHistory, ensureLoaded } = useFocusHistory()

defineExpose({ refresh: loadFocusHistory })

const polyline = (pts, w, h) => concPolyline(pts, w, h)

function pad(n) {
  return String(n).padStart(2, '0')
}

function formatRange(start, end) {
  const fmt = (iso) => {
    if (!iso) return '—'
    const d = new Date(iso.replace(' ', 'T'))
    if (Number.isNaN(d.getTime())) return String(iso).slice(0, 10)
    return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  }
  return `${fmt(start)} — ${fmt(end)}`
}

onMounted(() => ensureLoaded())
</script>

<style scoped>
@import '../styles/hidden-scroll.css';

.focus-strip {
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

.focus-strip__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-2);
  flex-shrink: 0;
}

.focus-strip__title {
  margin: 0;
  font-size: var(--fs-small);
  font-weight: 600;
}

.focus-strip__refresh {
  border: 0;
  background: transparent;
  color: var(--color-text-3);
  cursor: pointer;
  font-size: 16px;
  padding: 4px;
  border-radius: var(--radius-sm);
}
.focus-strip__refresh:hover {
  color: var(--color-text);
  background: var(--color-surface-2);
}

.focus-strip__hint {
  margin: 0;
  font-size: var(--fs-tiny);
  color: var(--color-text-3);
}

.focus-strip__list {
  list-style: none;
  margin: 0;
  padding: 0;
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.focus-strip__more {
  flex-shrink: 0;
  margin-top: var(--space-2);
  font-size: 11px;
  color: var(--color-text-3);
  text-decoration: none;
}
.focus-strip__more:hover {
  color: var(--color-accent);
}

.focus-card {
  padding: var(--space-2);
  border-radius: var(--radius);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
}

.focus-card__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 6px;
}

.focus-card__id {
  font-size: var(--fs-tiny);
  font-weight: 600;
  color: var(--color-text);
}

.focus-card__avg {
  font-size: 11px;
  color: #2563eb;
  font-weight: 600;
}

.focus-card__meta {
  margin: 4px 0 6px;
  font-size: 10px;
  color: var(--color-text-3);
  line-height: 1.35;
}

.focus-card__chart {
  height: 56px;
  border-radius: var(--radius-sm);
  background: linear-gradient(180deg, rgba(37, 99, 235, 0.06) 0%, transparent 100%);
  overflow: hidden;
}

.focus-card__svg {
  display: block;
  width: 100%;
  height: 100%;
}

.focus-card__line {
  fill: none;
  stroke: #2563eb;
  stroke-width: 2.5;
  vector-effect: non-scaling-stroke;
}

</style>
