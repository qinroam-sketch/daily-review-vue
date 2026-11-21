<script setup>
import { computed, onMounted, ref } from 'vue'
import { loadManifest } from '../lib/loadDay.js'
import { pct, pctCls, rate, md } from '../lib/format.js'
import SentimentTag from '../components/SentimentTag.vue'
import Disclaimer from '../components/Disclaimer.vue'

const loading = ref(true)
const error = ref('')
const manifest = ref({ days: [] })

onMounted(async () => {
  try {
    manifest.value = await loadManifest()
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
})

const days = computed(() => manifest.value.days || [])

const months = computed(() => {
  const map = new Map()
  for (const d of days.value) {
    const key = d.date.slice(0, 7)
    if (!map.has(key)) map.set(key, [])
    map.get(key).push(d)
  }
  return [...map.entries()].sort((a, b) => (a[0] < b[0] ? 1 : -1))
})

function calendarWeeks(month, monthDays) {
  const [y, m] = month.split('-').map(Number)
  const first = new Date(y, m - 1, 1)
  const lastDate = new Date(y, m, 0).getDate()
  const startPad = (first.getDay() + 6) % 7 // Monday first
  const byDate = Object.fromEntries(monthDays.map((d) => [d.date, d]))
  const cells = []
  for (let i = 0; i < startPad; i++) cells.push(null)
  for (let day = 1; day <= lastDate; day++) {
    const iso = `${month}-${String(day).padStart(2, '0')}`
    cells.push({ day, iso, rec: byDate[iso] || null })
  }
  const weeks = []
  for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7))
  while (weeks[weeks.length - 1].length < 7) weeks[weeks.length - 1].push(null)
  return weeks
}

function shPct(rec) {
  return rec?.indices?.['上证指数']
}
function monthTitle(ym) {
  const [y, m] = ym.split('-')
  return `${y}年${Number(m)}月`
}
</script>

<template>
  <main class="page">
    <h1 class="page-title">交易日目录</h1>
    <p class="page-sub">
      选择一天查看完整复盘。新增一天只需放入数据文件并更新目录，不用改页面代码。
      <span v-if="manifest.updated">目录更新于 {{ manifest.updated }}（香港时间）。</span>
    </p>

    <div v-if="loading" class="loading">正在读取交易日目录…</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <template v-else>
      <section v-for="[ym, list] in months" :key="ym" class="section">
        <h2><span class="idx">历</span>{{ monthTitle(ym) }}</h2>
        <table class="cal">
          <thead>
            <tr>
              <th v-for="w in ['一','二','三','四','五','六','日']" :key="w">{{ w }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(week, wi) in calendarWeeks(ym, list)" :key="wi">
              <td v-for="(cell, ci) in week" :key="ci" :class="{ empty: !cell, on: cell && cell.rec }">
                <template v-if="cell">
                  <router-link v-if="cell.rec" :to="`/day/${cell.rec.date}`">
                    <div class="n">{{ cell.day }}</div>
                    <div class="mini" :class="pctCls(shPct(cell.rec))">{{ pct(shPct(cell.rec), 2) }}</div>
                  </router-link>
                  <div v-else class="n">{{ cell.day }}</div>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <h2 class="page-sub" style="margin-top:8px;font-size:15px;color:var(--text)">全部已收录交易日</h2>
      <div class="cards">
        <router-link v-for="d in days" :key="d.date" class="day-card" :to="`/day/${d.date}`">
          <div>
            <span class="d">{{ d.date }}</span>
            <span class="w">星期{{ d.weekday }}</span>
          </div>
          <div class="idx-row">
            <span><b>沪</b><span :class="pctCls(d.indices?.['上证指数'])">{{ pct(d.indices?.['上证指数']) }}</span></span>
            <span><b>创</b><span :class="pctCls(d.indices?.['创业板指'])">{{ pct(d.indices?.['创业板指']) }}</span></span>
            <span><b>科创</b><span :class="pctCls(d.indices?.['科创50'])">{{ pct(d.indices?.['科创50']) }}</span></span>
          </div>
          <div class="meta">
            <span>涨停 {{ d.lu_nonst ?? '—' }}</span>
            <span>跌停 {{ d.ld ?? '—' }}</span>
            <span>封板率 {{ rate(d.seal_rate, 1) }}</span>
            <SentimentTag :tag="d.sentiment" />
            <span v-if="d.top_theme" class="tag tag-red">{{ d.top_theme }}</span>
          </div>
          <div v-if="d.headline" class="hl">{{ d.headline }}</div>
        </router-link>
      </div>
      <p v-if="!days.length" class="src">目录里还没有交易日。请先运行 python3 scripts/export_day.py YYYY-MM-DD。</p>
    </template>
    <Disclaimer extra="红涨绿跌。本页数字来自已导出的每日数据文件。" />
  </main>
</template>
