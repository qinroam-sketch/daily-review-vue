const BASE = import.meta.env.BASE_URL || './'

export function dataUrl(path) {
  const p = path.startsWith('/') ? path.slice(1) : path
  return `${BASE}${p}`
}

export async function loadManifest() {
  const r = await fetch(dataUrl('data/manifest.json'), { cache: 'no-cache' })
  if (!r.ok) throw new Error('无法读取交易日目录（manifest.json）')
  const man = await r.json()
  const days = (man.days || []).filter((d) => d && d.date && !String(d.date).startsWith('_') && !String(d.date).includes('YYYY'))
  days.sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0))
  return { ...man, days }
}

export async function loadDay(date) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    throw new Error('日期格式不正确')
  }
  const r = await fetch(dataUrl(`data/days/${date}.json`), { cache: 'no-cache' })
  if (r.status === 404) throw new Error(`没有 ${date} 的复盘数据`)
  if (!r.ok) throw new Error(`读取 ${date} 失败（${r.status}）`)
  return r.json()
}

export function neighbors(days, date) {
  const list = [...(days || [])].sort((a, b) => (a.date < b.date ? -1 : 1))
  const i = list.findIndex((d) => d.date === date)
  if (i < 0) return { prev: null, next: null }
  return {
    prev: i > 0 ? list[i - 1] : null,
    next: i < list.length - 1 ? list[i + 1] : null,
  }
}
