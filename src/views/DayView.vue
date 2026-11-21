<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { loadDay, loadManifest, neighbors } from '../lib/loadDay.js'
import { pct, pctCls, yi, rate, num, closePrice, md, joinNames, isNil } from '../lib/format.js'
import { C, FONT, textStyle, tooltipBase, categoryAxis, valueAxis } from '../lib/charts.js'
import PctNum from '../components/PctNum.vue'
import SentimentTag from '../components/SentimentTag.vue'
import SafeHtml from '../components/SafeHtml.vue'
import NoteBlock from '../components/NoteBlock.vue'
import SourceLine from '../components/SourceLine.vue'
import Disclaimer from '../components/Disclaimer.vue'
import ChartPanel from '../components/ChartPanel.vue'
import DataTable from '../components/DataTable.vue'

const route = useRoute()
const loading = ref(true)
const error = ref('')
const day = ref(null)
const navs = ref({ prev: null, next: null })

const SECTIONS = [
  { id: 'market', label: '大盘概况' },
  { id: 'ladder', label: '涨停梯队' },
  { id: 'themes', label: '题材板块' },
  { id: 'loss', label: '跌停与亏钱效应' },
  { id: 'lhb', label: '龙虎榜解读' },
  { id: 'cycle', label: '情绪周期' },
  { id: 'next', label: '次日观察要点' },
  { id: 'post', label: '事后验证' },
  { id: 'terms', label: '术语小卡' },
  { id: 'news', label: '消息面' },
  { id: 'gaps', label: '待核' },
]

async function load() {
  loading.value = true
  error.value = ''
  day.value = null
  const date = route.params.date
  try {
    const [doc, man] = await Promise.all([loadDay(date), loadManifest().catch(() => ({ days: [] }))])
    day.value = doc
    navs.value = neighbors(man.days, doc.date)
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(() => route.params.date, load)

const m = computed(() => day.value?.market || {})
const idx = (name) => (m.value.indices || []).find((i) => i.name === name)

const historyChart = computed(() => {
  const hist = day.value?.history || []
  if (!hist.length) return null
  const xs = hist.map((r) => md(r.date))
  return {
    tooltip: tooltipBase(),
    legend: { top: 4, textStyle: textStyle({ color: '#e7edf4' }), itemWidth: 12, itemHeight: 8 },
    grid: { left: 48, right: 52, top: 42, bottom: 32 },
    xAxis: categoryAxis(xs),
    yAxis: [
      valueAxis('家数', { min: 0 }),
      valueAxis('', { min: 0, max: 100, axisLabel: textStyle({ fontSize: 11, color: C.axis }), splitLine: { show: false } }),
    ],
    series: [
      { name: '涨停(不含ST)', type: 'bar', data: hist.map((r) => r.lu_nonst), itemStyle: { color: C.up, borderRadius: [2, 2, 0, 0] }, barGap: '20%', barMaxWidth: 16 },
      { name: '跌停', type: 'bar', data: hist.map((r) => r.ld), itemStyle: { color: C.down, borderRadius: [2, 2, 0, 0] }, barMaxWidth: 16 },
      { name: '封板率%', type: 'line', yAxisIndex: 1, data: hist.map((r) => (isNil(r.seal_rate) ? null : +(r.seal_rate * 100).toFixed(1))), smooth: false, symbol: 'circle', symbolSize: 7, itemStyle: { color: C.blue }, lineStyle: { width: 2 } },
      { name: '空间板(板)', type: 'line', yAxisIndex: 1, data: hist.map((r) => r.height), symbol: 'diamond', symbolSize: 8, itemStyle: { color: C.gold }, lineStyle: { width: 2, type: 'dashed' }, label: { show: true, position: 'top', color: C.gold, fontFamily: FONT, fontSize: 10 } },
    ],
  }
})

const breadthChart = computed(() => {
  const up = m.value.up, down = m.value.down, flat = m.value.flat
  if (up == null) return null
  return {
    tooltip: { ...tooltipBase(), trigger: 'item' },
    grid: { left: 16, right: 16, top: 24, bottom: 28, containLabel: true },
    xAxis: { type: 'value', axisLabel: textStyle({ fontSize: 11, color: C.axis }), splitLine: { lineStyle: { color: 'rgba(36,48,64,0.7)', type: 'dashed' } }, axisLine: { show: false }, axisTick: { show: false } },
    yAxis: categoryAxis(['涨跌家数（沪深日K）']),
    series: [
      { type: 'bar', stack: 'b', name: '上涨', data: [up], itemStyle: { color: C.up }, barWidth: 22, label: { show: true, formatter: `${up} 涨`, color: '#fff', fontFamily: FONT, fontSize: 11 } },
      { type: 'bar', stack: 'b', name: '平盘', data: [flat], itemStyle: { color: '#5a6570' }, label: { show: true, formatter: `${flat} 平`, color: '#fff', fontFamily: FONT, fontSize: 10 } },
      { type: 'bar', stack: 'b', name: '下跌', data: [down], itemStyle: { color: C.down }, label: { show: true, formatter: `${down} 跌`, color: '#fff', fontFamily: FONT, fontSize: 11 } },
    ],
  }
})

const ladderChart = computed(() => {
  const boards = [...(day.value?.ladder?.boards || [])].sort((a, b) => a.level - b.level)
  if (!boards.length) return null
  return {
    tooltip: tooltipBase(),
    grid: { left: 56, right: 36, top: 16, bottom: 24 },
    xAxis: valueAxis('家数', { minInterval: 1 }),
    yAxis: categoryAxis(boards.map((b) => `${b.level}板`)),
    series: [{
      type: 'bar',
      data: boards.map((b) => ({
        value: b.count,
        itemStyle: { color: b.level === 1 ? 'rgba(246,70,93,0.45)' : C.up, borderRadius: [0, 4, 4, 0] },
      })),
      barWidth: 16,
      label: { show: true, position: 'right', color: C.text, fontFamily: FONT, fontSize: 11 },
    }],
  }
})

const themeBarChart = computed(() => {
  const dist = [...(day.value?.themes?.distribution || [])].sort((a, b) => a.n - b.n)
  if (!dist.length) return null
  const highlight = day.value?.highlight_theme
  return {
    tooltip: tooltipBase(),
    grid: { left: 110, right: 36, top: 8, bottom: 24 },
    xAxis: valueAxis('家数（可重叠）', { minInterval: 1 }),
    yAxis: categoryAxis(dist.map((t) => t.name)),
    series: [{
      type: 'bar',
      data: dist.map((t) => ({
        value: t.n,
        itemStyle: { color: t.name === highlight ? C.up : (t.n >= 10 ? C.orange : '#5a6a7a'), borderRadius: [0, 4, 4, 0] },
      })),
      barWidth: 14,
      label: { show: true, position: 'right', color: C.text, fontFamily: FONT, fontSize: 11 },
    }],
  }
})

const themeTrendChart = computed(() => {
  const top = day.value?.themes?.top || []
  if (!top.length) return null
  const xs = (top[0].trend_dates || []).map(md)
  const palette = [C.up, C.gold, C.blue, '#c084fc', C.down]
  return {
    tooltip: tooltipBase(),
    legend: { top: 0, textStyle: textStyle({ color: '#e7edf4', fontSize: 11 }), itemWidth: 12, itemHeight: 8 },
    grid: { left: 44, right: 20, top: 36, bottom: 28 },
    xAxis: categoryAxis(xs),
    yAxis: valueAxis('涨停数', { minInterval: 1 }),
    series: top.map((t, i) => ({
      name: t.name, type: 'line', data: t.trend, symbol: 'circle', symbolSize: 7,
      itemStyle: { color: palette[i % palette.length] }, lineStyle: { width: 2 },
    })),
  }
})

const histChart = computed(() => {
  const vals = (day.value?.loss?.yesterday_returns || []).filter((v) => !isNil(v))
  if (!vals.length) return null
  const bins = []
  for (let x = -21; x < 23; x += 2) bins.push({ from: x, to: x + 2, n: 0 })
  for (const v of vals) {
    const b = bins.find((x) => v >= x.from && v < x.to) || bins[bins.length - 1]
    b.n += 1
  }
  return {
    tooltip: { ...tooltipBase(), formatter: (p) => `${p.name}<br/>家数 ${p.value}` },
    grid: { left: 44, right: 20, top: 36, bottom: 32 },
    xAxis: categoryAxis(bins.map((b) => `${b.from}`)),
    yAxis: valueAxis('家数', { minInterval: 1 }),
    series: [{
      type: 'bar',
      data: bins.map((b) => ({
        value: b.n,
        itemStyle: { color: b.from >= 0 ? C.up : C.down, opacity: 0.85, borderRadius: [2, 2, 0, 0] },
      })),
      barWidth: 14,
      markLine: {
        symbol: 'none',
        label: { show: false },
        lineStyle: { color: '#e7edf4', width: 1 },
        data: [{ xAxis: bins.findIndex((b) => b.from === 0) }],
      },
    }],
  }
})

const postThemeChart = computed(() => {
  const rows = day.value?.post?.theme_follow || []
  if (!rows.length) return null
  const xs = (rows[0].dates || []).map(md)
  const palette = [C.up, C.gold, C.blue, '#c084fc', C.down]
  return {
    tooltip: tooltipBase(),
    legend: { top: 0, textStyle: textStyle({ color: '#e7edf4', fontSize: 11 }), itemWidth: 12, itemHeight: 8 },
    grid: { left: 44, right: 16, top: 36, bottom: 28 },
    xAxis: categoryAxis(xs),
    yAxis: valueAxis('涨停数', { minInterval: 1 }),
    series: rows.map((t, i) => ({
      name: t.name, type: 'line', data: t.counts, symbol: 'circle', symbolSize: 7,
      itemStyle: { color: palette[i % palette.length] }, lineStyle: { width: 2 },
    })),
  }
})

const lhbThemeChart = computed(() => {
  const rows = [...(day.value?.lhb?.theme_agg || [])].filter((r) => r.theme !== '(未归类)')
  if (!rows.length) return null
  const xs = rows.map((r) => r.theme)
  return {
    tooltip: { ...tooltipBase(), formatter: (p) => `${p.seriesName}<br/>${p.name}：${yi(p.value)}` },
    legend: { top: 0, textStyle: textStyle({ color: '#e7edf4' }), itemWidth: 12, itemHeight: 8 },
    grid: { left: 52, right: 16, top: 36, bottom: 72 },
    xAxis: { ...categoryAxis(xs), axisLabel: { ...textStyle({ fontSize: 10, color: C.axis }), rotate: 30 } },
    yAxis: valueAxis('净买（元）'),
    series: [
      { name: '上涨股净买', type: 'bar', data: rows.map((r) => r.up_net), itemStyle: { color: C.up, borderRadius: [2, 2, 0, 0] }, barMaxWidth: 14 },
      { name: '下跌股净买', type: 'bar', data: rows.map((r) => r.down_net), itemStyle: { color: C.down, borderRadius: [2, 2, 0, 0] }, barMaxWidth: 14 },
    ],
  }
})

function boardNames(b) {
  if (!b.stocks) return ''
  if (b.level === 1) return `${b.count} 只（详见下方题材表，或展开）`
  return joinNames(b.stocks, 40)
}

function promoExtra(p) {
  const bits = []
  if (p.promoted_names?.length && p.from_level > 1) bits.push(p.promoted_names.join('、'))
  if (p.suspended_names?.length) bits.push('停牌：' + p.suspended_names.join('、'))
  return bits.join('；') || '—'
}

function promoRate(p) {
  if (p.tradable === 0) return '—（停牌）'
  return rate(p.rate, 0)
}

function tagClass(tag) {
  if (tag === '合力买') return 'tag tag-red'
  if (tag === '合力卖') return 'tag tag-green'
  if (tag === '分歧') return 'tag tag-gold'
  return 'tag tag-mute'
}

function followCell(d) {
  if (d.status === '停牌' || d.pct === null) return '停牌'
  let t = pct(d.pct, 1)
  if (d.limit_up) t += ' 涨停'
  else if (d.near_limit) t += ' 近涨停*'
  return t
}
function followCls(d) {
  if (d.status === '停牌' || d.pct === null) return 'muted'
  return pctCls(d.pct)
}
function vsText(rel) {
  if (!rel) return '—'
  return `${pct(rel.close_pct, 1)}（最高 ${pct(rel.high_pct, 1)} / 最低 ${pct(rel.low_pct, 1)}）`
}

const idxCols = [
  { key: 'name', label: '指数' },
  { key: 'close', label: '收盘', type: 'num', digits: 2 },
  { key: 'pct', label: '涨跌', type: 'pct' },
  { key: 'turnover', label: '成交额', type: 'yi' },
  { key: 'prev_turnover', label: '前日成交额', type: 'yi' },
]
</script>

<template>
  <main class="page" v-if="loading">
    <div class="loading">正在读取 {{ route.params.date }} 的复盘…</div>
  </main>
  <main class="page" v-else-if="error">
    <div class="error">{{ error }}</div>
    <p class="center"><router-link to="/">返回目录</router-link></p>
  </main>
  <main class="page" v-else-if="day">
    <div class="day-hero">
      <div class="topline">
        <div>
          <h1 class="page-title">A股每日复盘 · {{ day.date }}（{{ day.weekday }}）</h1>
          <p class="page-sub">前一交易日：{{ day.prev }}　红涨绿跌</p>
        </div>
        <div class="pager">
          <router-link v-if="navs.prev" :to="`/day/${navs.prev.date}`">← {{ navs.prev.date }}</router-link>
          <span v-else class="btn disabled">← 上一交易日</span>
          <router-link to="/">目录</router-link>
          <router-link v-if="navs.next" :to="`/day/${navs.next.date}`">{{ navs.next.date }} →</router-link>
          <span v-else class="btn disabled">下一交易日 →</span>
        </div>
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:4px 0 8px">
        <SentimentTag :tag="day.sentiment?.tag" />
        <span v-if="day.highlight_theme" class="tag tag-red">关注 {{ day.highlight_theme }}</span>
        <span v-if="m.height_name" class="tag tag-gold">空间板 {{ m.height }}连板 {{ m.height_name }}</span>
      </div>
      <p class="headline">{{ day.headline }}</p>
      <SafeHtml v-if="day.summary_html" :html="day.summary_html" style="margin-top:10px" />
    </div>

    <nav class="sec-nav">
      <a v-for="s in SECTIONS" :key="s.id" :href="`#${s.id}`">{{ s.label }}</a>
    </nav>

    <!-- 1 大盘 -->
    <section id="market" class="section">
      <h2><span class="idx">1</span>大盘概况</h2>
      <SourceLine :text="m.src" />
      <div class="metrics">
        <div class="metric">
          <div class="k">上证指数</div>
          <div class="v" :class="pctCls(idx('上证指数')?.pct)">{{ pct(idx('上证指数')?.pct) }}</div>
          <div class="s">收盘 {{ closePrice(idx('上证指数')?.close) }}</div>
        </div>
        <div class="metric">
          <div class="k">创业板指</div>
          <div class="v" :class="pctCls(idx('创业板指')?.pct)">{{ pct(idx('创业板指')?.pct) }}</div>
          <div class="s">收盘 {{ closePrice(idx('创业板指')?.close) }}</div>
        </div>
        <div class="metric">
          <div class="k">科创50</div>
          <div class="v" :class="pctCls(idx('科创50')?.pct)">{{ pct(idx('科创50')?.pct) }}</div>
          <div class="s">收盘 {{ closePrice(idx('科创50')?.close) }}</div>
        </div>
        <div class="metric">
          <div class="k">三市成交额</div>
          <div class="v">{{ yi(m.turnover) }}</div>
          <div class="s">较前日 <span :class="pctCls(m.turnover_chg_pct)">{{ pct(m.turnover_chg_pct, 1) }}</span> · 约 {{ num((m.turnover || 0) / 1e8, 0) }} 亿</div>
        </div>
        <div class="metric">
          <div class="k">涨停 / 跌停（不含ST / 含ST跌停）</div>
          <div class="v"><span class="up">{{ m.lu_nonst }}</span> / <span class="dn">{{ m.ld }}</span></div>
          <div class="s">含ST涨停 {{ m.lu_all }} · 前日 {{ m.lu_nonst_prev }} / {{ m.ld_prev }}</div>
        </div>
        <div class="metric">
          <div class="k">封板率（扶摇口径）</div>
          <div class="v">{{ rate(m.seal_rate, 1) }}</div>
          <div class="s">封住 {{ m.sealed }} / 触及 {{ m.touched }} · 前日 {{ rate(m.seal_rate_prev, 1) }}</div>
        </div>
      </div>
      <DataTable :columns="idxCols" :rows="m.indices || []" />
      <dl class="kv">
        <dt>上涨 / 下跌 / 平盘</dt>
        <dd>{{ m.up }} / {{ m.down }} / {{ m.flat }}（沪深日K，共 {{ m.n }} 只；前日 {{ m.up_prev }} / {{ m.down_prev }}）；个股涨幅中位数 <PctNum :value="m.median_pct" /></dd>
        <dt>涨幅≥7% / 跌幅≤-7%</dt>
        <dd>{{ m.big_up }} / {{ m.big_dn }}（前日 {{ m.big_up_prev }} / {{ m.big_dn_prev }}）</dd>
        <dt>涨停（不含ST）/ 含ST</dt>
        <dd>{{ m.lu_nonst }} / {{ m.lu_all }}（前日 {{ m.lu_nonst_prev }} / {{ m.lu_all_prev }}）</dd>
        <dt>炸板</dt>
        <dd>{{ m.br }}（前日 {{ m.br_prev }}）</dd>
        <dt>昨日涨停今日溢价</dt>
        <dd><PctNum :value="m.prem" />，{{ m.prem_up }}/{{ m.prem_n }} 只收红；昨日连板股 <PctNum :value="m.prem_lb" />（{{ m.prem_lb_n }} 只）</dd>
        <dt>空间板</dt>
        <dd>{{ m.height }} 板{{ m.height_name ? ' · ' + m.height_name : '' }}（前日 {{ m.height_prev }} 板）</dd>
      </dl>
      <h4>近{{ day.history?.length }}个交易日情绪指标</h4>
      <ChartPanel v-if="historyChart" :option="historyChart" :height="300" />
      <ChartPanel v-if="breadthChart" :option="breadthChart" :height="140" />
      <DataTable
        :columns="[
          { key: 'date', label: '日期', get: (r) => md(r.date) },
          { key: 'lu_nonst', label: '涨停', type: 'num' },
          { key: 'ld', label: '跌停', type: 'num' },
          { key: 'br', label: '炸板', type: 'num' },
          { key: 'seal_rate', label: '封板率', type: 'rate', digits: 1 },
          { key: 'height', label: '空间板', type: 'num' },
          { key: 'prem', label: '昨涨停溢价', type: 'pct', digits: 1 },
          { key: 'turnover', label: '成交额', type: 'yi' },
        ]"
        :rows="day.history || []"
      />
      <NoteBlock :notes="m.notes" />
    </section>

    <!-- 2 梯队 -->
    <section id="ladder" class="section">
      <h2><span class="idx">2</span>涨停梯队</h2>
      <SourceLine :text="day.ladder?.src" />
      <DataTable
        :columns="[
          { key: 'level', label: '板数', get: (r) => r.level + '板' },
          { key: 'count', label: '家数', type: 'num' },
          { key: 'names', label: '个股（按封板时间）', get: boardNames },
        ]"
        :rows="day.ladder?.boards || []"
      />
      <ChartPanel v-if="ladderChart" :option="ladderChart" :height="240" />
      <details v-if="(day.ladder?.boards || []).some((b) => b.level === 1)">
        <summary>展开：全部首板名单</summary>
        <DataTable
          :columns="[
            { key: 'name', label: '名称' },
            { key: 'code', label: '代码' },
            { key: 'limit_up_time', label: '首封' },
            { key: 'open_times', label: '开板次数', type: 'num' },
            { key: 'seal_money', label: '封单', type: 'yi' },
            { key: 'reason', label: '涨停原因' },
          ]"
          :rows="(day.ladder?.boards || []).find((b) => b.level === 1)?.stocks || []"
        />
      </details>
      <h4>晋级率（昨天→今天）</h4>
      <table class="data" v-if="day.ladder?.promotions?.length">
        <thead>
          <tr>
            <th>档位</th><th class="num">昨日家数</th><th class="num">今日晋级</th><th class="num">可交易</th><th class="num">晋级率</th><th>晋级个股 / 停牌</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in day.ladder.promotions" :key="p.label">
            <td>{{ p.label }}</td>
            <td class="num">{{ p.yesterday }}</td>
            <td class="num">{{ p.promoted }}</td>
            <td class="num">{{ p.tradable }}</td>
            <td class="num">{{ promoRate(p) }}</td>
            <td>{{ promoExtra(p) }}</td>
          </tr>
        </tbody>
      </table>
      <p v-if="day.ladder?.fuyao_page_boards?.length" class="src">
        扶摇统计口径晋级率：{{ day.ladder.fuyao_page_boards.map((b) => `${b.board_level}=${b.stock_count}家/${b.promotion_rate == null ? '—' : rate(b.promotion_rate, 0)}`).join('，') }}（与自算口径可能因ST、停牌略有差异）
      </p>
      <h4>昨日连板股今天断板</h4>
      <DataTable
        :columns="[
          { key: 'name', label: '名称' },
          { key: 'code', label: '代码' },
          { key: 'yesterday_text', label: '昨日' },
          { key: 'pct', label: '今日涨跌', type: 'pct', emptyKey: 'status' },
          { key: 'reason', label: '涨停原因' },
        ]"
        :rows="day.ladder?.broke || []"
        empty="无"
      />
      <NoteBlock :notes="day.ladder?.notes" />
    </section>

    <!-- 3 题材 -->
    <section id="themes" class="section">
      <h2><span class="idx">3</span>题材板块</h2>
      <SourceLine :text="day.themes?.src" />
      <div class="theme-pills">
        <span v-for="t in day.themes?.top || []" :key="t.name" class="theme-pill" :class="{ new: t.status === '新启动' }">
          <strong>{{ t.name }}</strong> {{ t.n }}只 · {{ t.status }}
        </span>
      </div>
      <ChartPanel v-if="themeBarChart" :option="themeBarChart" :height="280" />
      <table class="data" v-if="day.themes?.top?.length">
        <thead>
          <tr>
            <th>题材</th><th class="num">涨停数</th><th>龙头</th><th>中军</th><th>跟风（部分）</th><th>近几日涨停数</th><th>判断</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in day.themes.top" :key="t.name">
            <td><b>{{ t.name }}</b></td>
            <td class="num">{{ t.n }}</td>
            <td>{{ t.lead?.name }}<div class="muted">{{ t.lead?.boards_text }} {{ t.lead?.limit_up_time }}</div></td>
            <td>{{ t.mid?.name }}<div class="muted">约{{ yi(t.mid?.amount_est) }}</div></td>
            <td>{{ (t.followers || []).map((x) => x.name).join('、') || '—' }}</td>
            <td class="num">{{ (t.trend || []).join(' → ') }}</td>
            <td><span class="tag" :class="t.status === '新启动' ? 'tag-red' : (t.status.includes('降温') ? 'tag-mute' : 'tag-gold')">{{ t.status }}</span></td>
          </tr>
        </tbody>
      </table>
      <h4>前5题材近{{ (day.themes?.top?.[0]?.trend_dates || []).length }}日涨停数走势</h4>
      <ChartPanel v-if="themeTrendChart" :option="themeTrendChart" :height="280" />
      <details>
        <summary>展开：前5题材全部涨停股</summary>
        <div v-for="t in day.themes?.top || []" :key="t.name">
          <h4>{{ t.name }}（{{ t.n }}）</h4>
          <DataTable
            :columns="[
              { key: 'name', label: '名称' },
              { key: 'code', label: '代码' },
              { key: 'boards_text', label: '板数' },
              { key: 'limit_up_time', label: '首封' },
              { key: 'open_times', label: '开板次数', type: 'num' },
              { key: 'seal_money', label: '封单', type: 'yi' },
              { key: 'reason', label: '涨停原因' },
            ]"
            :rows="t.stocks || []"
          />
        </div>
      </details>
      <NoteBlock :notes="day.themes?.notes" />
    </section>

    <!-- 4 跌停 -->
    <section id="loss" class="section">
      <h2><span class="idx">4</span>跌停与亏钱效应</h2>
      <SourceLine :text="day.loss?.src" />
      <DataTable
        :columns="[
          { key: 'name', label: '名称' },
          { key: 'code', label: '代码' },
          { key: 'pct', label: '跌幅', type: 'pct' },
          { key: 'first_limit_time', label: '首次跌停' },
          { key: 'turnover_ratio_pct', label: '换手', get: (r) => isNil(r.turnover_ratio_pct) ? '—' : r.turnover_ratio_pct.toFixed(1) + '%' },
          { key: 'keywords', label: '异动关键词', get: (r) => (r.keywords || []).join('；') },
        ]"
        :rows="day.loss?.limit_downs || []"
        empty="当日无跌停"
      />
      <h4>昨日涨停股今天的涨跌分布（均值 {{ pct(m.prem) }}，{{ m.prem_up }}/{{ m.prem_n }} 收红）</h4>
      <ChartPanel v-if="histChart" :option="histChart" :height="240" />
      <h4>昨日涨停、今天跌得最多的</h4>
      <DataTable
        :columns="[
          { key: 'name', label: '名称' },
          { key: 'code', label: '代码' },
          { key: 'yesterday_text', label: '昨日' },
          { key: 'pct', label: '今日', type: 'pct' },
        ]"
        :rows="day.loss?.yesterday_worst || []"
      />
      <h4>跌幅≥7%里成交额最大的10只</h4>
      <DataTable
        :columns="[
          { key: 'code', label: '代码' },
          { key: 'name', label: '名称' },
          { key: 'pct', label: '今日', type: 'pct' },
          { key: 'amount_est', label: '成交额(估)', type: 'yi' },
          { key: 'keywords', label: '异动关键词', get: (r) => (r.keywords || []).join('；') },
        ]"
        :rows="day.loss?.big_down || []"
      />
      <NoteBlock :notes="day.loss?.notes" />
    </section>

    <!-- 5 龙虎榜 -->
    <section id="lhb" class="section">
      <h2><span class="idx">5</span>龙虎榜解读</h2>
      <SourceLine :text="day.lhb?.src" />
      <p>当日“1日榜”共 {{ day.lhb?.count ?? '—' }} 只。</p>
      <h4>净买入前10</h4>
      <table class="data" v-if="day.lhb?.net_buy_top?.length">
        <thead>
          <tr>
            <th>名称</th><th>代码</th><th class="num">涨跌</th><th class="num">净买</th><th class="num">机构净买</th><th class="num">游资净买</th><th>合力/分歧</th><th>题材</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in day.lhb.net_buy_top" :key="r.code">
            <td>{{ r.name }}</td><td>{{ r.code }}</td>
            <td class="num" :class="pctCls(r.pct)">{{ pct(r.pct) }}</td>
            <td class="num" :class="pctCls(r.net)">{{ yi(r.net) }}</td>
            <td class="num" :class="pctCls(r.org_net)">{{ yi(r.org_net) }}</td>
            <td class="num" :class="pctCls(r.hot_net)">{{ yi(r.hot_net) }}</td>
            <td><span v-if="r.tag" :class="tagClass(r.tag)">{{ r.tag }}</span><span v-else class="muted">—</span></td>
            <td>{{ (r.themes || []).join('、') || '—' }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else class="src">当日龙虎榜日榜缺失或没有净买入记录。</p>
      <h4>净卖出前5</h4>
      <table class="data" v-if="day.lhb?.net_sell_top?.length">
        <thead>
          <tr>
            <th>名称</th><th>代码</th><th class="num">涨跌</th><th class="num">净买</th><th class="num">机构净买</th><th class="num">游资净买</th><th>合力/分歧</th><th>题材</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in day.lhb.net_sell_top" :key="r.code">
            <td>{{ r.name }}</td><td>{{ r.code }}</td>
            <td class="num" :class="pctCls(r.pct)">{{ pct(r.pct) }}</td>
            <td class="num" :class="pctCls(r.net)">{{ yi(r.net) }}</td>
            <td class="num" :class="pctCls(r.org_net)">{{ yi(r.org_net) }}</td>
            <td class="num" :class="pctCls(r.hot_net)">{{ yi(r.hot_net) }}</td>
            <td><span v-if="r.tag" :class="tagClass(r.tag)">{{ r.tag }}</span><span v-else class="muted">—</span></td>
            <td>{{ (r.themes || []).join('、') || '—' }}</td>
          </tr>
        </tbody>
      </table>
      <h4>按题材汇总的龙虎榜净买（分上涨股/下跌股）</h4>
      <p class="src">题材优先用涨停原因归类，没有涨停原因的用同花顺概念归类；一只票可能算进多个题材。</p>
      <DataTable
        :columns="[
          { key: 'theme', label: '题材' },
          { key: 'up', label: '上涨股净买(只数)', get: (r) => `${yi(r.up_net)}（${r.up_n}）` },
          { key: 'down', label: '下跌股净买(只数)', get: (r) => `${yi(r.down_net)}（${r.down_n}）` },
        ]"
        :rows="day.lhb?.theme_agg || []"
      />
      <ChartPanel v-if="lhbThemeChart" :option="lhbThemeChart" :height="300" />
      <h4 v-if="day.lhb?.org_buy_top?.length">机构专用：净买前5</h4>
      <DataTable
        v-if="day.lhb?.org_buy_top?.length"
        :columns="[
          { key: 'name', label: '名称' },
          { key: 'code', label: '代码' },
          { key: 'pct', label: '涨跌', type: 'pct' },
          { key: 'org_net', label: '机构净买', type: 'yi' },
          { key: 'seats', label: '买/卖席位数', get: (r) => `${r.buy_num ?? '—'}/${r.sell_num ?? '—'}` },
        ]"
        :rows="day.lhb.org_buy_top"
      />
      <h4 v-if="day.lhb?.org_sell_top?.length">机构专用：净卖前5</h4>
      <DataTable
        v-if="day.lhb?.org_sell_top?.length"
        :columns="[
          { key: 'name', label: '名称' },
          { key: 'code', label: '代码' },
          { key: 'pct', label: '涨跌', type: 'pct' },
          { key: 'org_net', label: '机构净买', type: 'yi' },
          { key: 'seats', label: '买/卖席位数', get: (r) => `${r.buy_num ?? '—'}/${r.sell_num ?? '—'}` },
        ]"
        :rows="day.lhb.org_sell_top"
      />
      <h4 v-if="day.lhb?.hot_money?.length">知名游资（扶摇按席位外号归类）当日净买与主要个股</h4>
      <table class="data" v-if="day.lhb?.hot_money?.length">
        <thead>
          <tr><th>游资</th><th class="num">当日净买合计</th><th>主要个股（该游资在此股净额）</th></tr>
        </thead>
        <tbody>
          <tr v-for="g in day.lhb.hot_money" :key="g.name">
            <td>{{ g.name }}</td>
            <td class="num" :class="pctCls(g.net)">{{ yi(g.net) }}</td>
            <td>{{ (g.stocks || []).map((s) => `${s.name}(${yi(s.net)})`).join('、') }}</td>
          </tr>
        </tbody>
      </table>
      <NoteBlock :notes="day.lhb?.notes" />
    </section>

    <!-- 6 情绪 -->
    <section id="cycle" class="section">
      <h2><span class="idx">6</span>情绪周期</h2>
      <p>
        <b>规则自动判断：{{ day.sentiment?.auto_stage }}</b>
       　<SentimentTag :tag="day.sentiment?.tag" />
      </p>
      <ul>
        <li v-for="(w, i) in day.sentiment?.auto_why || []" :key="i">{{ w }}</li>
      </ul>
      <NoteBlock :notes="day.sentiment?.notes" title="白话解读" />
    </section>

    <!-- 7 次日观察：不含事后 -->
    <section id="next" class="section">
      <h2><span class="idx">7</span>次日观察要点</h2>
      <SourceLine :text="day.next?.src" />
      <ol>
        <li v-for="(p, i) in day.next?.points || []" :key="i">{{ p.replace(/^\d+）/, '') }}</li>
      </ol>
      <h4>观察名单</h4>
      <DataTable
        :columns="[
          { key: 'code', label: '代码' },
          { key: 'name', label: '名称' },
          { key: 'why', label: '关注理由' },
        ]"
        :rows="day.next?.watch || []"
      />
    </section>

    <!-- 8 事后验证 -->
    <section id="post" class="section hindsight">
      <h2><span class="idx">8</span>事后验证</h2>
      <div class="warn">⚠ {{ day.post?.warning || '以下为事后数据（复盘当天并不知道），用来检验上面的判断对不对。' }}</div>
      <DataTable
        :columns="[
          { key: 'date', label: '日期', get: (r) => md(r.date) },
          { key: 'index_pct', label: '上证涨跌', type: 'pct' },
          { key: 'lu_nonst', label: '涨停', type: 'num' },
          { key: 'ld', label: '跌停', type: 'num' },
          { key: 'seal_rate', label: '封板率', type: 'rate', digits: 0 },
          { key: 'height', label: '空间板', type: 'num' },
          { key: 'prem', label: '昨涨停溢价', type: 'pct', digits: 1 },
          { key: 'turnover', label: '成交额', type: 'yi' },
        ]"
        :rows="day.post?.days || []"
        empty="还没有后续交易日数据。"
      />
      <h4 v-if="day.post?.theme_follow?.length">前5题材之后几天的涨停家数</h4>
      <table class="data" v-if="day.post?.theme_follow?.length">
        <thead>
          <tr>
            <th>题材</th>
            <th v-for="d in day.post.theme_follow[0].dates" :key="d" class="num">{{ md(d) }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in day.post.theme_follow" :key="t.name">
            <td>{{ t.name }}</td>
            <td v-for="(c, i) in t.counts" :key="i" class="num">{{ c }}</td>
          </tr>
        </tbody>
      </table>
      <ChartPanel v-if="postThemeChart" :option="postThemeChart" :height="300" />
      <h4 v-if="day.post?.watch_follow?.length">观察名单之后几天表现</h4>
      <p v-if="day.post?.near_limit_note" class="src">涨停=扶摇涨停池里有它；近涨停*：{{ day.post.near_limit_note }}</p>
      <table class="data" v-if="day.post?.watch_follow?.length">
        <thead>
          <tr>
            <th>名称</th><th>代码</th>
            <th v-for="d in day.post.watch_follow[0].days" :key="d.date" class="num">{{ md(d.date) }}</th>
            <th>{{ day.post.watch_follow[0].vs_base?.asof ? md(day.post.watch_follow[0].vs_base.asof) + '收盘相对' + md(day.date) : '相对当日' }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="w in day.post.watch_follow" :key="w.code">
            <td>{{ w.name }}</td>
            <td>{{ w.code }}</td>
            <td v-for="d in w.days" :key="d.date" class="num" :class="followCls(d)">{{ followCell(d) }}</td>
            <td class="num" :class="pctCls(w.vs_base?.close_pct)">{{ vsText(w.vs_base) }}</td>
          </tr>
        </tbody>
      </table>
      <NoteBlock :notes="day.post?.notes" title="事后对照" />
    </section>

    <!-- 9 术语 -->
    <section id="terms" class="section">
      <h2><span class="idx">9</span>术语小卡</h2>
      <div class="terms">
        <div v-for="t in day.terms || []" :key="t.term" class="term">
          <dt>{{ t.term }}</dt>
          <dd>{{ t.def }}</dd>
        </div>
      </div>
    </section>

    <!-- 消息面 -->
    <section id="news" class="section">
      <h2><span class="idx">讯</span>当日消息面（带出处）</h2>
      <ul v-if="day.news?.length" class="news">
        <li v-for="(n, i) in day.news" :key="i">
          {{ n.point }}
          ——
          <a v-if="n.url" class="src-link" :href="n.url" target="_blank" rel="noopener noreferrer">{{ n.src }}</a>
          <span v-else class="src-link">{{ n.src }}</span>
        </li>
      </ul>
      <p v-else class="src">消息面未核。</p>
    </section>

    <!-- 待核 -->
    <section id="gaps" class="section">
      <h2><span class="idx">核</span>数据缺口 / 待核</h2>
      <ul v-if="day.gaps?.length" class="gaps">
        <li v-for="(g, i) in day.gaps" :key="i">{{ g }}</li>
      </ul>
      <p v-else class="src">本页关键统计均有数据来源。若个股名称标注“待核”，是本地名单缺失，不影响涨跌数字本身。</p>
    </section>

    <Disclaimer extra="短线交易风险高，涨停不代表次日还能赚。请以交易所与公司公告为准。" />
  </main>
</template>
