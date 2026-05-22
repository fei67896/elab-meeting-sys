import { reactive, computed } from 'vue'
import { DEFAULT_MCP_CARDS, SLOT_ORDER } from '../utils/mcpCards'
import { secretaryApi } from '@shared/api/meeting'

const cards = reactive({})

function ensureCard(def) {
  const existing = cards[def.id]
  if (!existing) {
    cards[def.id] = {
      id: def.id,
      side: def.side,
      slot: def.slot || 'lt',
      title: def.title,
      description: def.description,
      status: 'idle',
      lines: [],
      tool: null,
      at: null,
    }
  } else if (def.slot) {
    existing.slot = def.slot
  }
}

function initFromDefs(defs = DEFAULT_MCP_CARDS) {
  for (const d of defs) ensureCard(d)
}

initFromDefs()

function applyMcpCalls(mcpCalls) {
  if (!mcpCalls?.length) return
  for (const call of mcpCalls) {
    const id = call.card_id
    if (!cards[id]) {
      ensureCard({
        id,
        side: call.side || 'left',
        slot: call.slot || 'lt',
        title: call.card_title || id,
        description: '',
      })
    }
    const c = cards[id]
    c.status = call.status === 'error' ? 'error' : 'success'
    c.lines = Array.isArray(call.lines) ? [...call.lines] : []
    c.tool = call.mcp_tool || null
    c.at = call.at || new Date().toISOString()
    if (call.card_title) c.title = call.card_title
    if (call.slot) c.slot = call.slot
  }
}

function setCardRunning(cardId) {
  const c = cards[cardId]
  if (!c) return
  c.status = 'running'
  c.lines = ['处理中…']
}

function resetCards() {
  for (const c of Object.values(cards)) {
    c.status = 'idle'
    c.lines = []
    c.tool = null
    c.at = null
  }
}

async function loadMcpCardsFromApi() {
  try {
    const data = await secretaryApi.mcpCards()
    const defs = data?.cards || data
    if (Array.isArray(defs) && defs.length) {
      for (const d of defs) ensureCard(d)
    }
  } catch (_) {
    /* 使用本地默认 */
  }
}

function _cardForSlot(slot) {
  return Object.values(cards).find((c) => c.slot === slot) || null
}

const cornerCards = computed(() => ({
  lt: _cardForSlot('lt'),
  lb: _cardForSlot('lb'),
  rt: _cardForSlot('rt'),
  rb: _cardForSlot('rb'),
}))

export function useAgentMcp() {
  return {
    cards,
    cornerCards,
    SLOT_ORDER,
    initFromDefs,
    applyMcpCalls,
    setCardRunning,
    resetCards,
    loadMcpCardsFromApi,
  }
}
