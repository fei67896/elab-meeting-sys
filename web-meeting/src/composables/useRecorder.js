// MediaRecorder + 服务端 Whisper 转写。
// 适用场景: Web Speech API 在 Edge / 大陆网络环境下不可用时的备用方案。
//
// 行为:
// - start(): 请求麦克风 + 启动 MediaRecorder, 录到内存 Blob。
// - stop(): 停止录音, 自动 POST 到 /api/transcribe 拿文字。
// - transcript: 后端返回的最终文本 (一次性, 不分段)。
// - isRecording / isUploading: UI 状态。
import { ref, onBeforeUnmount } from 'vue'
import client from '../api/client'

export function useRecorder() {
  const isRecording = ref(false)
  const isUploading = ref(false)
  const transcript = ref('')
  const errorMsg = ref('')

  let stream = null
  let recorder = null
  let chunks = []

  // 挑一个浏览器普遍支持的 MIME。Whisper 用 ffmpeg 解码, 通常能吃 webm/opus
  function pickMime() {
    const list = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/ogg;codecs=opus',
      'audio/mp4',
    ]
    for (const m of list) {
      if (window.MediaRecorder && MediaRecorder.isTypeSupported(m)) return m
    }
    return ''
  }

  async function start() {
    if (isRecording.value || isUploading.value) return
    errorMsg.value = ''
    transcript.value = ''
    chunks = []

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      errorMsg.value = 'getUserMedia 不可用 (需要 HTTPS 或新浏览器)'
      throw new Error(errorMsg.value)
    }
    if (!window.MediaRecorder) {
      errorMsg.value = '当前浏览器不支持 MediaRecorder'
      throw new Error(errorMsg.value)
    }

    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          channelCount: 1,
          sampleRate: 16000,
        },
        video: false,
      })
      const mime = pickMime()
      recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined)
      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunks.push(e.data)
      }
      recorder.start(250) // 每 250ms 给一次 chunk, 便于尽早 flush
      isRecording.value = true
      console.log('[recorder] start mime=', recorder.mimeType)
    } catch (e) {
      const code = e && e.name
      const map = {
        NotAllowedError: '麦克风权限被拒绝',
        NotFoundError: '没有找到麦克风设备',
        NotReadableError: '麦克风被其他程序占用',
      }
      errorMsg.value = map[code] || (e.message || String(e))
      _cleanup()
      throw e
    }
  }

  function _cleanup() {
    if (stream) {
      try { stream.getTracks().forEach((t) => t.stop()) } catch (_) {}
    }
    stream = null
    recorder = null
    isRecording.value = false
  }

  // 停止录音, 等所有 chunk 就绪后, POST 到 /api/transcribe
  function stop() {
    return new Promise((resolve, reject) => {
      if (!isRecording.value || !recorder) {
        return resolve('')
      }
      recorder.onstop = async () => {
        const blob = new Blob(chunks, { type: recorder?.mimeType || 'audio/webm' })
        console.log('[recorder] stopped, blob size=', blob.size)
        _cleanup()
        if (blob.size === 0) {
          errorMsg.value = '没有录到声音'
          return reject(new Error(errorMsg.value))
        }

        // 上传给后端转写
        isUploading.value = true
        try {
          const fd = new FormData()
          fd.append('file', blob, 'audio.webm')
          const data = await client.post('/api/transcribe', fd, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 60000,
          })
          const text = (data && data.text) || ''
          transcript.value = text
          console.log('[recorder] transcribed:', text)
          resolve(text)
        } catch (err) {
          errorMsg.value = err.message || '转写失败'
          reject(err)
        } finally {
          isUploading.value = false
        }
      }
      try { recorder.stop() } catch (_) {}
    })
  }

  function cancel() {
    if (recorder) {
      recorder.onstop = null
      try { recorder.stop() } catch (_) {}
    }
    _cleanup()
    isUploading.value = false
    transcript.value = ''
  }

  onBeforeUnmount(cancel)

  return {
    isRecording,
    isUploading,
    transcript,
    errorMsg,
    start,
    stop,
    cancel,
  }
}
