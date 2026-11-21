<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { init, FONT } from '../lib/charts.js'

const props = defineProps({
  option: { type: Object, default: null },
  height: { type: Number, default: 280 },
})

const el = ref(null)
let chart = null

async function readyFonts() {
  try {
    if (document.fonts && document.fonts.load) {
      await Promise.all([
        document.fonts.load('14px "Noto Sans SC"'),
        document.fonts.load('700 14px "Noto Sans SC"'),
      ])
      await document.fonts.ready
    }
  } catch {
    /* 系统中文黑体兜底 */
  }
}

function render() {
  if (!el.value || !props.option) return
  if (!chart) chart = init(el.value, null, { renderer: 'canvas' })
  const opt = {
    textStyle: { fontFamily: FONT },
    ...props.option,
  }
  chart.setOption(opt, true)
  chart.resize()
}

let ro
onMounted(async () => {
  await readyFonts()
  render()
  ro = new ResizeObserver(() => chart && chart.resize())
  if (el.value) ro.observe(el.value)
})
watch(() => props.option, render, { deep: true })
onBeforeUnmount(() => {
  ro && ro.disconnect()
  chart && chart.dispose()
  chart = null
})
</script>
<template>
  <div ref="el" class="chart" :style="{ height: height + 'px' }"></div>
</template>
