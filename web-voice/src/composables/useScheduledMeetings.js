import { ref } from 'vue'
import { meetingApi } from '@shared/api/meeting'

const meetings = ref([])
const loading = ref(false)
let _loaded = false

async function loadScheduledMeetings(limit = 10) {
  loading.value = true
  try {
    const weekAgo = new Date(Date.now() - 7 * 86400000).toISOString()
    const data = await meetingApi.list({
      from: weekAgo,
      limit: 40,
    })
    const items = (data?.items || [])
      .filter((m) => m.status === 'scheduled' || m.status === 'ongoing')
      .sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
      .slice(0, limit)
    meetings.value = items
    _loaded = true
  } catch (e) {
    console.warn('[voice] 已定会议加载失败', e)
    meetings.value = []
  } finally {
    loading.value = false
  }
}

export function useScheduledMeetings() {
  return {
    meetings,
    loading,
    loadScheduledMeetings,
    ensureLoaded() {
      if (!_loaded) return loadScheduledMeetings()
      return Promise.resolve()
    },
  }
}
