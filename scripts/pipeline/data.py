"""数据层：数字来自扶摇接口或本机日K。路径可用环境变量覆盖。"""
import os, glob, json, re, datetime as dt
import pandas as pd
from fy import get, pool, dms, SH

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))

def _daily_review_root():
    return os.environ.get('DAILY_REVIEW_ROOT', '')

LHB = os.environ.get('FUYAO_LHB_DIR', '/workspace/fuyao_lhb_market/daily')
MARKET = os.environ.get('FUYAO_MARKET_DAILY', '/workspace/fuyao/market_daily')
ARCHIVE = os.environ.get('LIMITUP_ARCHIVE', '/workspace/archive_limitup_2y.csv')
IDX = {
    '000001.SH': '上证指数',
    '399001.SZ': '深证成指',
    '399006.SZ': '创业板指',
    '000688.SH': '科创50',
    '899050.BJ': '北证50',
}
TURN_IDX = ['000001.SH', '399106.SZ', '899050.BJ']

def index_bars(code, start='2026-05-01', end='2026-11-20'):
    j = get('/api/a-share-index/prices/historical', thscode=code, interval='1d', start=dms(start), end=dms(end))
    out = {}
    for it in (j.get('data') or {}).get('item') or []:
        d = str(dt.datetime.fromtimestamp(it['date_ms'] / 1000, SH).date())
        out[d] = it
    return out

def calendar():
    return sorted(index_bars('000001.SH').keys())

_panel = None

def _panel_cache_path():
    dr = _daily_review_root()
    if dr and os.path.exists(os.path.join(dr, 'cache', 'panel.pkl')):
        return os.path.join(dr, 'cache', 'panel.pkl')
    d = os.path.join(ROOT, '.cache')
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, 'panel.pkl')

def panel():
    global _panel
    if _panel is not None:
        return _panel
    pk = _panel_cache_path()
    src = MARKET
    if os.path.exists(pk) and os.path.exists(src) and os.path.getmtime(pk) >= os.path.getmtime(src):
        _panel = pd.read_pickle(pk)
        return _panel
    if os.path.exists(pk) and not os.path.exists(src):
        _panel = pd.read_pickle(pk)
        return _panel
    rows = []
    for f in glob.glob(src + '/*.csv'):
        c = os.path.basename(f)[2:8]
        d = pd.read_csv(f)
        d = d[d.date >= '2026-04-01']
        d['code'] = c
        rows.append(d)
    if not rows:
        raise RuntimeError(f'未找到日K：请设置 FUYAO_MARKET_DAILY（当前 {src}）')
    p = pd.concat(rows)
    p['amt'] = p.vol * 100 * p.close
    p = p.pivot_table(index='date', columns='code', values=['close', 'high', 'low', 'open', 'amt'])
    p.to_pickle(pk)
    _panel = p
    return p

def pct_on(d, prev):
    p = panel()
    if d not in p.index or prev not in p.index:
        return pd.Series(dtype=float)
    return (p['close'].loc[d] / p['close'].loc[prev] - 1) * 100

def lu_pool(d):
    r, _ = pool('limit-up-pool', d)
    return r or []

def ld_pool(d):
    r, _ = pool('limit-down-pool', d)
    return r or []

def br_pool(d):
    r, _ = pool('limit-break-pool', d)
    return r or []

def lu_stats(d):
    j = get('/api/a-share/special-data/limit-up-statistics', date=d)
    return j.get('data') if j.get('code') == 0 else None

def lhb(d, kind):
    f = f'{LHB}/{kind}/{d}.json'
    if not os.path.exists(f):
        return None
    j = json.load(open(f))
    return j.get('data') if j.get('code') == 0 else None

def anomalies(d):
    j = get('/api/news/anomaly/analysis', begin_date=d, end_date=d)
    items = (j.get('data') or {}).get('items') or []
    out = {}
    for x in items:
        m = re.search(r'thsHqCode=(\d{6})', x.get('link_url') or '')
        if m:
            out.setdefault(m.group(1), []).append(x)
    return out

def board_of(t):
    if t.startswith(('688', '689')):
        return '科创'
    if t.startswith(('300', '301', '302')):
        return '创业板'
    if t.startswith(('8', '4', '92')):
        return '北交'
    return '主板'

def day_metrics(d, cal):
    i = cal.index(d)
    prev = cal[i - 1]
    lu = lu_pool(d)
    ld = ld_pool(d)
    br = br_pool(d)
    st = lu_stats(d)
    plu = lu_pool(prev)
    pc = pct_on(d, prev)
    prem = [pc.get(x['ticker']) for x in plu if x['ticker'] in pc.index and pd.notna(pc.get(x['ticker']))]
    prem_lb = [pc.get(x['ticker']) for x in plu if x['continue_day_cnt'] >= 2 and x['ticker'] in pc.index and pd.notna(pc.get(x['ticker']))]
    turn = 0
    ok = True
    for c in TURN_IDX:
        b = index_bars(c).get(d)
        if b:
            turn += b['turnover']
        else:
            ok = False
    nonst = [x for x in lu if not x['is_st']]
    return dict(
        date=d, prev=prev,
        lu_all=len(lu), lu_nonst=len(nonst), lu_st=len(lu) - len(nonst),
        ld=len(ld), br=len(br),
        seal_rate_calc=len(lu) / (len(lu) + len(br)) if lu else None,
        stats=st, height=max([x['continue_day_cnt'] for x in lu] or [0]),
        up=int((pc > 0).sum()), down=int((pc < 0).sum()), flat=int((pc == 0).sum()), n=int(pc.notna().sum()),
        big_up=int((pc >= 7).sum()), big_dn=int((pc <= -7).sum()),
        median=float(pc.median()) if len(pc) else None,
        prem=sum(prem) / len(prem) if prem else None, prem_up=sum(1 for v in prem if v > 0), prem_n=len(prem),
        prem_lb=sum(prem_lb) / len(prem_lb) if prem_lb else None, prem_lb_n=len(prem_lb),
        turnover=turn if ok else None,
    )
