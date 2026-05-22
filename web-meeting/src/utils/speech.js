/**
 * 是否适合使用浏览器 Web Speech API。
 *
 * Edge (Chromium) 虽暴露 SpeechRecognition, 但识别走微软云端,
 * 大陆网络下 frequent 报 network / 无结果, 应改用服务端 Whisper。
 * Chrome 本地/云端相对稳定, 中文 interim 体验更好。
 */
export function canUseBrowserSpeech() {
  if (typeof window === 'undefined') return false

  const hasApi =
    'webkitSpeechRecognition' in window || 'SpeechRecognition' in window
  if (!hasApi) return false

  const ua = navigator.userAgent || ''
  if (/Edg\//i.test(ua)) return false

  return true
}

export function speechEngineLabel() {
  return canUseBrowserSpeech()
    ? '浏览器语音识别 (Chrome 推荐)'
    : '服务端 Whisper (Edge / 备用)'
}
