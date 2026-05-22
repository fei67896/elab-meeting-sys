<template>
  <div class="state-hist">
    <div v-if="metaLoading" class="text-muted">加载状态数据…</div>
    <div v-else-if="!meta?.imported" class="card is-flat empty">
      <p class="text-muted">尚未导入老系统状态检测数据。</p>
      <p class="text-tiny text-dim">
        在后端仓库根目录执行：
        <code class="inline-code">.venv/bin/python scripts/import_legacy_detection.py --dir "…/old_data"</code>
      </p>
    </div>
    <template v-else>
      <p v-if="meta.imported_at" class="state-hist__meta text-tiny text-dim">
        数据导入于 {{ formatDateTime(meta.imported_at) }} ·
        行为 {{ meta.counts?.actions?.toLocaleString() }} ·
        专注 {{ meta.counts?.concentration?.toLocaleString() }} ·
        情绪 {{ meta.counts?.emotions?.toLocaleString() }}
      </p>

      <div class="state-hist__layout">
        <aside class="state-hist__meetings card">
          <header class="state-hist__aside-head">
            <h2 class="text-small">检测会议</h2>
            <button class="btn btn-sm btn-ghost" @click="loadSessions">刷新</button>
          </header>
          <p v-if="sessionsLoading" class="text-tiny text-muted">加载中…</p>
          <ul v-else class="meeting-list">
            <li v-for="s in sessions" :key="s.group_id">
              <button
                type="button"
                :class="['meeting-item', { 'is-active': selectedMeetingId === s.group_id }]"
                @click="selectMeeting(s)"
              >
                <span class="meeting-item__id">会议 #{{ s.group_id }}</span>
                <span class="text-tiny text-dim">
                  {{ formatDateTime(s.started_at) }} — {{ formatDateTime(s.ended_at) }}
                </span>
                <span class="text-tiny text-muted">
                  {{ s.student_count }} 人 · {{ s.sample_count?.toLocaleString() }} 采样
                </span>
              </button>
            </li>
          </ul>
        </aside>

        <section v-if="!selectedMeetingId" class="state-hist__detail card is-flat empty">
          <p class="text-muted">← 选择左侧会议，在同一页查看参会人、专注度、情绪与行为</p>
        </section>

        <section v-else class="state-hist__detail card">
          <header class="state-hist__detail-head">
            <div>
              <h2 class="text-small">会议 #{{ selectedMeetingId }}</h2>
              <p v-if="selectedMeeting" class="text-tiny text-dim">
                {{ formatDateTime(selectedMeeting.started_at) }} ~ {{ formatDateTime(selectedMeeting.ended_at) }}
                · {{ participants.length }} 位参会人
              </p>
            </div>
          </header>

          <div v-if="overviewLoading" class="text-muted text-small">加载会议数据…</div>

          <div v-else class="meeting-page">
            <!-- 参会人汇总 -->
            <section class="meeting-block">
              <h3 class="meeting-block__title">参会人</h3>
              <div class="table-wrap">
                <table class="participants-table">
                  <thead>
                    <tr>
                      <th>姓名</th>
                      <th>学号</th>
                      <th>专注均值</th>
                      <th>主导情绪</th>
                      <th>行为记录</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="p in participants" :key="p.student_id">
                      <td>{{ p.display_name }}</td>
                      <td class="text-dim">{{ p.student_no || '—' }}</td>
                      <td>
                        <template v-if="p.concentration?.summary">
                          {{ p.concentration.summary.avg }}
                          <span class="text-tiny text-dim">
                            ({{ p.concentration.summary.min }}–{{ p.concentration.summary.max }})
                          </span>
                        </template>
                        <span v-else class="text-muted">—</span>
                      </td>
                      <td>{{ p.emotion?.dominant ? emotionLabel(p.emotion.dominant) : '—' }}</td>
                      <td class="action-summary">
                        <span
                          v-for="(cnt, key) in p.action?.flag_totals"
                          :key="key"
                          v-show="cnt > 0"
                          class="action-chip"
                        >{{ key }} {{ cnt }}</span>
                        <span
                          v-if="!hasActionFlags(p)"
                          class="text-tiny text-muted"
                        >无异常</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            <!-- 专注度 -->
            <section class="meeting-block">
              <h3 class="meeting-block__title">专注度</h3>
              <div class="metric-grid">
                <article
                  v-for="p in participants"
                  :key="'c-' + p.student_id"
                  class="metric-card"
                >
                  <header class="metric-card__head">
                    <span class="metric-card__name">{{ p.display_name }}</span>
                    <span v-if="p.concentration?.summary" class="text-tiny text-dim">
                      均 {{ p.concentration.summary.avg }}
                    </span>
                  </header>
                  <div class="chart-wrap chart-wrap--sm">
                    <svg
                      v-if="p.concentration?.points?.length"
                      class="line-chart"
                      viewBox="0 0 400 100"
                      preserveAspectRatio="none"
                    >
                      <polyline
                        class="line-chart__stroke"
                        :points="concPolyline(p.concentration.points)"
                      />
                    </svg>
                    <p v-else class="text-muted text-tiny">无数据</p>
                  </div>
                </article>
              </div>
            </section>

            <!-- 情绪 -->
            <section class="meeting-block">
              <h3 class="meeting-block__title">情绪</h3>
              <div class="metric-grid">
                <article
                  v-for="p in participants"
                  :key="'e-' + p.student_id"
                  class="metric-card"
                >
                  <header class="metric-card__head">
                    <span class="metric-card__name">{{ p.display_name }}</span>
                    <span v-if="p.emotion?.dominant" class="text-tiny text-dim">
                      {{ emotionLabel(p.emotion.dominant) }}
                    </span>
                  </header>
                  <div v-if="emoAvgBars(p.emotion?.average).length" class="emo-bars emo-bars--compact">
                    <div v-for="b in emoAvgBars(p.emotion.average)" :key="b.key" class="emo-bar">
                      <span class="emo-bar__label text-tiny">{{ b.label }}</span>
                      <div class="emo-bar__track">
                        <div class="emo-bar__fill" :style="{ width: `${b.pct}%` }"></div>
                      </div>
                    </div>
                  </div>
                  <p v-else class="text-muted text-tiny">无数据</p>
                </article>
              </div>
            </section>

            <!-- 行为 -->
            <section class="meeting-block">
              <h3 class="meeting-block__title">行为</h3>
              <div class="metric-grid metric-grid--flags">
                <article
                  v-for="p in participants"
                  :key="'a-' + p.student_id"
                  class="metric-card metric-card--flags"
                >
                  <span class="metric-card__name">{{ p.display_name }}</span>
                  <div class="stat-row stat-row--wrap">
                    <span
                      v-for="(cnt, key) in p.action?.flag_totals"
                      :key="key"
                      class="action-chip"
                    >{{ key }} {{ cnt }}</span>
                  </div>
                </article>
              </div>
              <h4 class="meeting-block__subtitle">行为时间线</h4>
              <ul v-if="timelineEvents.length" class="action-events">
                <li v-for="(ev, i) in timelineEvents" :key="i">
                  <time class="text-tiny text-dim">{{ formatDateTime(ev.ts) }}</time>
                  <span class="participant-tag">{{ ev.display_name }}</span>
                  <span v-for="f in ev.flags" :key="f" class="tag is-accent">{{ f }}</span>
                </li>
              </ul>
              <p v-else class="text-muted text-small">该会议未记录异常行为</p>
            </section>
          </div>
        </section>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { legacyApi } from '../api/legacy'
import { formatDateTime } from '../utils/format'

const meta = ref(null)
const metaLoading = ref(true)
const sessions = ref([])
const sessionsLoading = ref(false)
const selectedMeetingId = ref(null)
const overviewLoading = ref(false)
const participants = ref([])
const timelineEvents = ref([])

const emotionMap = {
  angry: '愤怒',
  disgusted: '厌恶',
  fearful: '恐惧',
  happy: '开心',
  sad: '悲伤',
  surprised: '惊讶',
  neutral: '平静',
}

const selectedMeeting = computed(() =>
  sessions.value.find((s) => s.group_id === selectedMeetingId.value) || null,
)

const emotionLabel = (k) => emotionMap[k] || k

const hasActionFlags = (p) =>
  Object.values(p.action?.flag_totals || {}).some((n) => n > 0)

const concPolyline = (pts) => {
  if (!pts?.length) return ''
  const vals = pts.map((p) => p.value)
  const min = Math.min(...vals)
  const max = Math.max(...vals)
  const span = max - min || 1
  const w = 400
  const h = 100
  const pad = 6
  return pts
    .map((p, i) => {
      const x = pad + (i / Math.max(pts.length - 1, 1)) * (w - pad * 2)
      const y = h - pad - ((p.value - min) / span) * (h - pad * 2)
      return `${x},${y}`
    })
    .join(' ')
}

const emoAvgBars = (avg) => {
  if (!avg) return []
  const entries = Object.entries(avg).map(([key, val]) => ({
    key,
    label: emotionMap[key] || key,
    val,
  }))
  const max = Math.max(...entries.map((e) => e.val), 0.001)
  return entries
    .sort((a, b) => b.val - a.val)
    .slice(0, 5)
    .map((e) => ({
      ...e,
      pct: Math.round((e.val / max) * 100),
    }))
}

const loadMeta = async () => {
  metaLoading.value = true
  try {
    meta.value = await legacyApi.meta()
  } catch (e) {
    console.warn('[state-history] meta', e)
    meta.value = { imported: false }
  } finally {
    metaLoading.value = false
  }
}

const loadSessions = async () => {
  sessionsLoading.value = true
  try {
    const data = await legacyApi.sessions(80)
    sessions.value = data?.items || []
  } catch (e) {
    console.warn('[state-history] sessions', e)
    sessions.value = []
  } finally {
    sessionsLoading.value = false
  }
}

const selectMeeting = async (s) => {
  selectedMeetingId.value = s.group_id
  overviewLoading.value = true
  participants.value = []
  timelineEvents.value = []
  try {
    const data = await legacyApi.overview(s.group_id)
    participants.value = data?.participants || []
    timelineEvents.value = data?.events || []
  } catch (e) {
    console.warn('[state-history] overview', e)
  } finally {
    overviewLoading.value = false
  }
}

onMounted(async () => {
  await loadMeta()
  if (meta.value?.imported) await loadSessions()
})
</script>

<style scoped>
.state-hist__meta { margin: 0 0 var(--space-4); }
.state-hist__layout {
  display: grid;
  grid-template-columns: minmax(220px, 280px) 1fr;
  gap: var(--space-4);
  align-items: start;
}
@media (max-width: 900px) {
  .state-hist__layout { grid-template-columns: 1fr; }
}
.state-hist__aside-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-3);
}
.state-hist__aside-head h2 { margin: 0; }
.meeting-list {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 520px;
  overflow: auto;
}
.meeting-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  width: 100%;
  padding: var(--space-3);
  border: none;
  border-bottom: 1px solid var(--color-border);
  background: transparent;
  text-align: left;
  cursor: pointer;
  font-family: inherit;
}
.meeting-item:hover { background: var(--color-surface-2); }
.meeting-item.is-active {
  background: var(--color-surface-2);
  border-left: 3px solid var(--color-text);
}
.meeting-item__id { font-weight: 600; font-size: var(--fs-small); }

.state-hist__detail { padding: var(--space-4); min-height: 360px; }
.state-hist__detail-head {
  margin-bottom: var(--space-4);
}

.meeting-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  max-height: calc(100vh - 220px);
  overflow: auto;
  padding-right: var(--space-1);
}
.meeting-block__title {
  margin: 0 0 var(--space-3);
  font-size: var(--fs-small);
  font-weight: 600;
  letter-spacing: 0.02em;
}
.meeting-block__subtitle {
  margin: var(--space-4) 0 var(--space-2);
  font-size: var(--fs-tiny);
  font-weight: 600;
  color: var(--color-text-2);
}

.table-wrap {
  overflow: auto;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
}
.participants-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-small);
}
.participants-table th,
.participants-table td {
  padding: var(--space-2) var(--space-3);
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}
.participants-table th {
  background: var(--color-surface-2);
  font-weight: 600;
  font-size: var(--fs-tiny);
  color: var(--color-text-2);
}
.action-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: var(--space-3);
}
.metric-grid--flags {
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
}
.metric-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: var(--space-3);
  background: var(--color-surface);
}
.metric-card--flags {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.metric-card__head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: var(--space-2);
}
.metric-card__name {
  font-weight: 600;
  font-size: var(--fs-small);
}

.stat-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  font-size: var(--fs-tiny);
}
.chart-wrap {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--space-2);
  background: var(--color-bg);
}
.chart-wrap--sm .line-chart { height: 90px; }
.line-chart {
  width: 100%;
  height: 140px;
}
.line-chart__stroke {
  fill: none;
  stroke: var(--color-accent);
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.emo-bars { display: flex; flex-direction: column; gap: 4px; }
.emo-bars--compact .emo-bar {
  grid-template-columns: 48px 1fr;
}
.emo-bar {
  display: grid;
  grid-template-columns: 56px 1fr 40px;
  align-items: center;
  gap: var(--space-2);
}
.emo-bar__track {
  height: 6px;
  background: var(--color-surface-2);
  border-radius: 4px;
  overflow: hidden;
}
.emo-bar__fill {
  height: 100%;
  background: var(--color-text);
  border-radius: 4px;
}

.action-chip {
  padding: 2px 8px;
  background: var(--color-surface-2);
  border-radius: var(--radius-sm);
  font-size: var(--fs-tiny);
}
.participant-tag {
  font-size: var(--fs-tiny);
  font-weight: 600;
  padding: 0 6px;
  background: var(--color-surface-2);
  border-radius: var(--radius-sm);
}
.action-events {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 240px;
  overflow: auto;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
}
.action-events li {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--color-border);
  font-size: var(--fs-small);
}
.empty { padding: var(--space-6); text-align: center; }
.inline-code {
  display: block;
  margin-top: var(--space-2);
  padding: var(--space-2);
  background: var(--color-surface-2);
  border-radius: var(--radius-sm);
  font-size: var(--fs-tiny);
  word-break: break-all;
}
</style>
