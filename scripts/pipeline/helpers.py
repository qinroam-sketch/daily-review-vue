"""从原 HTML 生成器抽出来的公共判断，不含作图。"""
import os, json, glob
import numpy as np
import pandas as pd
from data import LHB, ARCHIVE, board_of
from themes import themes_of

def is_stock(t):
    return not str(t).startswith(('11', '12', '20', '90', '13'))

_NM = None

def name_map():
    global _NM
    if _NM is not None:
        return _NM
    from data import _daily_review_root, ROOT
    candidates = []
    dr = _daily_review_root()
    if dr:
        candidates.append(os.path.join(dr, 'cache', 'names.json'))
    candidates.append(os.path.join(ROOT, '.cache', 'names.json'))
    for f in candidates:
        if os.path.exists(f):
            _NM = json.load(open(f))
            return _NM
    nm = {}
    if os.path.exists(ARCHIVE):
        a = pd.read_csv(ARCHIVE, dtype=str, usecols=['code', 'name'])
        nm.update(dict(zip(a.code, a.name)))
    if os.path.isdir(os.path.join(LHB, 'all')):
        for fn in sorted(glob.glob(os.path.join(LHB, 'all', '*.json'))):
            try:
                for x in (json.load(open(fn)).get('data') or {}).get('stock_items', []):
                    nm[x['ticker']] = x['name']
            except Exception:
                pass
    out = candidates[-1]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(nm, open(out, 'w'), ensure_ascii=False)
    _NM = nm
    return nm

def idx_chg(c, d, cal):
    from data import index_bars
    b = index_bars(c)
    p = cal[cal.index(d) - 1]
    return (b[d]['close_price'] / b[p]['close_price'] - 1) * 100 if d in b and p in b else None

def primary_theme(reason):
    for tok in (reason or '').split('+'):
        th = themes_of(tok)
        if th:
            return th[0]
    return None

def lhb_themes(x):
    return themes_of(x.get('limit_reason')) or themes_of('+'.join(c['name'] for c in (x.get('concept_list') or [])))

def watchable(t, name):
    return board_of(t) == '主板' and 'ST' not in name and not t.startswith('30')

def auto_stage(M, hist):
    d = hist[-1]
    p = hist[-2]
    m = M[d]
    q = M[p]
    avg_lu = np.mean([M[x]['lu_nonst'] for x in hist[-6:-1]])
    sr = (m['stats'] or {}).get('seal_rate') or 0
    why = [
        f"涨停 {m['lu_nonst']} 家，近5日均值 {avg_lu:.0f}；跌停 {m['ld']} 家",
        f"封板率 {sr*100:.0f}%；空间板 {q['height']}→{m['height']} 板",
        (f"昨日涨停今日溢价 {m['prem']:+.2f}%，昨日连板股 {m['prem_lb']:+.2f}%" if m['prem'] is not None else '溢价待核'),
        f"成交额较前日 {((m['turnover'] or 0)/(q['turnover'] or 1)-1)*100:+.1f}%",
    ]
    if m['ld'] >= 50 or (m['lu_nonst'] < 40 and (m['prem'] or 0) < 0):
        st = '冰点/退潮'
    elif m['lu_nonst'] >= 100 and sr >= 0.85 and (m['prem'] or 0) >= 3:
        st = '高潮'
    elif m['height'] < q['height'] and (m['prem'] or 0) > 0 and m['ld'] < 20:
        st = '分歧（高位断板，低位仍有承接）'
    elif m['height'] < q['height']:
        st = '退潮'
    elif m['lu_nonst'] > avg_lu and (m['prem'] or 0) > 0:
        st = '发酵'
    else:
        st = '分歧/修复（指标不一致）'
    return st, why

def default_watch(lu, theme_info, lhb_info):
    w = []
    for x in sorted(lu, key=lambda x: -x['continue_day_cnt'])[:3]:
        if watchable(x['ticker'], x['name']):
            w.append(dict(code=x['ticker'], name=x['name'], why=f"空间/高位 {x['continue_day_text']}"))
    for t, v in theme_info.items():
        for x in [v['lead'], v['mid']]:
            if watchable(x['ticker'], x['name']) and x['ticker'] not in [y['code'] for y in w]:
                w.append(dict(code=x['ticker'], name=x['name'], why=f'{t} 龙头/中军'))
    return w[:12]
