import { ref } from 'vue'

/** 根据 <video> 实际分辨率收紧外框，避免 contain 左右留白 */
export function useAvatarFrameAspect(videoRef) {
  const frameAspect = ref(null)

  function onVideoMetadata() {
    const v = videoRef.value
    if (!v?.videoWidth || !v?.videoHeight) return
    frameAspect.value = `${v.videoWidth} / ${v.videoHeight}`
  }

  function frameStyle(fallback = 'var(--avatar-aspect)') {
    return {
      aspectRatio: frameAspect.value || fallback,
      width: '100%',
      maxHeight: '100dvh',
      height: 'auto',
    }
  }

  return { frameAspect, onVideoMetadata, frameStyle }
}
