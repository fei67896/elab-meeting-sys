/** 专注度折线 SVG polyline 点串（与 web-meeting StateHistoryPanel 一致） */
export function concPolyline(pts, width = 400, height = 100) {
  if (!pts?.length) return ''
  const vals = pts.map((p) => Number(p.value ?? p.con_score ?? 0))
  const min = Math.min(...vals)
  const max = Math.max(...vals)
  const span = max - min || 1
  const pad = 6
  return pts
    .map((p, i) => {
      const x = pad + (i / Math.max(pts.length - 1, 1)) * (width - pad * 2)
      const y = height - pad - ((Number(p.value ?? p.con_score ?? 0) - min) / span) * (height - pad * 2)
      return `${x},${y}`
    })
    .join(' ')
}

/** 多参会人专注度曲线取平均（用于会议级迷你图） */
export function aggregateConcentrationPoints(participants) {
  const series = (participants || [])
    .map((p) => p.concentration?.points || [])
    .filter((pts) => pts.length > 0)
  if (!series.length) {
    const avgs = (participants || [])
      .map((p) => p.concentration?.summary?.avg)
      .filter((v) => v != null && !Number.isNaN(Number(v)))
    if (!avgs.length) return []
    const mean = avgs.reduce((a, b) => a + Number(b), 0) / avgs.length
    return Array.from({ length: 20 }, (_, i) => ({ value: mean, i }))
  }
  const len = Math.min(
    80,
    Math.max(...series.map((s) => s.length)),
  )
  const out = []
  for (let i = 0; i < len; i += 1) {
    let sum = 0
    let n = 0
    for (const s of series) {
      const idx = Math.floor((i / Math.max(len - 1, 1)) * (s.length - 1))
      const v = Number(s[idx]?.value ?? s[idx]?.con_score)
      if (!Number.isNaN(v)) {
        sum += v
        n += 1
      }
    }
    if (n) out.push({ value: sum / n })
  }
  return out
}
