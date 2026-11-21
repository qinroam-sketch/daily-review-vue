<script setup>
import { pct, pctCls, yi, rate, num, isNil } from '../lib/format.js'

defineProps({
  columns: { type: Array, required: true },
  rows: { type: Array, default: () => [] },
  empty: { type: String, default: '暂无' },
})

function cell(col, row) {
  const v = typeof col.get === 'function' ? col.get(row) : row[col.key]
  if (col.type === 'pct') return isNil(v) ? (row[col.emptyKey] || '—') : pct(v, col.digits ?? 2)
  if (col.type === 'yi') return yi(v, col.digits ?? 2)
  if (col.type === 'rate') return rate(v, col.digits ?? 0)
  if (col.type === 'num') return num(v, col.digits ?? 0)
  if (v === null || v === undefined || v === '') return col.emptyText ?? '—'
  return v
}
function cls(col, row) {
  const v = typeof col.get === 'function' ? col.get(row) : row[col.key]
  const base = col.numeric || col.type ? 'num' : ''
  if (col.type === 'pct' || col.signed) return `${base} ${pctCls(v)}`.trim()
  if (col.type === 'yi' && !isNil(v) && Number(v) !== 0) return `${base} ${Number(v) > 0 ? 'up' : 'dn'}`
  return base
}
</script>
<template>
  <table v-if="rows && rows.length" class="data">
    <thead>
      <tr>
        <th v-for="c in columns" :key="c.key || c.label" :class="{ num: c.numeric || c.type }">{{ c.label }}</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(row, i) in rows" :key="i">
        <td v-for="c in columns" :key="c.key || c.label" :class="cls(c, row)">
          <template v-if="c.slot">
            <slot :name="c.slot" :row="row" :value="cell(c, row)" />
          </template>
          <template v-else>{{ cell(c, row) }}</template>
        </td>
      </tr>
    </tbody>
  </table>
  <p v-else class="src">{{ empty }}</p>
</template>
