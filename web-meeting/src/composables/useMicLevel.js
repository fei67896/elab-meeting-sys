// 麦克风音量监测 (0..1)。
// 用 getUserMedia + AnalyserNode 实时计算 RMS, 供 UI 画音量条。
// 浏览器会复用 SpeechRecognition 已经请求过的麦克风权限, 不会再弹窗。
import { ref, onBeforeUnmount } from 'vue'

export function useMicLevel() {
  const level = ref(0)          // 0..1
  const isActive = ref(false)
  const errorMsg = ref('')

  let stream = null
  let audioCtx = null
  let analyser = null
  let rafId = 0

  const start = async () => {
    if (isActive.value) return
    console.log('[mic-level] start()')

    // 基础环境检查 (HTTP / 老浏览器会缺这个 API)
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      errorMsg.value = 'navigator.mediaDevices.getUserMedia 不可用 (需要 HTTPS 或较新浏览器)'
      console.warn('[mic-level]', errorMsg.value)
      throw new Error(errorMsg.value)
    }

    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true },
        video: false,
      })
      console.log('[mic-level] got stream', stream)
      const Ctx = window.AudioContext || window.webkitAudioContext
      if (!Ctx) {
        errorMsg.value = 'AudioContext 不可用'
        throw new Error(errorMsg.value)
      }
      audioCtx = new Ctx()
      // 部分浏览器 autoplay policy 下需要 resume
      if (audioCtx.state === 'suspended') {
        try { await audioCtx.resume() } catch (_) {}
      }
      const source = audioCtx.createMediaStreamSource(stream)
      analyser = audioCtx.createAnalyser()
      analyser.fftSize = 1024
      analyser.smoothingTimeConstant = 0.6
      source.connect(analyser)

      const buf = new Float32Array(analyser.fftSize)
      const loop = () => {
        if (!analyser) return
        analyser.getFloatTimeDomainData(buf)
        let sum = 0
        for (let i = 0; i < buf.length; i++) sum += buf[i] * buf[i]
        const rms = Math.sqrt(sum / buf.length)
        // 经验校准: rms 通常在 0~0.3, 放大并 clamp
        level.value = Math.min(1, rms * 5)
        rafId = requestAnimationFrame(loop)
      }
      isActive.value = true
      errorMsg.value = ''
      console.log('[mic-level] active, fftSize=', analyser.fftSize)
      loop()
    } catch (e) {
      const code = e && e.name
      const map = {
        NotAllowedError: '麦克风权限被拒绝',
        NotFoundError: '没有找到麦克风设备',
        NotReadableError: '麦克风被其他程序占用',
        OverconstrainedError: '麦克风约束无法满足',
        SecurityError: '安全策略阻止访问 (检查 HTTPS)',
      }
      errorMsg.value = map[code] || (e.message || String(e))
      console.warn('[mic-level] failed:', code, e)
      throw e
    }
  }

  const stop = () => {
    if (rafId) cancelAnimationFrame(rafId)
    rafId = 0
    if (analyser) try { analyser.disconnect() } catch (_) {}
    analyser = null
    if (audioCtx) try { audioCtx.close() } catch (_) {}
    audioCtx = null
    if (stream) {
      stream.getTracks().forEach((t) => { try { t.stop() } catch (_) {} })
    }
    stream = null
    isActive.value = false
    level.value = 0
  }

  onBeforeUnmount(stop)

  return { level, isActive, errorMsg, start, stop }
}
