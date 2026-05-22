// 单例 WebRTC 连接 (全局共享)
//
// 设计目标:
//   - 应用启动时建立一次 PC 连接, 之后路由切换 (工作台 / 移动秘书 / 设置)
//     都共享同一个 RTCPeerConnection + sessionId + MediaStream
//   - 各页面组件只负责: 把 sharedStream 附着到自己的 <video>, 卸载时 detach
//   - 数字人 TTS 播报不被路由切换打断
//
// API:
//   const { connectionState, sessionId, sharedStream,
//           startPlay, stopPlay, attachVideo } = useWebRTC()
//
//   attachVideo(videoRef)  // 组件 onMounted 调一次, 返回 detach 函数; 通常配合
//                          // onBeforeUnmount(() => detach()) 使用
//
// 注意: 只有调用 stopPlay() 才会真正关掉 PC; 组件卸载只解除附着, 不关连接.
import { ref, watch } from 'vue'

const sessionId = ref(0)
const connectionState = ref('idle') // idle | connecting | connected | failed | closed
const sharedStream = ref(null)       // 当前接收到的 MediaStream
const attachedVideos = new Set()     // 当前已 attach 的 <video> 元素

let pc = null
let pendingConnect = null            // 防止并发 startPlay

function setState(s) { connectionState.value = s }

// 给所有已 attach 的 <video> 重新设置 srcObject
function broadcastStream(stream) {
  sharedStream.value = stream
  for (const v of attachedVideos) {
    try {
      if (v.srcObject !== stream) v.srcObject = stream
    } catch (_) {}
  }
}

async function _doConnect(stunServer) {
  setState('connecting')
  try {
    const configuration = { iceServers: [] }
    if (stunServer) configuration.iceServers.push({ urls: stunServer })

    pc = new RTCPeerConnection(configuration)

    pc.ontrack = (event) => {
      if (event.streams && event.streams[0]) {
        broadcastStream(event.streams[0])
      }
    }

    pc.onconnectionstatechange = () => {
      if (!pc) return
      const cs = pc.connectionState
      if (cs === 'connected') setState('connected')
      else if (cs === 'failed' || cs === 'disconnected') setState('failed')
      else if (cs === 'closed') setState('closed')
    }

    pc.addTransceiver('audio', { direction: 'recvonly' })
    pc.addTransceiver('video', { direction: 'recvonly' })

    const offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    const resp = await fetch('/offer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sdp: pc.localDescription.sdp,
        type: pc.localDescription.type,
      }),
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)

    const data = await resp.json()
    sessionId.value = data.sessionid

    await pc.setRemoteDescription(
      new RTCSessionDescription({ sdp: data.sdp, type: data.type })
    )
    return data.sessionid
  } catch (err) {
    console.error('[WebRTC] 连接失败', err)
    setState('failed')
    if (pc) {
      try { pc.close() } catch (_) {}
      pc = null
    }
    sharedStream.value = null
    throw err
  }
}

async function startPlay(stunServer = 'stun:stun.miwifi.com:3478') {
  // 已经连上或正在连 → 复用
  if (connectionState.value === 'connected' && pc) {
    return sessionId.value
  }
  if (pendingConnect) return pendingConnect
  // 旧 PC 可能在 failed 状态, 先清掉
  if (pc) {
    try { pc.close() } catch (_) {}
    pc = null
  }
  pendingConnect = _doConnect(stunServer).finally(() => {
    pendingConnect = null
  })
  return pendingConnect
}

function stopPlay() {
  if (pc) {
    try { pc.close() } catch (_) {}
    pc = null
  }
  // 清掉所有 <video> 的 srcObject
  for (const v of attachedVideos) {
    try { v.srcObject = null } catch (_) {}
  }
  sharedStream.value = null
  sessionId.value = 0
  setState('closed')
}

// 把一个 <video> 元素附着到共享流; 返回 detach 函数
function attachVideo(videoRef) {
  // videoRef 可以是 ref 或 DOM 元素
  const getEl = () =>
    videoRef && 'value' in videoRef ? videoRef.value : videoRef

  const apply = () => {
    const el = getEl()
    if (!el) return
    attachedVideos.add(el)
    if (sharedStream.value && el.srcObject !== sharedStream.value) {
      el.srcObject = sharedStream.value
    }
  }

  // 立即尝试一次
  apply()

  // 如果 videoRef 是 ref, 监听其变化 (元素延迟挂载)
  let stopWatch = null
  if (videoRef && 'value' in videoRef) {
    stopWatch = watch(videoRef, apply, { immediate: false })
  }

  return function detach() {
    const el = getEl()
    if (el) {
      attachedVideos.delete(el)
      try { el.srcObject = null } catch (_) {}
    }
    if (stopWatch) stopWatch()
  }
}

export function useWebRTC() {
  return {
    sessionId,
    connectionState,
    sharedStream,
    startPlay,
    stopPlay,
    attachVideo,
  }
}
