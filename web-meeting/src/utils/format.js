// 时间和文本格式化工具

const PAD = (n) => String(n).padStart(2, '0')

export function formatDateTime(iso) {
  if (!iso) return '-'
  try {
    const d = new Date(iso)
    if (isNaN(d.getTime())) return iso
    return `${d.getFullYear()}-${PAD(d.getMonth() + 1)}-${PAD(d.getDate())} ${PAD(d.getHours())}:${PAD(d.getMinutes())}`
  } catch (_) {
    return iso
  }
}

export function formatDate(iso) {
  if (!iso) return '-'
  try {
    const d = new Date(iso)
    if (isNaN(d.getTime())) return iso
    return `${d.getFullYear()}-${PAD(d.getMonth() + 1)}-${PAD(d.getDate())}`
  } catch (_) {
    return iso
  }
}

export function formatTime(iso) {
  if (!iso) return '-'
  try {
    const d = new Date(iso)
    if (isNaN(d.getTime())) return iso
    return `${PAD(d.getHours())}:${PAD(d.getMinutes())}`
  } catch (_) {
    return iso
  }
}

export function formatRelative(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  const now = new Date()
  const diff = (d - now) / 1000  // 秒
  const abs = Math.abs(diff)
  const sign = diff >= 0 ? '后' : '前'

  if (abs < 60) return diff >= 0 ? '即将开始' : '刚刚'
  if (abs < 3600) return `${Math.floor(abs / 60)} 分钟${sign}`
  if (abs < 86400) return `${Math.floor(abs / 3600)} 小时${sign}`
  if (abs < 86400 * 7) return `${Math.floor(abs / 86400)} 天${sign}`
  return formatDate(iso)
}

export const STATUS_LABEL = {
  scheduled: '已排期',
  ongoing: '进行中',
  completed: '已完成',
  cancelled: '已取消',
}

export const STATUS_TAG_CLASS = {
  scheduled: 'is-primary',
  ongoing: 'is-success',
  completed: '',
  cancelled: 'is-danger',
}

export const MODE_LABEL = {
  online: '线上',
  offline: '线下',
  hybrid: '线上 + 线下',
}

export const CATEGORY_LABEL = {
  project_report: '项目汇报',
  research_report: '科研汇报',
  general: '综合',
  other: '其他',
}

export const CATEGORY_OPTIONS = [
  { value: 'project_report', label: '项目汇报' },
  { value: 'research_report', label: '科研汇报' },
  { value: 'general', label: '综合' },
  { value: 'other', label: '其他' },
]

export const ATTENDANCE_LABEL = {
  attending: '参加',
  declined: '不参加',
  pending: '待定',
}

export const ATTENDANCE_TAG_CLASS = {
  attending: 'is-success',
  declined: 'is-danger',
  pending: '',
}
