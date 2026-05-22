<template>
  <div class="workbench">
    <div class="workbench__inner">
      <header class="workbench__intro">
        <p class="ai-eyebrow workbench__eyebrow">Workspace</p>
        <h1 class="ai-large-title workbench__h1">工作台</h1>
        <p class="workbench__lead">
          自然语言下达指令，AI 自动规划会议、议程与参会人，由数字人实时播报反馈。
        </p>
      </header>

      <div class="workbench__grid">
        <main class="workbench__main">
          <SecretaryChat />
          <CommandResultCard :result="lastResult" />
        </main>

        <aside class="workbench__aside">
          <AvatarWindow @session="onSession" />
          <section class="card">
            <header class="aside-head">
              <h3 class="aside-title">今日会议</h3>
              <router-link to="/meetings" class="text-tiny">查看全部 →</router-link>
            </header>
            <div v-if="loading" class="text-small text-muted">加载中…</div>
            <ul v-else-if="today.length" class="aside-list">
              <li v-for="m in today" :key="m.id">
                <router-link :to="`/meetings/${m.id}`" class="aside-item">
                  <span class="aside-item__time mono">{{ formatTime(m.start_time) }}</span>
                  <span class="aside-item__title">{{ m.title }}</span>
                  <span class="tag text-tiny" :class="statusTag(m.status)">
                    {{ statusLabel(m.status) }}
                  </span>
                </router-link>
              </li>
            </ul>
            <p v-else class="text-small text-muted">今天没有会议安排。</p>
          </section>
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import SecretaryChat from '../components/SecretaryChat.vue'
import CommandResultCard from '../components/CommandResultCard.vue'
import AvatarWindow from '../components/AvatarWindow.vue'
import { useSecretary } from '../composables/useSecretary'
import { meetingApi } from '../api/meeting'
import { formatTime, STATUS_LABEL, STATUS_TAG_CLASS } from '../utils/format'

const { lastResult, setSessionId, setCurrentMeetingId } = useSecretary()
setCurrentMeetingId(null)

const today = ref([])
const loading = ref(true)

const onSession = (sid) => {
  if (sid) setSessionId(sid)
}

const fetchToday = async () => {
  loading.value = true
  try {
    const now = new Date()
    const start = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0)
    const end = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59)
    const data = await meetingApi.list({
      from: start.toISOString(),
      to: end.toISOString(),
      limit: 20,
    })
    today.value = data?.items || []
  } catch (err) {
    console.warn('[workbench] 拉取今日会议失败', err)
    today.value = []
  } finally {
    loading.value = false
  }
}

const statusLabel = (s) => STATUS_LABEL[s] || s
const statusTag = (s) => STATUS_TAG_CLASS[s] || ''

onMounted(fetchToday)
</script>

<style scoped>
.workbench {
  padding: var(--space-6) 0 var(--space-7);
}
.workbench__inner {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 0 var(--space-5);
}
.workbench__intro {
  margin-bottom: var(--space-6);
  padding-bottom: var(--space-5);
  border-bottom: 1px solid var(--color-border);
}
.workbench__h1 { margin: 0 0 var(--space-2); }
.workbench__lead {
  margin: 0;
  max-width: 640px;
  color: var(--color-text-2);
  font-size: var(--fs-small);
  line-height: var(--lh-body);
}

.workbench__grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) var(--avatar-aside-w);
  gap: var(--space-5);
  align-items: start;
}
@media (max-width: 960px) {
  .workbench__grid { grid-template-columns: 1fr; }
}

.workbench__main {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.workbench__aside {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  position: sticky;
  top: calc(var(--header-h) + var(--space-4));
}

.aside-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-3);
}
.aside-title {
  font-size: var(--fs-h4);
  font-weight: 600;
  margin: 0;
}
.aside-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
.aside-item {
  display: grid;
  grid-template-columns: 52px 1fr auto;
  align-items: center;
  gap: var(--space-2);
  padding: 8px;
  border-radius: var(--radius-sm);
  color: inherit;
  text-decoration: none;
}
.aside-item:hover { background: var(--color-surface-2); color: inherit; }
.aside-item__time {
  color: var(--color-text-2);
  font-weight: 600;
  font-size: var(--fs-tiny);
}
.aside-item__title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
