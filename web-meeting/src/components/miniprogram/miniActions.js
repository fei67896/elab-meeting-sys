/** 小程序版：环绕数字人的快捷菜单 */
export const MINI_MENU = {
  left: [
    { id: 'book', label: '订会议', icon: '📅', type: 'command', text: '帮我预订明天下午3点的会议' },
    { id: 'schedule', label: '查日程', icon: '🗓', type: 'command', text: '查一下本周有哪些会议安排？' },
  ],
  right: [
    { id: 'agenda', label: '加议程', icon: '📝', type: 'command', text: '给当前会议增加一条议程：项目进度汇报' },
    { id: 'history', label: '专注历史', icon: '📈', type: 'route', to: '/history' },
  ],
  top: [
    { id: 'today', label: '今日会议', icon: '☀️', type: 'command', text: '查一下今天有哪些会议？' },
  ],
  bottom: [
    { id: 'meetings', label: '会议管理', icon: '📋', type: 'route', to: '/meetings' },
  ],
}

export const MINI_TABS = [
  { id: 'secretary', label: '秘书', path: '/mini' },
  { id: 'meetings', label: '会议', path: '/meetings' },
  { id: 'mine', label: '我的', path: '/settings' },
]
