<template>
  <div class="invite">
    <!-- 阶段一: 输入显示名 + 自动登录 -->
    <section v-if="phase === 'enter'" class="invite__welcome">
      <div class="invite__card card">
        <div class="invite__brand">
          <BrandLogo size="md" />
          <h1 class="invite__title">受邀加入会议</h1>
          <p class="invite__sub">请填写你的显示名，会议秘书会引导你完成确认。</p>
        </div>
        <form class="invite__form" @submit.prevent="enter">
          <label class="invite__field">
            <span>显示名</span>
            <input v-model="displayName" class="input" placeholder="例如 张三" autofocus />
          </label>
          <p v-if="error" class="invite__error">{{ error }}</p>
          <button type="submit" class="btn btn-primary btn-lg" :disabled="entering">
            {{ entering ? '加入中…' : '加入会议' }}
          </button>
          <p class="text-tiny text-muted text-center mt-2">
            进入后, 数字人会自动连接并开始为你播报。
          </p>
        </form>
      </div>
    </section>

    <!-- 阶段二: 已登录, 主工作面板 -->
    <section v-else class="invite__main">
      <div class="invite__inner">
        <header class="invite__head">
          <div>
            <p class="text-tiny text-dim">受邀参与</p>
            <h1 class="invite__h1">{{ meeting?.title || '加载中…' }}</h1>
            <p class="invite__meta">
              <span>{{ formatDateTime(meeting?.start_time) }}</span>
              <span class="text-dim" v-if="meeting?.mode">{{ modeLabel(meeting.mode) }}</span>
              <span class="text-dim" v-if="meeting?.location">地点 {{ meeting.location }}</span>
              <span class="text-dim mono" v-if="meeting?.meeting_code">{{ meeting.meeting_code }}</span>
            </p>
          </div>
          <div class="invite__attend">
            <button class="btn"
                    :class="myAttendance === 'attending' ? 'btn-primary' : ''"
                    @click="setAttendance('attending')">参加</button>
            <button class="btn"
                    :class="myAttendance === 'declined' ? 'btn-primary' : ''"
                    @click="setAttendance('declined')">不参加</button>
          </div>
        </header>

        <div class="invite__grid">
          <main class="invite__col-main">
            <SecretaryChat />
            <CommandResultCard :result="lastResult" />
          </main>

          <aside class="invite__col-side">
            <AvatarWindow :auto-connect="true" @session="onSession" />

            <section class="card">
              <h3 class="invite__h3">添加议程</h3>
              <p class="text-tiny text-muted mb-2">
                也可以直接说："给当前会议加一项科研汇报议程, 主题是 XX"。
              </p>
              <form class="invite__agenda" @submit.prevent="submitAgenda">
                <input v-model="agendaDraft.topic" class="input" placeholder="议程主题" required />
                <div class="invite__agenda-row">
                  <select v-model="agendaDraft.category" class="select">
                    <option v-for="o in CATEGORY_OPTIONS" :key="o.value" :value="o.value">{{ o.label }}</option>
                  </select>
                  <select v-model="agendaDraft.mode" class="select">
                    <option value="online">线上</option>
                    <option value="offline">线下</option>
                  </select>
                </div>
                <button type="submit" class="btn btn-primary btn-sm" :disabled="submittingAgenda">
                  {{ submittingAgenda ? '提交中…' : '+ 添加议程' }}
                </button>
              </form>
            </section>

            <section class="card">
              <h3 class="invite__h3">现有议程 <span class="text-tiny text-dim">{{ meeting?.agendas?.length || 0 }}</span></h3>
              <AgendaList :agendas="meeting?.agendas || []" />
            </section>
          </aside>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BrandLogo from '../components/BrandLogo.vue'
import SecretaryChat from '../components/SecretaryChat.vue'
import CommandResultCard from '../components/CommandResultCard.vue'
import AvatarWindow from '../components/AvatarWindow.vue'
import AgendaList from '../components/AgendaList.vue'
import { meetingApi } from '../api/meeting'
import { useAuth } from '../composables/useAuth'
import { useSecretary } from '../composables/useSecretary'
import {
  formatDateTime, MODE_LABEL, CATEGORY_OPTIONS,
} from '../utils/format'

const route = useRoute()
const router = useRouter()
const { loginByShare, user, isAuthed, guestCtx } = useAuth()
const { lastResult, setSessionId, setCurrentMeetingId, pushMessage } = useSecretary()

const shareToken = computed(() => route.params.token)

const phase = ref('enter') // enter | ready
const displayName = ref('')
const entering = ref(false)
const error = ref('')

const meeting = ref(null)
const submittingAgenda = ref(false)

const agendaDraft = reactive({
  topic: '',
  category: 'general',
  mode: 'online',
})

const myAttendance = computed(() => {
  if (!meeting.value || !user.value) return null
  const me = meeting.value.participants?.find(p => p.user_id === user.value.id)
  return me?.attendance_status || null
})

const modeLabel = (m) => MODE_LABEL[m] || m

const refresh = async () => {
  if (!meeting.value) return
  meeting.value = await meetingApi.get(meeting.value.id)
}

const enter = async () => {
  if (!shareToken.value) {
    error.value = '链接缺少 token'
    return
  }
  entering.value = true
  error.value = ''
  try {
    const data = await loginByShare(shareToken.value, displayName.value.trim())
    meeting.value = await meetingApi.get(data.meeting_id)
    setCurrentMeetingId(meeting.value.id)
    phase.value = 'ready'

    // 给一个欢迎消息进对话流
    pushMessage('system',
      `已成功加入"${meeting.value.title}"。数字人正在连接, 可以语音或文字下达指令。`,
    )
  } catch (err) {
    error.value = err.message || '加入失败'
  } finally {
    entering.value = false
  }
}

const onSession = (sid) => {
  if (sid) setSessionId(sid)
}

const setAttendance = async (status) => {
  try {
    await meetingApi.setAttendance(meeting.value.id, { status })
    await refresh()
  } catch (err) {
    alert(`参会状态更新失败: ${err.message}`)
  }
}

const submitAgenda = async () => {
  if (!agendaDraft.topic.trim()) return
  submittingAgenda.value = true
  try {
    await meetingApi.addAgenda(meeting.value.id, { ...agendaDraft })
    agendaDraft.topic = ''
    await refresh()
  } catch (err) {
    alert(`议程添加失败: ${err.message}`)
  } finally {
    submittingAgenda.value = false
  }
}

// 进入页面时的智能恢复:
// 1. 当前 user 已是 owner -> 直接跳到 meeting-detail (token 关联的会议)
// 2. 当前 user 是 guest 且 guestCtx.share_token 与 URL 一致 -> 跳过输名直接进
// 3. 其他情况 -> 走 phase='enter' 输名
onMounted(async () => {
  const urlToken = shareToken.value
  if (!urlToken) return

  // owner 已登录: 不走 invite, 直接看会议详情 (owner 有全权限)
  if (isAuthed.value && user.value?.role === 'owner') {
    try {
      // 临时解析: 我们不知道这个 share token 对应哪个会议,
      // 但 owner 自己应该走 meeting 管理页, 这里给一个安全跳转
      router.replace({ name: 'meetings' })
    } catch (_) {}
    return
  }

  // guest 已登录, 且就是这个 share token 的 -> 复用 session
  if (
    isAuthed.value &&
    user.value?.role === 'guest' &&
    guestCtx.value?.share_token === urlToken &&
    guestCtx.value?.meeting_id
  ) {
    try {
      meeting.value = await meetingApi.get(guestCtx.value.meeting_id)
      setCurrentMeetingId(meeting.value.id)
      displayName.value = guestCtx.value.display_name || user.value.display_name || ''
      phase.value = 'ready'
    } catch (e) {
      // 拉不到 -> 回到输名页让用户重试
      error.value = '会话恢复失败, 请重新进入'
    }
  }
})
</script>

<style scoped>
.invite { min-height: 100vh; background: var(--color-bg); }

/* ---- 阶段一: 欢迎卡 ---- */
.invite__welcome {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-5);
  background:
    radial-gradient(at 20% 20%, rgba(20, 55, 125, 0.06), transparent 60%),
    radial-gradient(at 80% 80%, rgba(200, 16, 46, 0.04), transparent 60%),
    var(--color-bg);
}
.invite__card {
  width: 100%;
  max-width: 440px;
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  box-shadow: var(--shadow-2);
}
.invite__brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 6px;
}
.invite__title { font-family: var(--font-serif); font-size: var(--fs-h1); margin: 0; }
.invite__sub { margin: 0; color: var(--color-text-2); font-size: var(--fs-small); }

.invite__form { display: flex; flex-direction: column; gap: var(--space-3); }
.invite__field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: var(--fs-small);
}
.invite__field span { font-weight: 600; color: var(--color-text-2); }
.invite__error {
  margin: 0;
  padding: 8px 10px;
  background: var(--color-danger-soft);
  color: var(--color-danger);
  border-radius: var(--radius-sm);
  font-size: var(--fs-small);
}

/* ---- 阶段二: 工作面板 ---- */
.invite__main { padding: var(--space-5) 0 var(--space-7); }
.invite__inner {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 0 var(--space-5);
}
.invite__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-5);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--space-5);
}
.invite__h1 {
  font-family: var(--font-serif);
  font-size: var(--fs-h1);
  margin: 4px 0;
  letter-spacing: -0.005em;
}
.invite__meta {
  margin: 0;
  font-size: var(--fs-small);
  color: var(--color-text-2);
  display: flex;
  gap: var(--space-3);
  flex-wrap: wrap;
}
.invite__attend { display: flex; gap: var(--space-2); }

.invite__grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) var(--avatar-aside-w);
  gap: var(--space-5);
}
@media (max-width: 960px) {
  .invite__grid { grid-template-columns: 1fr; }
}
.invite__col-main, .invite__col-side {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.invite__h3 {
  font-family: var(--font-serif);
  font-size: var(--fs-h4);
  margin: 0 0 var(--space-2);
}
.invite__agenda { display: flex; flex-direction: column; gap: var(--space-2); }
.invite__agenda-row { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2); }
.text-center { text-align: center; }
</style>
