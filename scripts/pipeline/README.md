# 复盘数据管道

这些脚本把扶摇接口、本机日 K、龙虎榜日榜整理成 Vue 应用读取的 JSON。

- `fy.py`：扶摇 HTTP 封装，带本地缓存。密钥只从 `FUYAO_API_KEY` 或项目根目录 `secrets/fuyao.key` 读取，不会写进仓库。
- `data.py`：涨停/跌停/炸板池、指数 K 线、日 K 指标。
- `themes.py` / `terms.py`：题材关键词与术语释义。
- `helpers.py`：晋级判断、情绪自动规则、观察名单默认逻辑。

上游数据默认路径（可用环境变量覆盖）：

| 变量 | 默认 | 含义 |
|---|---|---|
| `FUYAO_API_KEY` | （无） | 扶摇 API 密钥 |
| `FUYAO_CACHE_DIR` | 项目 `.cache/fuyao` | 接口缓存 |
| `FUYAO_LHB_DIR` | `/workspace/fuyao_lhb_market/daily` | 龙虎榜日榜 |
| `FUYAO_MARKET_DAILY` | `/workspace/fuyao/market_daily` | 个股日 K |
| `LIMITUP_ARCHIVE` | `/workspace/archive_limitup_2y.csv` | 历史涨停档案（补名称） |
| `DAILY_REVIEW_ROOT` | （无） | 若指向已有 `daily_review` 目录，会复用其 `cache/` 与 `notes/` |

日常请用仓库根目录的 `python3 scripts/export_day.py YYYY-MM-DD`。
