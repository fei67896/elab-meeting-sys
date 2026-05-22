import { ref } from 'vue'

/**
 * WebRTC 数字人 <video> 音频解锁（浏览器自动播放策略需用户手势）。
 */
export function useAvatarVideoAudio(videoRef) {
  const muted = ref(true)
  const needsUnmute = ref(false)

  function checkAudioState() {
    const v = videoRef.value
    if (!v) {
      needsUnmute.value = muted.value
      return
    }
    // play() 可能成功但元素仍被静音
    needsUnmute.value = v.muted || muted.value
  }

  async function unmute() {
    const v = videoRef.value
    if (!v) return false
    muted.value = false
    v.muted = false
    v.volume = 1
    try {
      await v.play()
    } catch (e) {
      console.warn('[avatar-audio] play failed', e)
    }
    checkAudioState()
    return !needsUnmute.value
  }

  function scheduleAutoUnmute(delayMs = 400) {
    setTimeout(() => {
      unmute()
      checkAudioState()
    }, delayMs)
  }

  return { muted, needsUnmute, unmute, checkAudioState, scheduleAutoUnmute }
}
