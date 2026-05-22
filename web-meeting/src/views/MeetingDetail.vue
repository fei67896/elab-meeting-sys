<template>
  <div class="md">
    <div class="container">
      <router-link to="/meetings" class="text-small back">← 返回列表</router-link>

      <div v-if="loading" class="text-muted mt-4">加载中…</div>
      <div v-else-if="!meeting" class="text-muted mt-4">会议不存在或已被删除。</div>

      <template v-else>
        <header class="md__head">
          <div>
            <div class="flex items-center gap-2 mb-2">
              <span class="tag" :class="statusClass">{{ statusLabel }}</span>
              <span class="tag text-tiny">{{ modeLabel }}</span>
              <span class="text-tiny text-dim mono">{{ meeting.meeting_code }}</span>
            </div>
            <h1 class="md__title">{{ meeting.title }}</h1>
            <p class="md__sub">
              {{ formatDateTime(meeting.start_time) }}
              <span v-if="meeting.end_time"> &nbsp;—&nbsp; {{ formatDateTime(meeting.end_time) }}</span>
              <span class="text-dim"> · {{ formatRelative(meeting.start_time) }}</span>
              <span v-if="meeting.location" class="text-dim"> · 地点 {{ meeting.location }}</span>
            </p>
          </div>
          <div class="md__actions">
            <button class="btn" @click="onAttend('attending')" :class="myAttendance === 'attending' ? 'btn-primary' : ''">
              参加
            </button>
            <button class="btn" @click="onAttend('declined')" :class="myAttendance === 'declined' ? 'btn-primary' : ''">
              不参加
            </button>
            <a class="btn" :href="icsUrl" :download="`meeting-${meeting.meeting_code}.ics`">下载 ICS</a>
            <button v-if="isOwner" class="btn" @click="onShare">分享链接</button>
            <button
              v-if="isOwner && meeting.status !== 'cancelled'"
              class="btn"
              @click="onCancel"
            >取消会议</button>
            <button v-if="isOwner" class="btn" @click="openParticipant = true">+ 参会人</button>
            <button class="btn btn-primary" @click="openAgenda = true">+ 议程</button>
          </div>
        </header>

        <div class="md__grid">
          <main class="md__body">
            <section class="card">
              <h3 class="md__h3">议程</h3>
              <AgendaList :agendas="meeting.agendas || []" />
            </section>

            <section class="card">
              <h3 class="md__h3">备注</h3>
              <p v-if="meeting.description" class="md__desc">{{ meeting.description }}</p>
              <p v-else class="text-muted text-small">暂无描述。</p>
            </section>
          </main>

          <aside class="md__side">
            <section class="card">
              <h3 class="md__h3">参会人 <span class="text-tiny text-dim">{{ meeting.participants?.length || 0 }}</span></h3>
              <ul v-if="meeting.participants?.length" class="participants">
                <li v-for="p in meeting.participants" :key="p.id">
                  <span class="avatar-sm">{{ initial(p.name) }}</span>
                  <div class="flex flex-col" style="min-width:0">
                    <span class="participant-name">{{ p.name }}</span>
                    <span v-if="p.email" class="text-tiny text-dim mono">{{ p.email }}</span>
                  </div>
                  <span class="tag text-tiny" :class="roleTagClass(p.role)">{{ roleLabel(p.role) }}</span>
                  <span class="tag text-tiny" :class="attendanceClass(p.attendance_status)">
                    {{ attendanceLabel(p.attendance_status) }}
                  </span>
                </li>
              </ul>
              <p v-if="meeting.attendance_summary" class="text-tiny text-muted mt-2">
                参加 {{ meeting.attendance_summary.attending }} ·
                不参加 {{ meeting.attendance_summary.declined }} ·
                待定 {{ meeting.attendance_summary.pending }}
              </p>
              <p v-else class="text-muted text-small">尚未添加参会人。</p>
            </section>

            <section class="card">
              <h3 class="md__h3">会议链接</h3>
              <code class="md__link">{{ meeting.meeting_url }}</code>
              <p class="text-tiny text-dim mt-2">
                本地占位链接，演示用。后续可对接腾讯会议/Zoom 真实创建会议。
              </p>
            </section>
          </aside>
        </div>
      </template>
    </div>

    <Modal :open="openAgenda" title="追加议程" @close="openAgenda = false">
      <form @submit.prevent="submitAgenda" class="mform">
        <div class="mform__row">
          <label class="mform__label">议程主题</label>
          <input v-model="agendaDraft.topic" class="input" required />
        </div>
        <div class="mform__row mform__grid">
          <div>
            <label class="mform__label">类型</label>
            <select v-model="agendaDraft.category" class="select">
              <option v-for="o in CATEGORY_OPTIONS" :key="o.value" :value="o.value">{{ o.label }}</option>
            </select>
          </div>
          <div>
            <label class="mform__label">形式</label>
            <select v-model="agendaDraft.mode" class="select">
              <option value="online">线上</option>
              <option value="offline">线下</option>
            </select>
          </div>
        </div>
        <div class="mform__row mform__grid">
          <div>
            <label class="mform__label">主讲</label>
            <input v-model="agendaDraft.owner" class="input" />
          </div>
          <div>
            <label class="mform__label">时长 (分钟)</label>
            <input v-model.number="agendaDraft.duration_min" type="number" min="1" class="input" />
          </div>
        </div>
        <div class="mform__row">
          <label class="mform__label">备注</label>
          <textarea v-model="agendaDraft.notes" class="textarea" rows="2" />
        </div>
        <div class="mform__actions">
          <button type="button" class="btn" @click="openAgenda = false">取消</button>
          <button type="submit" class="btn btn-primary">追加</button>
        </div>
      </form>
    </Modal>

    <Modal :open="!!shareLink" title="分享链接已生成" @close="shareLink = ''">
      <div class="share-block">
        <p class="text-small text-muted mb-3">
          把下面的链接发给受邀人, TA 打开后可以匿名加入这场会议。
        </p>
        <div class="share-url">
          <input :value="shareLink" class="input" readonly @focus="$event.target.select()" />
          <button class="btn btn-primary" @click="copyShare">复制</button>
        </div>
        <p v-if="shareCopied" class="text-tiny text-success mt-2">已复制到剪贴板。</p>
      </div>
    </Modal>

    <Modal :open="openParticipant" title="添加参会人" @close="openParticipant = false">
      <form @submit.prevent="submitParticipant" class="mform">
        <div class="mform__row">
          <label class="mform__label">姓名</label>
          <input v-model="participantDraft.name" class="input" required />
        </div>
        <div class="mform__row">
          <label class="mform__label">邮箱</label>
          <input v-model="participantDraft.email" type="email" class="input" />
        </div>
        <div class="mform__row">
          <label class="mform__label">角色</label>
          <select v-model="participantDraft.role" class="select">
            <option value="attendee">参会者</option>
            <option value="host">主持人</option>
            <option value="optional">可选参会</option>
          </select>
        </div>
        <div class="mform__actions">
          <button type="button" class="btn" @click="openParticipant = false">取消</button>
          <button type="submit" class="btn btn-primary">添加</button>
        </div>
      </form>
    </Modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import AgendaList from '../components/AgendaList.vue'
import Modal from '../components/Modal.vue'
import { meetingApi } from '../api/meeting'
import { useAuth } from '../composables/useAuth'
import { useSecretary } from '../composables/useSecretary'
import {
  formatDateTime, formatRelative,
  STATUS_LABEL, STATUS_TAG_CLASS,
  MODE_LABEL, CATEGORY_OPTIONS, ATTENDANCE_LABEL, ATTENDANCE_TAG_CLASS,
} from '../utils/format'

const route = useRoute()
const meetingId = computed(() => {
  const raw = route.params.id
  const n = Number(raw)
  return Number.isFinite(n) && n > 0 ? n : null
})
const { user, isOwner } = useAuth()
const { setCurrentMeetingId } = useSecretary()

const meeting = ref(null)
const loading = ref(true)

const openAgenda = ref(false)
const agendaDraft = reactive({
  topic: '', owner: '', duration_min: null, notes: '',
  category: 'general', mode: 'online',
})

const openParticipant = ref(false)
const participantDraft = reactive({ name: '', email: '', role: 'attendee' })

const shareLink = ref('')
const shareCopied = ref(false)

const icsUrl = computed(() => meetingApi.icsUrl(meetingId.value))

const statusLabel = computed(() =>
  meeting.value ? STATUS_LABEL[meeting.value.status] || meeting.value.status : ''
)
const statusClass = computed(() =>
  meeting.value ? STATUS_TAG_CLASS[meeting.value.status] || '' : ''
)
const modeLabel = computed(() =>
  meeting.value ? MODE_LABEL[meeting.value.mode] || meeting.value.mode : ''
)

// 当前登录用户对该会议的参会状态
const myAttendance = computed(() => {
  if (!meeting.value || !user.value) return null
  const me = meeting.value.participants?.find(p => p.user_id === user.value.id)
  return me?.attendance_status || null
})

const refresh = async () => {
  loading.value = true
  try {
    if (meetingId.value == null) {
      meeting.value = null
      return
    }
    meeting.value = await meetingApi.get(meetingId.value)
    setCurrentMeetingId(meetingId.value)
  } catch (err) {
    meeting.value = null
    console.warn('[meeting-detail] 加载失败', err)
  } finally {
    loading.value = false
  }
}

const submitAgenda = async () => {
  try {
    await meetingApi.addAgenda(meetingId.value, { ...agendaDraft })
    openAgenda.value = false
    agendaDraft.topic = ''
    agendaDraft.owner = ''
    agendaDraft.duration_min = null
    agendaDraft.notes = ''
    agendaDraft.category = 'general'
    agendaDraft.mode = 'online'
    await refresh()
  } catch (err) {
    alert(`追加议程失败: ${err.message}`)
  }
}

const submitParticipant = async () => {
  try {
    await meetingApi.addParticipant(meetingId.value, { ...participantDraft })
    openParticipant.value = false
    participantDraft.name = ''
    participantDraft.email = ''
    participantDraft.role = 'attendee'
    await refresh()
  } catch (err) {
    alert(`添加参会人失败: ${err.message}`)
  }
}

const onCancel = async () => {
  if (!confirm('确定取消这场会议吗？')) return
  try {
    await meetingApi.update(meetingId.value, { status: 'cancelled' })
    await refresh()
  } catch (err) {
    alert(`取消失败: ${err.message}`)
  }
}

const onAttend = async (status) => {
  try {
    await meetingApi.setAttendance(meetingId.value, { status })
    await refresh()
  } catch (err) {
    alert(`更新参会状态失败: ${err.message}`)
  }
}

const onShare = async () => {
  try {
    const r = await meetingApi.createShare(meetingId.value)
    shareLink.value = `${location.origin}/#/invite/${r.token}`
    shareCopied.value = false
  } catch (err) {
    alert(`生成分享链接失败: ${err.message}`)
  }
}

const copyShare = async () => {
  try {
    await navigator.clipboard.writeText(shareLink.value)
    shareCopied.value = true
  } catch (_) {
    // 兜底: 选中文本
    shareCopied.value = false
  }
}

const initial = (n) => {
  if (!n) return '?'
  return /[\u4e00-\u9fa5]/.test(n) ? n.slice(-1) : n.slice(0, 1).toUpperCase()
}
const roleLabel = (r) => ({ host: '主持人', attendee: '参会', optional: '可选' }[r] || r)
const roleTagClass = (r) => (r === 'host' ? 'is-accent' : '')
const attendanceLabel = (s) => ATTENDANCE_LABEL[s] || '待定'
const attendanceClass = (s) => ATTENDANCE_TAG_CLASS[s] || ''

watch(meetingId, refresh)
onMounted(refresh)
</script>

<style scoped>
.md { padding: var(--space-5) 0 var(--space-7); }
.back {
  color: var(--color-text-2);
}
.md__head {
  margin: var(--space-4) 0 var(--space-5);
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-5);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}
.md__title {
  font-family: var(--font-serif);
  font-size: var(--fs-display);
  margin: 0 0 var(--space-2);
  letter-spacing: -0.01em;
}
.md__sub {
  margin: 0;
  color: var(--color-text-2);
  font-size: var(--fs-small);
}
.md__actions {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
  align-items: center;
}

.md__grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: var(--space-5);
}
@media (max-width: 900px) {
  .md__grid { grid-template-columns: 1fr; }
}
.md__body, .md__side {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.md__h3 {
  font-family: var(--font-serif);
  font-size: var(--fs-h4);
  margin: 0 0 var(--space-3);
}
.md__desc {
  margin: 0;
  font-family: var(--font-serif);
  font-size: var(--fs-body);
  line-height: var(--lh-loose);
  color: var(--color-text);
}
.md__link {
  display: block;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: var(--fs-small);
  color: var(--color-text);
  word-break: break-all;
}

.participants {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.participants li {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr) auto auto;
  align-items: center;
  gap: var(--space-2);
  padding: 8px 0;
  border-bottom: 1px solid var(--color-border);
}
.participants li:last-child { border-bottom: 0; }
.avatar-sm {
  width: 28px; height: 28px; border-radius: 50%;
  background: var(--color-text);
  color: var(--color-text-inverse);
  font-size: 11px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.participant-name { font-weight: 500; }

.mform { display: flex; flex-direction: column; gap: var(--space-4); }
.mform__row { display: flex; flex-direction: column; gap: 6px; }
.mform__grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); }
.mform__label { font-size: var(--fs-small); font-weight: 600; color: var(--color-text-2); }
.mform__actions { display: flex; justify-content: flex-end; gap: var(--space-2); }

.share-url {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--space-2);
}
.text-success { color: var(--color-success); }
</style>
