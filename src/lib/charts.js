import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkLineComponent,
} from 'echarts/components'

use([CanvasRenderer, BarChart, LineChart, GridComponent, TooltipComponent, LegendComponent, MarkLineComponent])

export { init } from 'echarts/core'

export const FONT = '"Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif'

export const C = {
  up: '#f6465d',
  down: '#0ecb81',
  gold: '#e0b15a',
  blue: '#4da3ff',
  muted: '#9aa8b7',
  line: '#243040',
  text: '#e7edf4',
  axis: '#6d7b8a',
}

export function textStyle(extra = {}) {
  return { fontFamily: FONT, color: C.muted, fontSize: 12, ...extra }
}

export function tooltipBase() {
  return {
    trigger: 'axis',
    backgroundColor: 'rgba(14,20,28,0.94)',
    borderColor: C.line,
    textStyle: textStyle({ color: C.text, fontSize: 12 }),
    extraCssText: 'backdrop-filter:blur(8px);box-shadow:0 8px 28px rgba(0,0,0,.35)',
  }
}

export function gridBase() {
  return { left: 48, right: 48, top: 40, bottom: 36, containLabel: false }
}

export function categoryAxis(data) {
  return {
    type: 'category',
    data,
    axisLine: { lineStyle: { color: C.line } },
    axisTick: { show: false },
    axisLabel: textStyle({ fontSize: 11, color: C.axis }),
    splitLine: { show: false },
  }
}

export function valueAxis(name, extra = {}) {
  return {
    type: 'value',
    name,
    nameTextStyle: textStyle({ fontSize: 11 }),
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: textStyle({ fontSize: 11, color: C.axis }),
    splitLine: { lineStyle: { color: 'rgba(36,48,64,0.7)', type: 'dashed' } },
    ...extra,
  }
}
