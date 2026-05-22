<template>
  <div class="meetings">
    <div class="container">
      <header class="page-head">
        <div>
          <h1 class="page-title">会议管理</h1>
          <p class="page-sub">所有由会议秘书登记或手动创建的线上会议。</p>
        </div>
        <button class="btn btn-primary" @click="openCreate = true">+ 新建会议</button>
      </header>

      <section class="filters card is-flat">
        <div class="filters__row">
          <div class="filters__field">
            <label>关键词</label>
            <input v-model="filters.keyword" class="input" placeholder="标题 / 描述" @change="refresh" />
          </div>
          <div class="filters__field">
            <label>参会人</label>
            <input v-model="filters.participant" class="input" placeholder="姓名" @change="refresh" />
          </div>
          <div class="filters__field">
            <label>状态</label>
            <select v-model="filters.status" class="select" @change="refresh">
              <option value="">全部</option>
              <option value="scheduled">已排期</option>
              <option value="ongoing">进行中</option>
              <option value="completed">已完成</option>
              <option value="cancelled">已取消</option>
            </select>
          </div>
          <div class="filters__field">
            <label>开始日期</label>
            <input v-model="filters.fromDate" type="date" class="input" @change="refresh" />
          </div>
          <div class="filters__field">
            <label>截止日期</label>
            <input v-model="filters.toDate" type="date" class="input" @change="refresh" />
          </div>
          <div class="filters__field filters__field--auto">
            <button class="btn" @click="resetFilters">重置</button>
          </div>
        </div>
      </section>

      <section class="meetings__list">
        <div v-if="loading" class="text-muted">加载中…</div>
        <div v-else-if="items.length === 0" class="empty card is-flat">
          <p class="text-muted">没有匹配的会议。试试调整筛选条件，或新建一场。</p>
        </div>
        <div v-else class="grid">
          <MeetingCard v-for="m in items" :key="m.id" :meeting="m" />
        </div>
      </section>
    </div>

    <Modal :open="openCreate" title="新建会议" @close="openCreate = false">
      <MeetingForm :submitting="creating" @cancel="openCreate = false" @submit="handleCreate" />
    </Modal>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import MeetingCard from '../components/MeetingCard.vue'
import MeetingForm from '../components/MeetingForm.vue'
import Modal from '../components/Modal.vue'
import { meetingApi } from '../api/meeting'

const router = useRouter()

const filters = reactive({
  keyword: '',
  participant: '',
  status: '',
  fromDate: '',
  toDate: '',
})

const items = ref([])
const loading = ref(true)
const openCreate = ref(false)
const creating = ref(false)

const refresh = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.participant) params.participant = filters.participant
    if (filters.status) params.status = filters.status
    if (filters.fromDate) params.from = `${filters.fromDate}T00:00:00+08:00`
    if (filters.toDate) params.to = `${filters.toDate}T23:59:59+08:00`
    const data = await meetingApi.list(params)
    items.value = data?.items || []
  } catch (err) {
    console.warn('[meetings] 加载失败', err)
    items.value = []
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.keyword = ''
  filters.participant = ''
  filters.status = ''
  filters.fromDate = ''
  filters.toDate = ''
  refresh()
}

const handleCreate = async (payload) => {
  creating.value = true
  try {
    const m = await meetingApi.create(payload)
    openCreate.value = false
    await refresh()
    if (m && m.id) router.push(`/meetings/${m.id}`)
  } catch (err) {
    alert(`创建失败: ${err.message}`)
  } finally {
    creating.value = false
  }
}

onMounted(refresh)
</script>

<style scoped>
.meetings { padding: var(--space-5) 0 var(--space-7); }
.page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}
.page-title {
  font-family: var(--font-serif);
  font-size: var(--fs-h1);
  margin: 0 0 4px;
}
.page-sub {
  margin: 0;
  color: var(--color-text-2);
  font-size: var(--fs-small);
}

.filters {
  margin-bottom: var(--space-5);
  padding: var(--space-4);
}
.filters__row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: var(--space-3);
  align-items: end;
}
.filters__field { display: flex; flex-direction: column; gap: 4px; }
.filters__field label {
  font-size: var(--fs-tiny);
  font-weight: 600;
  color: var(--color-text-2);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.filters__field--auto { align-self: end; }

.meetings__list { min-height: 200px; }
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
}
.empty {
  padding: var(--space-7);
  text-align: center;
}
</style>
