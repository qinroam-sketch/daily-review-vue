<script setup>
import { computed } from 'vue'
import { pct, pctCls } from '../lib/format.js'

const props = defineProps({
  value: { type: [Number, String, null], default: null },
  digits: { type: Number, default: 2 },
  empty: { type: String, default: '—' },
})
const text = computed(() => (props.value === null || props.value === undefined ? props.empty : pct(props.value, props.digits)))
const cls = computed(() => pctCls(props.value))
</script>
<template>
  <span class="num" :class="cls">{{ text }}</span>
</template>
