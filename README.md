# A股每日复盘（Vue 3）

面向新股民的短线复盘终端：看当天大盘、涨停梯队、题材、跌停、龙虎榜、情绪阶段，以及「次日观察」和带标注的「事后验证」。

- 界面和说明都是简体中文，尽量写白话，术语在当日页面底部有小卡片。
- 颜色是 **红涨绿跌**。
- 每个交易日页面末尾都有一句：**基于数据的分析框架，不构成投资建议**。
- 页面是数据驱动的。新增一天只需放入 JSON，并更新目录文件，不用改 Vue 代码。

仓库地址：<https://github.com/qinroam-sketch/daily-review-vue>

当前已收录样板日：**2026-08-03（星期一）**。那天是「指数跌、个股涨」：沪指 -0.59%，三市成交约 20113 亿，涨停 75 只（不含 ST，扶摇封板率 82.4%），空间板是传智教育 6 连板；核电/核聚变因 7/31 国务院核准 8 台机组而新启动。情绪判断是「分歧偏修复」。

## 本地运行

需要 Node.js 18 或更高版本。

```bash
git clone https://github.com/qinroam-sketch/daily-review-vue.git
cd daily-review-vue
npm install
npm run dev
```

浏览器打开终端里提示的地址（一般是 http://localhost:5173）。路由使用 Hash（`#/day/2026-08-03`），不依赖服务器 rewrite，也方便以后用 GitHub Pages 发布。

## 打包

```bash
npm run build
npm run preview
```

产物在 `dist/`。中文字体已打进包里（Noto Sans SC 子集），图表不依赖外部 CDN，离线也能显示中文坐标和图例。

## 新增一个交易日

1. 如有人工解读，写到 `notes/YYYY-MM-DD.json`（键名：`summary`, `headline`, `sentiment_tag`, `market`, `ladder`, `themes`, `loss`, `lhb`, `cycle`, `next`, `watch`, `post`, `terms`, `news`, `gaps`）。没有 notes 也可以先出数据版。
2. 准备扶摇密钥（不要提交到 git）：
   - 环境变量 `FUYAO_API_KEY`，或
   - 项目根目录 `secrets/fuyao.key`（该目录已在 `.gitignore` 中）
3. 若本机已有日 K、龙虎榜、接口缓存，可设置：

```bash
export DAILY_REVIEW_ROOT=/path/to/daily_review
export FUYAO_LHB_DIR=/path/to/fuyao_lhb_market/daily
export FUYAO_MARKET_DAILY=/path/to/fuyao/market_daily
export FUYAO_CACHE_DIR=$DAILY_REVIEW_ROOT/cache
```

4. 导出并更新目录：

```bash
python3 scripts/export_day.py 2026-08-04
```

脚本会写入 `public/data/days/2026-08-04.json`，并更新 `public/data/manifest.json`。首页日历和列表会自动出现这一天。

字段说明见 `public/data/_fixture.example.json`。这个文件只是格式样例，**不会**作为真实交易日出现在目录里。

导出脚本依赖 Python 3，以及 `pandas`、`numpy`、`requests`。管道代码在 `scripts/pipeline/`，说明见该目录 README。

如果图表里新出现的汉字缺字，可在装有 Noto Sans CJK 的机器上运行：

```bash
python3 scripts/subset_font.py
```

## 把代码推到 GitHub

本仓库对应公开仓库 [qinroam-sketch/daily-review-vue](https://github.com/qinroam-sketch/daily-review-vue)。第一次推送示例：

```bash
git init
git add .
git commit -m "feat: 初始化每日复盘 Vue 应用，收录 2026-08-03 样板"
git branch -M main
git remote add origin https://github.com/qinroam-sketch/daily-review-vue.git
git push -u origin main
```

之后每个交易日更新：

```bash
python3 scripts/export_day.py YYYY-MM-DD
git add public/data
git commit -m "data: 更新 YYYY-MM-DD 复盘"
git push
```

请不要把 `secrets/`、`.env`、接口缓存、`node_modules` 或 `dist/` 提交上去。

## 页面结构

- `/`：交易日目录（日历 + 列表），展示指数涨跌、涨停/跌停、封板率、情绪标签、当日最值得盯的题材。
- `/#/day/YYYY-MM-DD`：当日完整复盘，顺序为：大盘概况、涨停梯队、题材板块、跌停与亏钱效应、龙虎榜解读、情绪周期、次日观察要点（不含事后信息）、事后验证（明确标注是事后才知道的）、术语小卡、消息面、待核。
- `/#/week`：周总结占位，等按周批量更新后再补。

数字不以「待核」代替已有数据。不同口径会写在「待核」里，例如 2026-08-03 涨停家数：扶摇不含 ST 为 75 只（封板率 82.4%，75/91），证券时报·数据宝为 83 只、封板率 79.05%。

## 许可与声明

数据来自扶摇接口、本机日 K 和已核对的公开报道。基于数据的分析框架，不构成投资建议。
