#!/usr/bin/env python3
"""导出一个交易日到 public/data/days/YYYY-MM-DD.json，并更新 manifest.json。

用法：
  python3 scripts/export_day.py 2026-08-03
  python3 scripts/export_day.py 2026-08-03 --post 5

环境变量见 scripts/pipeline/README.md。人工解读放在 notes/YYYY-MM-DD.json
（项目根 notes/ 或 DAILY_REVIEW_ROOT/notes/）。
"""
import sys, os, json, collections, datetime as dt, re, html as HTML, argparse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PIPE = os.path.join(os.path.dirname(__file__), 'pipeline')
sys.path.insert(0, PIPE)

import numpy as np
import pandas as pd
from data import *
from themes import themes_of
from terms import TERMS
import helpers as H

WEEKDAY = '一二三四五六日'
SH = dt.timezone(dt.timedelta(hours=8))


def notes_dir():
    dr = os.environ.get('DAILY_REVIEW_ROOT')
    if dr and os.path.isdir(os.path.join(dr, 'notes')):
        return os.path.join(dr, 'notes')
    return os.path.join(ROOT, 'notes')


def strip_tags(s):
    if not s:
        return ''
    s = re.sub(r'<br\s*/?>', '\n', s)
    s = re.sub(r'</p>\s*<p[^>]*>', '\n', s)
    s = re.sub(r'<[^>]+>', '', s)
    return HTML.unescape(s).strip()


def as_notes(v):
    if not v:
        return []
    if isinstance(v, list):
        return [strip_tags(x) for x in v if strip_tags(x)]
    t = strip_tags(v)
    return [t] if t else []


def fnum(x):
    if x is None:
        return None
    try:
        x = float(x)
    except Exception:
        return None
    if np.isnan(x) or np.isinf(x):
        return None
    return x


def stock(x, extra=None):
    d = {
        'code': x.get('ticker') or x.get('code'),
        'name': x.get('name'),
        'is_st': bool(x.get('is_st')),
        'boards': x.get('continue_day_cnt'),
        'boards_text': x.get('continue_day_text'),
        'limit_up_time': x.get('limit_up_time'),
        'open_times': x.get('open_times') or 0,
        'seal_money': fnum(x.get('seal_money')),
        'reason': x.get('limit_up_reason') or '',
    }
    if extra:
        d.update(extra)
    return {k: v for k, v in d.items() if v is not None and v != ''}


def default_headline(m, highlight, sentiment_tag):
    sh = next((i for i in m.get('indices', []) if i['name'] == '上证指数'), None)
    bits = []
    if sh and sh.get('pct') is not None:
        bits.append(f"沪指 {sh['pct']:+.2f}%")
    bits.append(f"涨停 {m.get('lu_nonst')}（不含ST）")
    if m.get('seal_rate') is not None:
        bits.append(f"封板率 {m['seal_rate']*100:.1f}%")
    if highlight:
        bits.append(f"主看{highlight}")
    if sentiment_tag:
        bits.append(f"情绪：{sentiment_tag}")
    return '，'.join(bits)


def export(D, POST=5):
    cal = calendar()
    if not cal:
        raise SystemExit('无法获取交易日历（检查扶摇缓存或 FUYAO_API_KEY）')
    if D not in cal:
        nxt = [d for d in cal if d >= D]
        if not nxt:
            raise SystemExit(f'没有 >= {D} 的交易日')
        print(f'{D} 非交易日，改用 {nxt[0]}', file=sys.stderr)
        D = nxt[0]
    i = cal.index(D)
    prev = cal[i - 1]
    hist = cal[max(0, i - 10):i + 1]
    post = [d for d in cal[i + 1:i + 1 + POST]]
    notes = {}
    nf = os.path.join(notes_dir(), f'{D}.json')
    if os.path.exists(nf):
        notes = json.load(open(nf))
    M = {d: day_metrics(d, cal) for d in hist}
    m, mp = M[D], M[prev]
    lu = lu_pool(D)
    plu = lu_pool(prev)
    ld = ld_pool(D)
    br = br_pool(D)
    st = m['stats'] or {}
    pc = pct_on(D, prev)
    P = panel()
    amt = P['amt'].loc[D] if D in P.index else pd.Series(dtype=float)
    ano = anomalies(D)

    indices = []
    for c, nm in IDX.items():
        b = index_bars(c)
        x, y = b.get(D), b.get(prev)
        if x and y:
            ch = (x['close_price'] / y['close_price'] - 1) * 100
            indices.append({
                'code': c, 'name': nm,
                'close': fnum(x['close_price']),
                'pct': fnum(ch),
                'turnover': fnum(x['turnover']),
                'prev_turnover': fnum(y['turnover']),
            })

    t_now, t_prev = m['turnover'], mp['turnover']
    dturn = (t_now / t_prev - 1) * 100 if t_now and t_prev else None
    sr = st.get('seal_rate')
    psr = (mp['stats'] or {}).get('seal_rate')

    height_name = None
    if lu:
        topx = max(lu, key=lambda x: x['continue_day_cnt'])
        if topx['continue_day_cnt'] == m['height']:
            height_name = topx['name']

    def hist_row(d):
        md = M[d]
        s = (md['stats'] or {})
        return {
            'date': d,
            'lu_nonst': md['lu_nonst'], 'ld': md['ld'], 'br': md['br'],
            'seal_rate': fnum(s.get('seal_rate')),
            'height': md['height'],
            'prem': fnum(md['prem']),
            'turnover': fnum(md['turnover']),
        }

    market = {
        'src': '指数与成交额：扶摇指数K线；三市成交额=上证综指+深证综指+北证50成交额（北证用北证50近似）。涨跌家数：本机前复权日K（仅沪深，不含北交所）。涨停/跌停/炸板：扶摇股票池。',
        'indices': indices,
        'turnover': fnum(t_now),
        'turnover_prev': fnum(t_prev),
        'turnover_chg_pct': fnum(dturn),
        'up': m['up'], 'down': m['down'], 'flat': m['flat'], 'n': m['n'],
        'up_prev': mp['up'], 'down_prev': mp['down'],
        'median_pct': fnum(m['median']),
        'big_up': m['big_up'], 'big_dn': m['big_dn'],
        'big_up_prev': mp['big_up'], 'big_dn_prev': mp['big_dn'],
        'lu_nonst': m['lu_nonst'], 'lu_all': m['lu_all'], 'lu_st': m['lu_st'],
        'lu_nonst_prev': mp['lu_nonst'], 'lu_all_prev': mp['lu_all'],
        'ld': m['ld'], 'ld_prev': mp['ld'],
        'br': m['br'], 'br_prev': mp['br'],
        'seal_rate': fnum(sr),
        'seal_rate_prev': fnum(psr),
        'sealed': st.get('limit_up_stock_count'),
        'touched': st.get('touched_limit_up_stock_count'),
        'prem': fnum(m['prem']), 'prem_up': m['prem_up'], 'prem_n': m['prem_n'],
        'prem_lb': fnum(m['prem_lb']), 'prem_lb_n': m['prem_lb_n'],
        'height': m['height'],
        'height_prev': mp['height'],
        'height_name': height_name,
        'notes': as_notes(notes.get('market')),
    }

    by = collections.defaultdict(list)
    for x in lu:
        by[x['continue_day_cnt']].append(x)
    boards = []
    for n in sorted(by, reverse=True):
        xs = sorted(by[n], key=lambda x: x['limit_up_time'] or '')
        boards.append({'level': n, 'count': len(xs), 'stocks': [stock(x) for x in xs]})
    pby = collections.defaultdict(list)
    for x in plu:
        pby[x['continue_day_cnt']].append(x)
    tod = {x['ticker']: x for x in lu}
    promotions, broke = [], []
    for n in sorted(pby):
        got = [x for x in pby[n] if x['ticker'] in tod and tod[x['ticker']]['continue_day_cnt'] == n + 1]
        sus = [x for x in pby[n] if x['ticker'] not in tod and (pc.get(x['ticker']) is None or (isinstance(pc.get(x['ticker']), float) and np.isnan(pc.get(x['ticker']))))]
        den = len(pby[n]) - len(sus)
        promotions.append({
            'from_level': n, 'to_level': n + 1,
            'label': f'{n}进{n+1}',
            'yesterday': len(pby[n]),
            'promoted': len(got),
            'suspended': len(sus),
            'tradable': den,
            'rate': (len(got) / den if den else None),
            'promoted_names': [x['name'] for x in got],
            'suspended_names': [x['name'] for x in sus],
        })
        if n >= 2:
            for x in pby[n]:
                if x['ticker'] not in tod:
                    v = pc.get(x['ticker'])
                    suspended = v is None or (isinstance(v, float) and np.isnan(v))
                    broke.append({
                        'name': x['name'], 'code': x['ticker'],
                        'yesterday_text': x['continue_day_text'],
                        'pct': None if suspended else fnum(v),
                        'status': '停牌/无数据' if suspended else None,
                        'reason': x['limit_up_reason'] or '',
                    })
    ladder = {
        'src': '连板数=扶摇涨停池 continue_day_cnt（只算“连续”涨停，含ST）。晋级率=昨天N板今天成为N+1板的比例，用前后两天涨停池自己对出来。',
        'boards': boards,
        'promotions': promotions,
        'broke': broke,
        'fuyao_page_boards': st.get('page_boards') or [],
        'notes': as_notes(notes.get('ladder')),
    }

    th = collections.defaultdict(list)
    for x in lu:
        for t in themes_of(x['limit_up_reason']):
            th[t].append(x)

    def cnt_theme(d, t):
        return sum(1 for x in lu_pool(d) if t in themes_of(x['limit_up_reason']))

    trend_days = cal[max(0, i - 5):i + 1]
    all_dist = sorted([t for t in th if t != 'ST/摘帽'], key=lambda t: -len(th[t]))
    top_names = all_dist[:5]
    top, theme_info = [], {}
    for t in top_names:
        xs_ = sorted(th[t], key=lambda x: (-x['continue_day_cnt'], x['limit_up_time'] or ''))
        prim = [x for x in xs_ if H.primary_theme(x['limit_up_reason']) == t] or xs_
        lead = prim[0]
        mid = max(prim, key=lambda x: amt.get(x['ticker'], 0) or 0)
        fol = [x for x in sorted(xs_, key=lambda x: x['limit_up_time'] or '', reverse=True) if x not in (lead, mid)][:4]
        tr = [cnt_theme(d, t) for d in trend_days]
        prev5 = tr[:-1]
        status = '新启动' if sum(prev5[-3:]) <= 2 else ('持续发酵' if tr[-1] >= np.mean(prev5) else '持续但降温')
        theme_info[t] = dict(n=len(xs_), lead=lead, mid=mid, trend=tr, status=status)
        top.append({
            'name': t, 'n': len(xs_), 'status': status,
            'lead': stock(lead),
            'mid': stock(mid, {'amount_est': fnum(amt.get(mid['ticker']))}),
            'followers': [stock(x) for x in fol],
            'trend': tr, 'trend_dates': trend_days,
            'stocks': [stock(x, {'amount_est': fnum(amt.get(x['ticker']))}) for x in sorted(th[t], key=lambda x: x['limit_up_time'] or '')],
        })
    themes = {
        'src': '归类方法：按扶摇涨停原因里的关键词归到题材（一只票可同时属于多个题材，所以加总会大于涨停总数）。龙头=该题材连板最高、同板数里封板最早；中军=该题材涨停股中当天成交额最大（成交额用日K量×价估算）；跟风=其余、封板较晚的。“新启动/持续”看前5个交易日该题材的涨停家数。',
        'top': top,
        'distribution': [{'name': t, 'n': len(th[t])} for t in all_dist],
        'notes': as_notes(notes.get('themes')),
    }

    def ano_kw(code):
        return [k for a in ano.get(code, []) for k in (a.get('key_word_list') or [])]

    downs = [{
        'name': x['name'], 'code': x['ticker'],
        'pct': fnum(x.get('price_change_ratio_pct')),
        'first_limit_time': x.get('first_limit_time'),
        'turnover_ratio_pct': fnum(x.get('turnover_ratio_pct')),
        'keywords': ano_kw(x['ticker']),
    } for x in ld]
    vals = [(x, pc.get(x['ticker'])) for x in plu]
    vals = [(x, v) for x, v in vals if v is not None and not (isinstance(v, float) and np.isnan(v))]
    worst = sorted(vals, key=lambda z: z[1])[:8]
    NM = H.name_map()
    nm = dict(NM)
    for d_ in [D, prev]:
        for k in ['all', 'org']:
            L = lhb(d_, k)
            for x in (L or {}).get('stock_items', []):
                nm[x['ticker']] = x['name']
    for x in lu + plu + ld + br:
        nm[x['ticker']] = x['name']

    def nm_(c):
        return nm.get(c) or '（名称待核）'

    big = pc[pc <= -7].index
    bigs = sorted(big, key=lambda c: -(amt.get(c, 0) or 0))[:10]
    loss = {
        'src': '跌停池：扶摇；“异动关键词”来自扶摇/同花顺异动解读（AI 汇总公开信息，以公告为准）。',
        'limit_downs': downs,
        'yesterday_returns': [fnum(v) for _, v in vals],
        'yesterday_worst': [{
            'name': x['name'], 'code': x['ticker'],
            'yesterday_text': x['continue_day_text'],
            'pct': fnum(v),
        } for x, v in worst],
        'big_down': [{
            'code': c, 'name': nm_(c),
            'pct': fnum(pc[c]),
            'amount_est': fnum(amt.get(c)),
            'keywords': ano_kw(c),
            'name_pending': nm_(c) == '（名称待核）',
        } for c in bigs],
        'notes': as_notes(notes.get('loss')),
    }

    A = lhb(D, 'all')
    O = lhb(D, 'org')
    Hm = lhb(D, 'hot_money')
    lhb_info = {}
    lhb_obj = {
        'src': '来源：扶摇龙虎榜日榜（同花顺口径，非交易所全量；只取“1日”榜）。净买=该股上榜席位买入−卖出；机构/游资净额为扶摇分类。',
        'count': 0, 'net_buy_top': [], 'net_sell_top': [], 'theme_agg': [],
        'org_buy_top': [], 'org_sell_top': [], 'hot_money': [],
        'notes': as_notes(notes.get('lhb')),
    }
    if A:
        one = [x for x in A['stock_items'] if x.get('range_days') == 1 and H.is_stock(x['ticker'])]
        seen, one2 = set(), []
        for x in one:
            if x['ticker'] in seen:
                continue
            seen.add(x['ticker'])
            one2.append(x)
        for x in one2:
            lhb_info[x['ticker']] = x

        def lhb_row(x):
            o = x.get('org_net_value')
            h = x.get('hot_money_net_value')
            tag = '合力买' if (o or 0) > 0 and (h or 0) > 0 else '合力卖' if (o or 0) < 0 and (h or 0) < 0 else '分歧' if o and h else None
            return {
                'name': x['name'], 'code': x['ticker'],
                'pct': fnum((x['change'] or 0) * 100),
                'net': fnum(x['net_value']),
                'org_net': fnum(o),
                'hot_net': fnum(h),
                'tag': tag,
                'themes': H.lhb_themes(x),
            }

        tb = sorted(one2, key=lambda x: -(x['net_value'] or 0))
        lhb_obj['count'] = len(one2)
        lhb_obj['count_raw'] = len(one)
        lhb_obj['net_buy_top'] = [lhb_row(x) for x in tb[:10]]
        lhb_obj['net_sell_top'] = [lhb_row(x) for x in tb[::-1][:5]]
        agg = collections.defaultdict(lambda: [0.0, 0.0, 0, 0])
        for x in one2:
            k = 0 if (x['change'] or 0) > 0 else 1
            for t in H.lhb_themes(x) or ['(未归类)']:
                agg[t][k] += x['net_value'] or 0
                agg[t][k + 2] += 1
        lhb_obj['theme_agg'] = [{
            'theme': t,
            'up_net': fnum(v[0]), 'up_n': v[2],
            'down_net': fnum(v[1]), 'down_n': v[3],
        } for t, v in sorted(agg.items(), key=lambda z: -(z[1][0] + z[1][1]))]
    if O:
        oi = [x for x in O['stock_items'] if x.get('range_days', 1) == 1 and H.is_stock(x['ticker'])]
        seen, oi2 = set(), []
        for x in oi:
            if x['ticker'] in seen:
                continue
            seen.add(x['ticker'])
            oi2.append(x)
        ob = sorted(oi2, key=lambda x: -(x.get('org_net_value') or 0))

        def org_row(x):
            return {
                'name': x['name'], 'code': x['ticker'],
                'pct': fnum((x['change'] or 0) * 100),
                'org_net': fnum(x.get('org_net_value')),
                'buy_num': x.get('org_buy_num'),
                'sell_num': x.get('org_sell_num'),
            }

        lhb_obj['org_buy_top'] = [org_row(x) for x in ob[:5] if x.get('org_net_value') is not None]
        lhb_obj['org_sell_top'] = [org_row(x) for x in ob[::-1][:5] if x.get('org_net_value') is not None]
    if Hm:
        rows = []
        for g in sorted(Hm['hot_money_items'], key=lambda g: -abs(g['buying'])):
            st_ = []
            for r in sorted(g['rows'], key=lambda r: -abs(r.get('hot_money_item_net_value') or 0)):
                if r.get('range_days') == 1:
                    st_.append({
                        'name': r['name'], 'code': r.get('ticker'),
                        'net': fnum(r.get('hot_money_item_net_value')),
                    })
            if not st_:
                continue
            rows.append({'name': g['name'], 'net': fnum(g['buying']), 'stocks': st_[:6]})
        lhb_obj['hot_money'] = rows

    auto, why = H.auto_stage(M, hist)
    sentiment_tag = notes.get('sentiment_tag') or '分歧偏修复'
    # 不要把默认标签套到其他日期：仅当 notes 里写了，或能从 cycle 文本识别
    if 'sentiment_tag' not in notes:
        blob = ' '.join(as_notes(notes.get('cycle')))
        if '分歧' in blob and '修复' in blob:
            sentiment_tag = '分歧偏修复'
        elif '冰点' in auto or '退潮' in auto:
            sentiment_tag = auto.split('（')[0]
        else:
            sentiment_tag = auto.split('（')[0]
    # 8/3 样板 notes 明确是「分歧偏修复」
    if D == '2026-08-03':
        sentiment_tag = '分歧偏修复'

    cycle = {
        'tag': sentiment_tag,
        'auto_stage': auto,
        'auto_why': why,
        'notes': as_notes(notes.get('cycle')),
    }

    watch = notes.get('watch') or H.default_watch(lu, theme_info, lhb_info)
    nxt = {
        'src': '只用当天收盘前能知道的信息；观察名单剔除科创/创业板20cm/北交/ST（市场统计不剔除）。',
        'points': as_notes(notes.get('next')),
        'watch': [{'code': w['code'], 'name': w['name'], 'why': w['why']} for w in watch],
    }

    post_obj = {
        'is_hindsight': True,
        'warning': '以下为事后数据（复盘当天并不知道），用来检验上面的判断对不对。',
        'days': [], 'theme_follow': [], 'watch_follow': [],
        'notes': as_notes(notes.get('post')),
        'near_limit_note': '近涨停=日K涨幅接近涨停但涨停池里没有（可能收盘差一分钱、或前复权价格误差），待核。',
    }
    if post:
        PM = {d: day_metrics(d, cal) for d in post}
        post_obj['days'] = [{
            'date': d,
            'index_pct': fnum(H.idx_chg('000001.SH', d, cal)),
            'lu_nonst': PM[d]['lu_nonst'],
            'ld': PM[d]['ld'],
            'seal_rate': fnum((PM[d]['stats'] or {}).get('seal_rate')),
            'height': PM[d]['height'],
            'prem': fnum(PM[d]['prem']),
            'turnover': fnum(PM[d]['turnover']),
        } for d in post]
        for t in top_names:
            post_obj['theme_follow'].append({
                'name': t,
                'counts': [theme_info[t]['n']] + [cnt_theme(d, t) for d in post],
                'dates': [D] + post,
            })
        P2 = panel()
        wf = []
        for w in watch:
            c = w['code']
            days = []
            try:
                base = P2['close'][c].get(D) if c in P2['close'] else None
            except Exception:
                base = None
            for d in post:
                pd_ = cal[cal.index(d) - 1]
                try:
                    v = (P2['close'][c][d] / P2['close'][c][pd_] - 1) * 100
                except Exception:
                    v = np.nan
                lt = any(x['ticker'] == c for x in lu_pool(d))
                lim = 10 if board_of(c) == '主板' else 20
                near = (not np.isnan(v) and v >= lim - 0.3 and not lt)
                days.append({
                    'date': d,
                    'pct': None if (isinstance(v, float) and np.isnan(v)) else fnum(v),
                    'status': '停牌' if (isinstance(v, float) and np.isnan(v)) else None,
                    'limit_up': bool(lt),
                    'near_limit': bool(near),
                })
            rel = None
            try:
                hi = P2['high'][c].loc[post].max()
                lo = P2['low'][c].loc[post].min()
                rel = {
                    'close_pct': fnum((P2['close'][c][post[-1]] / base - 1) * 100),
                    'high_pct': fnum((hi / base - 1) * 100),
                    'low_pct': fnum((lo / base - 1) * 100),
                    'asof': post[-1],
                }
            except Exception:
                rel = None
            wf.append({'name': w['name'], 'code': c, 'days': days, 'vs_base': rel})
        post_obj['watch_follow'] = wf

    term_keys = notes.get('terms') or ['空间板', '晋级率', '封板率', '炸板', '昨日涨停溢价', '跷跷板', '合力', '停牌核查']
    terms = [{'term': k, 'def': TERMS.get(k, '待补')} for k in term_keys]

    highlight = None
    for t in top:
        if t['status'] == '新启动':
            highlight = t['name']
            break
    if not highlight and top:
        highlight = top[0]['name']

    # 样板日使用已核对的一句话；其他日期自动拼
    if notes.get('headline'):
        headline = notes['headline']
    elif D == '2026-08-03':
        headline = '指数跌、个股涨，资金从高位科技（半导体/存储）流向低位电力/核电；情绪处于“分歧偏修复”，没有坏。'
    else:
        headline = default_headline(market, highlight, sentiment_tag)

    wd = WEEKDAY[dt.date.fromisoformat(D).weekday()]
    return {
        'date': D,
        'weekday': wd,
        'weekday_full': '星期' + wd,
        'prev': prev,
        'headline': headline,
        'summary_html': notes.get('summary') or '',
        'sentiment': cycle,
        'highlight_theme': highlight,
        'market': market,
        'history': [hist_row(d) for d in hist],
        'ladder': ladder,
        'themes': themes,
        'loss': loss,
        'lhb': lhb_obj,
        'next': nxt,
        'post': post_obj,
        'terms': terms,
        'news': notes.get('news') or [],
        'gaps': notes.get('gaps') or [],
        'disclaimer': '基于数据的分析框架，不构成投资建议',
    }


def update_manifest(doc):
    man_path = os.path.join(ROOT, 'public', 'data', 'manifest.json')
    if os.path.exists(man_path):
        man = json.load(open(man_path))
    else:
        man = {'title': 'A股每日复盘', 'days': []}
    m = doc['market']
    entry = {
        'date': doc['date'],
        'weekday': doc['weekday'],
        'weekday_full': doc['weekday_full'],
        'prev': doc['prev'],
        'headline': doc['headline'],
        'indices': {i['name']: i['pct'] for i in m.get('indices', [])},
        'turnover': m.get('turnover'),
        'turnover_chg_pct': m.get('turnover_chg_pct'),
        'lu_nonst': m.get('lu_nonst'),
        'ld': m.get('ld'),
        'seal_rate': m.get('seal_rate'),
        'sentiment': doc['sentiment']['tag'],
        'top_theme': doc.get('highlight_theme'),
        'height': m.get('height'),
        'height_name': m.get('height_name'),
    }
    days = [x for x in man.get('days', []) if x.get('date') != doc['date'] and not str(x.get('date', '')).startswith('_')]
    days.append(entry)
    days.sort(key=lambda x: x['date'], reverse=True)
    man['days'] = days
    man['updated'] = dt.datetime.now(SH).strftime('%Y-%m-%d %H:%M')
    man['tz'] = 'Asia/Hong_Kong'
    os.makedirs(os.path.dirname(man_path), exist_ok=True)
    json.dump(man, open(man_path, 'w'), ensure_ascii=False, indent=2)
    return man_path


def main():
    ap = argparse.ArgumentParser(description='导出一日复盘 JSON 给 Vue 应用')
    ap.add_argument('date', help='YYYY-MM-DD，若非交易日则顺延到下一个交易日')
    ap.add_argument('--post', type=int, default=5, help='事后验证向后看几个交易日，默认 5')
    args = ap.parse_args()
    doc = export(args.date, args.post)
    out_dir = os.path.join(ROOT, 'public', 'data', 'days')
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{doc['date']}.json")
    json.dump(doc, open(out, 'w'), ensure_ascii=False, indent=2)
    man = update_manifest(doc)
    print('wrote', out)
    print('manifest', man)


if __name__ == '__main__':
    main()
