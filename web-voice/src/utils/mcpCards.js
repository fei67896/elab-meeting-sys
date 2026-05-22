/** 与后端 mcp_registry.MCP_CARDS 对齐：四角 slot lt/lb/rt/rb */
export const DEFAULT_MCP_CARDS = [
  {
    id: 'book',
    side: 'left',
    slot: 'lt',
    title: '预订会议',
    description: '说出日期时间即可预定',
  },
  {
    id: 'roster',
    side: 'left',
    slot: 'lb',
    title: '议程参会',
    description: '添加议程、参会人与出席登记',
  },
  {
    id: 'query',
    side: 'right',
    slot: 'rt',
    title: '查询会议',
    description: '按条件检索或查看单场详情',
  },
  {
    id: 'history',
    side: 'right',
    slot: 'rb',
    title: '会议历史',
    description: '近期语音指令与处理记录',
  },
]

export const TOOL_TO_CARD = {
  create_meeting: 'book',
  add_regular_meeting: 'book',
  cancel_meeting: 'book',
  add_agenda: 'roster',
  add_participant: 'roster',
  set_attendance: 'roster',
  list_meetings: 'query',
  get_meeting: 'query',
  list_command_history: 'history',
}

export const SLOT_ORDER = ['lt', 'lb', 'rt', 'rb']

export function cardIdForTool(tool) {
  return TOOL_TO_CARD[tool] || null
}
