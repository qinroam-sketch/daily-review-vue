export function isNil(v) {
  return v === null || v === undefined || (typeof v === 'number' && Number.isNaN(v))
}

export function pct(v, digits = 2) {
  if (isNil(v)) return '—'
  const n = Number(v)
  if (Number.isNaN(n)) return '—'
  const sign = n > 0 ? '+' : n < 0 ? '' : ''
  return `${sign}${n.toFixed(digits)}%`
}

export function pctCls(v) {
  if (isNil(v) || Number(v) === 0) return 'flat'
  return Number(v) > 0 ? 'up' : 'dn'
}

/** 金额（元）→ 亿元 */
export function yi(v, digits = 2) {
  if (isNil(v)) return '—'
  const n = Number(v) / 1e8
  const abs = Math.abs(n)
  const body = abs.toLocaleString('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
  return `${n < 0 ? '-' : ''}${body}亿`
}

export function rate(v, digits = 0) {
  if (isNil(v)) return '—'
  return `${(Number(v) * 100).toFixed(digits)}%`
}

export function num(v, digits = 0) {
  if (isNil(v)) return '—'
  return Number(v).toLocaleString('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

export function closePrice(v) {
  if (isNil(v)) return '—'
  return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export function md(date) {
  if (!date) return '—'
  return String(date).slice(5)
}

export function shortDate(date) {
  return md(date)
}

const WEEK = { 一: '星期一', 二: '星期二', 三: '星期三', 四: '星期四', 五: '星期五', 六: '星期六', 日: '星期日' }

export function weekdayFull(w) {
  if (!w) return ''
  if (String(w).startsWith('星期')) return w
  return WEEK[w] || w
}

export function codeName(row) {
  if (!row) return ''
  const name = row.name || ''
  const code = row.code || row.ticker || ''
  return code ? `${name} ${code}` : name
}

export function joinNames(arr, limit = 20) {
  if (!arr || !arr.length) return '—'
  const names = arr.map((x) => (typeof x === 'string' ? x : x.name)).filter(Boolean)
  if (names.length <= limit) return names.join('、')
  return names.slice(0, limit).join('、') + ` 等${names.length}只`
}
