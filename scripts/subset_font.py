#!/usr/bin/env python3
"""从本机 Noto Sans CJK 抽出中文子集 woff2，供图表离线显示中文。"""
import os, sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TTC_REG = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
TTC_BOLD = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')

def collect_text():
    chars = set()
    # ASCII + 常用标点、全角、拼音范围
    chars.update(chr(i) for i in range(0x20, 0x7F))
    chars.update('·—–…‘’“”《》【】（）「」『』、。，、；：？！￥％‰℃★⚠←→●○◆■□▪▫▲▼✔✕＋－×÷～')
    chars.update('０１２３４５６７８９')
    for folder in [ROOT / 'src', ROOT / 'public' / 'data', ROOT / 'scripts', ROOT / 'notes', ROOT / 'README.md']:
        if folder.is_file():
            chars.update(folder.read_text(encoding='utf-8', errors='ignore'))
            continue
        if not folder.exists():
            continue
        for p in folder.rglob('*'):
            if p.suffix.lower() in {'.vue', '.js', '.css', '.json', '.md', '.html', '.txt', '.py'}:
                chars.update(p.read_text(encoding='utf-8', errors='ignore'))
    # 股票名称，方便以后加新交易日少缺字
    for cand in (
        Path(os.environ.get('DAILY_REVIEW_ROOT', '/workspace/daily_review')) / 'cache' / 'names.json',
        ROOT / '.cache' / 'names.json',
    ):
        if cand.exists():
            try:
                nm = json.loads(cand.read_text())
                chars.update(''.join(nm.values()))
            except Exception:
                pass
    # 去掉控制符
    return ''.join(sorted(c for c in chars if ord(c) >= 32 or c in '\n\t'))

def sc_index(ttc_path):
    from fontTools.ttLib import TTCollection
    ttc = TTCollection(str(ttc_path))
    for i, font in enumerate(ttc.fonts):
        names = []
        for rec in font['name'].names:
            try:
                names.append(rec.toUnicode())
            except Exception:
                pass
        blob = ' '.join(names)
        if 'Noto Sans CJK SC' in blob and 'Mono' not in blob:
            return i
    return 2

def subset(ttc, index, text, dest):
    from fontTools.ttLib import TTCollection
    from fontTools.subset import Subsetter, Options
    ttc_obj = TTCollection(str(ttc))
    font = ttc_obj.fonts[index]
    opt = Options()
    opt.layout_features = ['*']
    opt.hinting = False
    opt.desubroutinize = True
    opt.flavor = 'woff2'
    opt.with_zopfli = False
    subsetter = Subsetter(options=opt)
    subsetter.populate(text=text)
    subsetter.subset(font)
    dest.parent.mkdir(parents=True, exist_ok=True)
    font.flavor = 'woff2'
    font.save(str(dest))
    print(f'wrote {dest} ({dest.stat().st_size/1024:.0f} KB), glyphs~{font["maxp"].numGlyphs}')

def main():
    text = collect_text()
    print('unique chars', len(set(text)))
    idx_r = sc_index(TTC_REG)
    idx_b = sc_index(TTC_BOLD)
    print('SC index regular/bold', idx_r, idx_b)
    dest_root = ROOT / 'src' / 'assets' / 'fonts'
    subset(TTC_REG, idx_r, text, dest_root / 'NotoSansSC-Subset.woff2')
    subset(TTC_BOLD, idx_b, text, dest_root / 'NotoSansSC-Bold-Subset.woff2')

if __name__ == '__main__':
    main()
