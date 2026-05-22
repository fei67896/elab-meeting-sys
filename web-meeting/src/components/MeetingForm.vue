<template>
  <form class="mform" @submit.prevent="onSubmit">
    <div class="mform__row">
      <label class="mform__label">
        会议标题 <span class="text-tiny text-dim">(可选)</span>
      </label>
      <input
        v-model="form.title"
        class="input"
        placeholder="不填则按开始时间自动生成"
      />
    </div>

    <div class="mform__row mform__grid">
      <div>
        <label class="mform__label">开始时间</label>
        <input v-model="form.start_time_local" type="datetime-local" class="input" required />
      </div>
      <div>
        <label class="mform__label">结束时间 <span class="text-tiny text-dim">(可选)</span></label>
        <input v-model="form.end_time_local" type="datetime-local" class="input" />
      </div>
    </div>

    <div class="mform__row mform__grid">
      <div>
        <label class="mform__label">形式</label>
        <select v-model="form.mode" class="select">
          <option value="online">线上</option>
          <option value="offline">线下</option>
          <option value="hybrid">线上 + 线下</option>
        </select>
      </div>
      <div v-if="form.mode !== 'online'">
        <label class="mform__label">地点</label>
        <input v-model="form.location" class="input" placeholder="例如：图书馆 305" />
      </div>
    </div>

    <div class="mform__row">
      <label class="mform__label">描述 <span class="text-tiny text-dim">(可选)</span></label>
      <textarea v-model="form.description" class="textarea" rows="2" />
    </div>

    <div class="mform__row">
      <label class="mform__label">参会人 <span class="text-tiny text-dim">(回车添加)</span></label>
      <div class="chips">
        <span v-for="(p, i) in form.participants" :key="i" class="tag is-primary">
          {{ p.name }}
          <button type="button" class="chip-x" @click="form.participants.splice(i, 1)" aria-label="移除">×</button>
        </span>
      </div>
      <input
        v-model="participantDraft"
        class="input mt-2"
        placeholder="输入姓名后回车"
        @keydown.enter.prevent="addParticipant"
      />
    </div>

    <div class="mform__row">
      <label class="mform__label">议程 <span class="text-tiny text-dim">(可逐条添加)</span></label>
      <ol class="mform__agendas" v-if="form.agendas.length">
        <li v-for="(a, i) in form.agendas" :key="i" class="agenda-row">
          <span class="agenda-row__topic">{{ a.topic }}</span>
          <span class="tag is-primary text-tiny">{{ categoryLabel(a.category) }}</span>
          <span class="tag text-tiny">{{ a.mode === 'offline' ? '线下' : '线上' }}</span>
          <button type="button" class="btn btn-sm btn-ghost" @click="form.agendas.splice(i, 1)">移除</button>
        </li>
      </ol>
      <div class="agenda-add">
        <input v-model="agendaDraft.topic" class="input" placeholder="议程主题 (回车添加)" @keydown.enter.prevent="addAgenda" />
        <select v-model="agendaDraft.category" class="select">
          <option v-for="o in CATEGORY_OPTIONS" :key="o.value" :value="o.value">{{ o.label }}</option>
        </select>
        <select v-model="agendaDraft.mode" class="select">
          <option value="online">线上</option>
          <option value="offline">线下</option>
        </select>
        <button type="button" class="btn btn-sm" @click="addAgenda">+ 加入</button>
      </div>
    </div>

    <div class="mform__actions">
      <button type="button" class="btn" @click="$emit('cancel')">取消</button>
      <button type="submit" class="btn btn-primary" :disabled="submitting">
        {{ submitting ? '提交中…' : '创建会议' }}
      </button>
    </div>
  </form>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { CATEGORY_LABEL, CATEGORY_OPTIONS } from '../utils/format'

const emit = defineEmits(['submit', 'cancel'])
const props = defineProps({
  submitting: { type: Boolean, default: false },
})

const form = reactive({
  title: '',
  start_time_local: defaultStart(),
  end_time_local: '',
  mode: 'online',
  location: '',
  description: '',
  participants: [],
  agendas: [],
})

const participantDraft = ref('')
const agendaDraft = reactive({ topic: '', category: 'general', mode: 'online' })

const categoryLabel = (v) => CATEGORY_LABEL[v] || v

function defaultStart() {
  const d = new Date()
  d.setMinutes(0, 0, 0)
  d.setHours(d.getHours() + 1)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function localToIso(local) {
  if (!local) return null
  // datetime-local 是本机时区, 拼上 +08:00 以保持一致 (服务端默认按 CST 解析)
  return `${local}:00+08:00`
}

function addParticipant() {
  const n = participantDraft.value.trim()
  if (!n) return
  form.participants.push({ name: n })
  participantDraft.value = ''
}

function addAgenda() {
  const t = agendaDraft.topic.trim()
  if (!t) return
  form.agendas.push({
    topic: t,
    category: agendaDraft.category || 'general',
    mode: agendaDraft.mode || 'online',
  })
  agendaDraft.topic = ''
}

function onSubmit() {
  // 把未提交的草稿也带上, 避免用户漏按回车
  if (participantDraft.value.trim()) addParticipant()
  if (agendaDraft.topic.trim()) addAgenda()

  emit('submit', {
    title: form.title.trim() || undefined,
    start_time: localToIso(form.start_time_local),
    end_time: localToIso(form.end_time_local),
    mode: form.mode || 'online',
    location: (form.location || '').trim() || null,
    description: form.description.trim() || null,
    participants: form.participants,
    agendas: form.agendas,
  })
}
</script>

<style scoped>
.mform { display: flex; flex-direction: column; gap: var(--space-4); }
.mform__row { display: flex; flex-direction: column; gap: 6px; }
.mform__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
}
.mform__label {
  font-size: var(--fs-small);
  font-weight: 600;
  color: var(--color-text-2);
}
.mform__agendas {
  margin: 0;
  padding-left: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.chip-x {
  background: none;
  border: 0;
  margin-left: 4px;
  color: inherit;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
}
.mform__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
}

.agenda-row {
  display: grid;
  grid-template-columns: 1fr auto auto auto;
  gap: var(--space-2);
  align-items: center;
  padding: 4px 0;
  border-bottom: 1px dashed var(--color-border);
}
.agenda-row:last-child { border-bottom: 0; }
.agenda-row__topic { font-weight: 500; }
.agenda-add {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 120px 100px auto;
  gap: var(--space-2);
  margin-top: var(--space-2);
}
@media (max-width: 640px) {
  .agenda-add { grid-template-columns: 1fr; }
}
</style>
