"""扶摇 API 薄封装。密钥只从环境变量 FUYAO_API_KEY 或被忽略的 secrets/fuyao.key 读取，绝不打印。"""
import json, os, time, datetime as dt, hashlib, requests

BASE = "https://fuyao.aicubes.cn"
SH = dt.timezone(dt.timedelta(hours=8))

def _project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def _cache_dir():
    env = os.environ.get('FUYAO_CACHE_DIR')
    if env:
        os.makedirs(env, exist_ok=True)
        return env
    d = os.path.join(_project_root(), '.cache', 'fuyao')
    os.makedirs(d, exist_ok=True)
    return d

CACHE = None  # resolved lazily

def _key():
    k = os.environ.get('FUYAO_API_KEY') or os.environ.get('X_API_KEY')
    if k:
        return k.strip()
    root = _project_root()
    for p in (
        os.path.join(root, 'secrets', 'fuyao.key'),
        os.path.join(root, 'secrets', 'api_key'),
    ):
        if os.path.isfile(p):
            return open(p).read().strip()
    return ''

def dms(d):
    return int(dt.datetime.strptime(d, '%Y-%m-%d').replace(tzinfo=SH).timestamp() * 1000)

def get(path, **params):
    global CACHE
    if CACHE is None:
        CACHE = _cache_dir()
    k = hashlib.md5((path + json.dumps(params, sort_keys=True)).encode()).hexdigest()
    f = os.path.join(CACHE, k + '.json')
    if os.path.exists(f):
        return json.load(open(f))
    key = _key()
    if not key:
        return {'code': -1, 'message': 'missing API key (set FUYAO_API_KEY or secrets/fuyao.key); cache miss: ' + path}
    for t in range(6):
        try:
            r = requests.get(BASE + path, params=params, headers={'X-api-key': key}, timeout=60)
        except Exception:
            time.sleep(3 + 2 * t)
            continue
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 + t)
            continue
        try:
            j = r.json()
        except Exception:
            time.sleep(2 + t)
            continue
        if j.get('code') == 0:
            json.dump(j, open(f, 'w'), ensure_ascii=False)
            return j
        if j.get('code') in (429, 1008, 1009, 1010):
            time.sleep(2 + t)
            continue
        return j
    return {'code': -1, 'message': 'retry fail'}

def pool(kind, d):
    out = []
    p = 1
    while True:
        j = get(f'/api/a-share/special-data/{kind}', date_ms=dms(d), page=p, size=200)
        if j.get('code') != 0:
            return None, j
        data = j['data']
        out += data.get('item') or []
        if p >= data['pagination'].get('pages', 1):
            break
        p += 1
    return out, j
