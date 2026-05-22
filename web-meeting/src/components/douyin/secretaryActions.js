/** 会议秘书右侧快捷操作 */
export const SECRETARY_ACTIONS = [
  {
    id: 'today',
    label: '今日',
    icon: 'calendar',
    type: 'command',
    text: '查一下今天和明天有哪些会议安排？',
  },
  {
    id: 'book',
    label: '订会',
    icon: 'plus',
    type: 'command',
    text: '帮我预订明天下午3点的会议，标题技术评审',
  },
  {
    id: 'agenda',
    label: '议程',
    icon: 'list',
    type: 'command',
    text: '给当前会议增加一条议程：项目进度汇报',
  },
  {
    id: 'interrupt',
    label: '打断',
    icon: 'stop',
    type: 'interrupt',
    accent: true,
  },
]
