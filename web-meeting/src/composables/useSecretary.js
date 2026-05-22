// 会议秘书的全局状态 (单例)。
// - messages: 聊天消息时间线 (user / secretary / system)
// - lastResult: 上一次 LLM 解析+执行结果，供 CommandResultCard 展示
// - status: 当前状态机文案
// - sendCommand(text): 主入口，发送指令到后端
// - secretary 消息的文字会等数字人开始播报后再"逐字"显示，与 TTS 节奏同步
import { reactive, readonly, ref } from 'vue'
import { secretaryApi, avatarApi } from '../api/meeting'
import client from '../api/client'
import { useWebRTC } from './useWebRTC'

const messages = reactive([])
const lastResult = ref(null)
const status = ref('idle') // idle | thinking | speaking | error
const currentMeetingId = ref(null)

// sessionId 直接复用 WebRTC 的全局 ref, 保证两边永远同步
const { sessionId: _rtcSessionId } = useWebRTC()
const sessionId = _rtcSessionId
let _seq = 0

function pushMessage(role, content, extra = {}) {
  _seq += 1
  messages.push({
    id: _seq,
    role,
    content,
    ts: new Date().toISOString(),
    ...extra,
  })
  // 返回 reactive 代理本身, 后续 mutate 才能触发 UI 更新
  return messages[messages.length - 1]
}

async function _isSpeakingRemote(sid) {
  try {
    const data = await client.post('/is_speaking', { sessionid: sid })
    // /is_speaking 不走 /api/* 包装, 返回的是 axios 后被拦截器透传的 data
    // 后端格式: { code:0, data: boolean } -> client 拦截器把 data 直接返回
    return data === true
  } catch (_) {
    return false
  }
}

// 等数字人开口, 然后按 TTS 节奏 (~180ms/字) 逐字显示 msg.content。
// 期间偶尔轮询; 一旦数字人说完, 立刻补全剩余文字。
async function _typeWithAvatar(msg, fullText, sid) {
  if (!fullText) return

  // 等开口, 最多 4s; 没等到就直接出字
  const t0 = Date.now()
  let speaking = false
  while (Date.now() - t0 < 4000) {
    if (await _isSpeakingRemote(sid)) { speaking = true; break }
    await new Promise(r => setTimeout(r, 120))
  }

  if (!speaking) {
    msg.content = fullText
    return
  }

  const charDelay = 180  // 中文 TTS 大致节奏
  for (let i = 1; i <= fullText.length; i++) {
    msg.content = fullText.slice(0, i)
    // 每 6 字检查一次, 如果数字人停了就直接补满
    if (i % 6 === 0) {
      if (!(await _isSpeakingRemote(sid))) {
        msg.content = fullText
        return
      }
    }
    await new Promise(r => setTimeout(r, charDelay))
  }
  // 文字念完了, 等数字人也念完再退出 speaking 状态
  while (await _isSpeakingRemote(sid)) {
    await new Promise(r => setTimeout(r, 200))
  }
}

async function sendCommand(text, { speak = true, meetingId = undefined } = {}) {
  const trimmed = (text || '').trim()
  if (!trimmed) return null

  pushMessage('user', trimmed)
  status.value = 'thinking'

  try {
    const result = await secretaryApi.command(trimmed, {
      sessionid: sessionId.value,
      speak,
      meetingId: meetingId !== undefined ? meetingId : currentMeetingId.value,
    })
    lastResult.value = result

    const fullReply = result.reply_text || '已处理。'
    // 先 push 空内容, 让气泡占位
    const msg = pushMessage('secretary', speak ? '' : fullReply, {
      intent: result.intent,
      params: result.params,
      result: result.result,
      logId: result.log_id,
    })

    if (speak) {
      status.value = 'speaking'
      // 异步: 等数字人开口 -> 逐字显示
      _typeWithAvatar(msg, fullReply, sessionId.value).finally(() => {
        msg.content = fullReply   // 兜底, 确保最终一定是完整文本
        status.value = 'idle'
      })
    }
    return result
  } catch (err) {
    status.value = 'error'
    pushMessage('system', `指令处理失败: ${err.message || err}`, { isError: true })
    setTimeout(() => { if (status.value === 'error') status.value = 'idle' }, 2000)
    throw err
  }
}

function setSessionId(id) {
  // 兼容旧调用: 只在 WebRTC 还没把值设进来时手动同步
  if (id && !sessionId.value) sessionId.value = id
}

function setCurrentMeetingId(id) {
  currentMeetingId.value = id == null ? null : Number(id)
}

function clearMessages() {
  messages.splice(0, messages.length)
  lastResult.value = null
}

export function useSecretary() {
  return {
    messages: readonly(messages),
    lastResult,
    status,
    sessionId,
    currentMeetingId,
    setSessionId,
    setCurrentMeetingId,
    pushMessage,
    sendCommand,
    clearMessages,
  }
}
