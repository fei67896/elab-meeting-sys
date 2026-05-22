<template>
  <div class="history">
    <div class="container">
      <header class="page-head">
        <div>
          <h1 class="page-title">历史查询</h1>
          <p class="page-sub">秘书指令记录与老系统参会状态检测数据。</p>
        </div>
      </header>

      <nav class="history-tabs" aria-label="历史类型">
        <button
          type="button"
          :class="['history-tabs__btn', { 'is-active': tab === 'commands' }]"
          @click="tab = 'commands'"
        >秘书指令</button>
        <button
          type="button"
          :class="['history-tabs__btn', { 'is-active': tab === 'state' }]"
          @click="tab = 'state'"
        >参会状态</button>
      </nav>

      <section v-show="tab === 'commands'">
        <div class="section-toolbar">
          <button class="btn btn-sm" @click="refresh">刷新</button>
        </div>
        <section v-if="loading" class="text-muted">加载中…</section>
        <section v-else-if="items.length === 0" class="card is-flat empty">
          <p class="text-muted">还没有任何指令历史。</p>
        </section>
        <ol v-else class="timeline">
          <li v-for="row in items" :key="row.id" class="timeline__item">
            <div class="timeline__dot" :class="dotClass(row.intent)"></div>
            <article class="timeline__card card">
              <header class="timeline__head">
                <span class="tag is-primary">{{ row.intent || 'unknown' }}</span>
                <time class="text-tiny text-dim">{{ formatDateTime(row.ts) }}</time>
              </header>
              <p class="timeline__user">
                <span class="text-tiny text-muted">用户：</span>
                {{ row.user_input }}
              </p>
              <p v-if="row.reply_text" class="timeline__reply">
                <span class="text-tiny text-muted">秘书：</span>
                {{ row.reply_text }}
              </p>
              <details v-if="row.params || row.result" class="timeline__details">
                <summary class="text-tiny">查看解析与结果</summary>
                <div class="grid">
                  <div>
                    <h5 class="text-tiny text-muted">解析参数</h5>
                    <pre class="code">{{ pretty(row.params) }}</pre>
                  </div>
                  <div>
                    <h5 class="text-tiny text-muted">执行结果</h5>
                    <pre class="code">{{ pretty(row.result) }}</pre>
                  </div>
                </div>
              </details>
            </article>
          </li>
        </ol>
      </section>

      <StateHistoryPanel v-show="tab === 'state'" />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { secretaryApi } from '../api/meeting'
import { formatDateTime } from '../utils/format'
import StateHistoryPanel from '../components/StateHistoryPanel.vue'

const tab = ref('state')
const items = ref([])
const loading = ref(true)

const refresh = async () => {
  loading.value = true
  try {
    const data = await secretaryApi.history(100)
    items.value = data?.items || []
  } catch (err) {
    console.warn('[history] 加载失败', err)
    items.value = []
  } finally {
    loading.value = false
  }
}

const pretty = (v) => (v == null ? '(空)' : JSON.stringify(v, null, 2))

const dotClass = (intent) => {
  if (!intent) return ''
  if (intent.startsWith('create')) return 'is-primary'
  if (intent.startsWith('cancel') || intent === 'error') return 'is-danger'
  if (intent === 'chitchat') return 'is-dim'
  return ''
}

watch(tab, (t) => {
  if (t === 'commands' && !items.value.length) refresh()
})

onMounted(() => {
  if (tab.value === 'commands') refresh()
})
</script>

<style scoped>
.history { padding: var(--space-5) 0 var(--space-7); }
.page-head {
  margin-bottom: var(--space-4);
}
.page-title {
  font-family: var(--font-serif);
  font-size: var(--fs-h1);
  margin: 0 0 4px;
}
.page-sub { margin: 0; color: var(--color-text-2); font-size: var(--fs-small); }

.history-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--space-5);
}
.history-tabs__btn {
  padding: 10px 20px;
  border: none;
  background: transparent;
  font-size: var(--fs-body);
  color: var(--color-text-2);
  cursor: pointer;
  position: relative;
}
.history-tabs__btn.is-active {
  color: var(--color-text);
  font-weight: 600;
}
.history-tabs__btn.is-active::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: -1px;
  height: 2px;
  background: var(--color-text);
}

.section-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: var(--space-4);
}
.empty { padding: var(--space-7); text-align: center; }

.timeline {
  list-style: none;
  margin: 0;
  padding: 0 0 0 18px;
  border-left: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.timeline__item { position: relative; }
.timeline__dot {
  position: absolute;
  left: -23px;
  top: 12px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-bg);
}
.timeline__dot.is-danger { background: var(--color-danger); }
.timeline__dot.is-primary { background: var(--color-primary); }
.timeline__dot.is-dim { background: var(--color-text-3); }

.timeline__card { padding: var(--space-4); }
.timeline__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-2);
}
.timeline__user, .timeline__reply { margin: 0 0 4px; }
.timeline__user { font-weight: 500; }
.timeline__reply { color: var(--color-text-2); }

.timeline__details {
  margin-top: var(--space-3);
  border-top: 1px dashed var(--color-border);
  padding-top: var(--space-3);
}
.timeline__details summary {
  cursor: pointer;
  color: var(--color-text-2);
}
.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
  margin-top: var(--space-2);
}
@media (max-width: 720px) {
  .grid { grid-template-columns: 1fr; }
}
.code {
  margin: 4px 0 0;
  padding: var(--space-3);
  background: var(--color-surface-2);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: var(--fs-tiny);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow: auto;
}
</style>
