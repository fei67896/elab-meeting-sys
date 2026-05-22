import { ref } from 'vue'
import { legacyApi } from '@shared/api/legacy.js'
import { aggregateConcentrationPoints } from '../utils/chart'

const items = ref([])
const loading = ref(false)
let _loaded = false

async function loadFocusHistory(sessionLimit = 5) {
  loading.value = true
  try {
    const sess = await legacyApi.sessions(sessionLimit)
    const sessions = sess?.items || []
    const cards = await Promise.all(
      sessions.map(async (s) => {
        try {
          const ov = await legacyApi.overview(s.group_id)
          const participants = ov?.participants || []
          const points = aggregateConcentrationPoints(participants)
          const avgs = participants
            .map((p) => p.concentration?.summary?.avg)
            .filter((v) => v != null)
          const meanFocus = avgs.length
            ? Math.round((avgs.reduce((a, b) => a + Number(b), 0) / avgs.length) * 10) / 10
            : null
          return {
            groupId: s.group_id,
            startedAt: s.started_at,
            endedAt: s.ended_at,
            studentCount: s.student_count,
            sampleCount: s.sample_count,
            points,
            meanFocus,
          }
        } catch (e) {
          console.warn('[voice] overview', s.group_id, e)
          return {
            groupId: s.group_id,
            startedAt: s.started_at,
            endedAt: s.ended_at,
            studentCount: s.student_count,
            sampleCount: s.sample_count,
            points: [],
            meanFocus: null,
          }
        }
      }),
    )
    items.value = cards
    _loaded = true
  } catch (e) {
    console.warn('[voice] 专注度历史加载失败', e)
    items.value = []
  } finally {
    loading.value = false
  }
}

export function useFocusHistory() {
  return {
    items,
    loading,
    loadFocusHistory,
    ensureLoaded() {
      if (!_loaded) return loadFocusHistory()
      return Promise.resolve()
    },
  }
}
