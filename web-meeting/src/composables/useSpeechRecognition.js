// 浏览器语音识别封装 (Web Speech API)。
//
// 设计要点 (针对 Chrome 中文识别的实际行为):
// - 强制 recognition.continuous = false: 单句模式下 Chrome 的 zh-CN 才会
//   稳定地推送 interimResults; continuous=true 时几乎只有 final 出来。
// - 对外通过 shouldContinue 在 onend 里自动 restart, 给上层"持续监听"的体验。
// - 直接维护 finalText + interim 拼接出来的 transcript ref, 上层只用监听一个 ref,
//   避免分别处理 onInterim/onFinal 导致的闪烁。
import { ref } from 'vue'

export function useSpeechRecognition(options = {}) {
  const {
    onChange = () => {},     // (text, {isFinal}) => void
    onError = () => {},
    onStart = () => {},
    onEnd = () => {},
    language = 'zh-CN',
    continuous = true,       // 对外语义: 是否在每句结束后自动接着听
  } = options

  const isSupported = ref(
    'webkitSpeechRecognition' in window || 'SpeechRecognition' in window
  )
  const isRecording = ref(false)
  const transcript = ref('')   // finalText + 当前 interim

  let recognition = null
  let shouldContinue = false
  let finalText = ''           // 已 finalize 的累计文本
  // _starting 是同步状态机, 用来挡掉 "recognition has already started" 的竞态。
  // recognition.start() 是同步调用, 但 onstart/onend 是异步触发, 中间用户连续点击会撞车。
  let _starting = false

  if (isSupported.value) {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    recognition = new SR()
    // 关键: 中文场景下 continuous=false 时 Chrome 才会稳定发送 interim 结果
    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = language

    recognition.onstart = () => {
      _starting = false
      isRecording.value = true
      onStart()
    }

    recognition.onresult = (event) => {
      // 把本次事件里 resultIndex 之后所有 result 重新解析
      // 把 isFinal=true 的拼到 finalText, 其余作为当前 interim
      let interim = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const text = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalText = (finalText + text).replace(/\s+/g, '')
        } else {
          interim += text
        }
      }
      transcript.value = (finalText + interim).trimStart()
      onChange(transcript.value, { isFinal: interim.length === 0 })
    }

    recognition.onerror = (event) => {
      if (event.error === 'no-speech' && shouldContinue) return
      const hard = ['not-allowed', 'service-not-allowed', 'audio-capture', 'network']
      if (hard.includes(event.error)) {
        shouldContinue = false
      }
      onError(event.error)
    }

    recognition.onend = () => {
      _starting = false
      isRecording.value = false
      if (shouldContinue) {
        // 短暂延迟后立刻 restart, 让用户感受像"一直在听"
        setTimeout(() => {
          if (shouldContinue && !isRecording.value && !_starting) {
            _starting = true
            try {
              recognition.start()
            } catch (_) {
              _starting = false
            }
          }
        }, 80)
      } else {
        onEnd()
      }
    }
  }

  const start = () => {
    if (!recognition || isRecording.value || _starting) return
    // 开新一段录音: 清空累计文本
    finalText = ''
    transcript.value = ''
    shouldContinue = !!continuous
    _starting = true
    try {
      recognition.start()
    } catch (err) {
      const msg = err && (err.message || String(err))
      _starting = false
      // start/stop 切换时 Chrome 偶发抛 "already started", 静默吞掉避免 UI 报错
      if (msg && /already started/i.test(msg)) return
      onError(msg || 'start failed')
    }
  }

  const stop = () => {
    if (!recognition) return
    shouldContinue = false
    try { recognition.stop() } catch (_) {}
  }

  const reset = () => {
    finalText = ''
    transcript.value = ''
  }

  return {
    isSupported,
    isRecording,
    transcript,
    start,
    stop,
    reset,
  }
}
