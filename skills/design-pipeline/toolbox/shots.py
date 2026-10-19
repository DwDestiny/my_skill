#!/usr/bin/env python3
"""shots.py 按评审清单批量截图（visual-motion-design/references/review.md 第 1 节）。Python 3.12 标准库。

用途：用 agent-browser 子进程把 review.md 截图清单一次拍完，并存控制台输出。
  d-fold、d-page-n、d-end（1440）、t-fold（768）、m-fold、m-page-n（390）、dark-fold、
  r-fold（减少动效）、k-1 到 k-3（Tab 三次）、h-rest 与 h-hover、stage-n（--docks 每个停靠点）。
什么时候跑：S5 门禁（出首轮截图）、S6 验收（每轮修正后重拍）。
输出去哪：<out>/*.png、<out>/SHOTS.md（文件名、视口、状态、用途）、<out>/console.txt。
  把 SHOTS.md 的表贴进 `05-评审/ROUND-<n>.md`。
前提：agent-browser 在 PATH（~/.local/bin）。并行时先设 `export AGENT_BROWSER_SESSION=<包名>`。
  页面用本地服务提供，例如在页面上级目录 `python3 -m http.server 8112 --bind 127.0.0.1`。

等待：每张截图前等 1500 ms，stage-n 等 3000 ms。第一次 open 失败时重试一次。
--gear 只写进 SHOTS.md 并决定 h-* 是否必拍（mixed、show 必拍，clear 也拍，列为选拍）。
--carrier [id]：读 library/carriers.json 的 viewport。窄载体（宽 <600）用载体视口代替 m-*，
  不拍 d-* 与 t-*。宽载体用载体主视口代替 d-*。不给 id 或找不到文件时用默认视口并提示。
--docks：逗号分隔的 `#id` 或 hash。每个停靠点执行 location.hash='<id>'，等 3000 ms 后拍。

已知不能拍：打印预览（print，clear 档必拍，需 `agent-browser pdf` 人工）、折叠展开后（fold-open）、
  深色整页（dark-page）、减少动效整页（r-page）。这些在 SHOTS.md 末尾列为"未拍"。

用法：python3 -I shots.py --url URL --out DIR [--gear clear|mixed|show] [--carrier [id]] [--docks "#s1,#s5"]
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import time

MAX_PAGES = 12
AB = shutil.which('agent-browser') or os.path.expanduser('~/.local/bin/agent-browser')
LOG = []
OK = [False]  # 最近一次 ab() 是否成功（返回码 0）


def ab(*args, timeout=90):
    """运行 agent-browser，返回标准输出文本。失败返回空串并记录。"""
    OK[0] = False
    try:
        r = subprocess.run([AB, *args], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        LOG.append('命令失败 %s: %s（超时）' % (' '.join(args)[:60], e))
        return ''
    if r.returncode != 0:
        msg = (r.stderr or r.stdout).strip()
        LOG.append('命令失败 %s: %s%s' % (' '.join(args)[:60], msg[:120], '（超时）' if 'timed out' in msg else ''))
        return ''
    OK[0] = True
    return r.stdout


def open_url(url):
    for i in range(2):  # 第一次 open 可能失败，重试一次
        if ab('open', url, timeout=45):
            return True
        if LOG and '超时' in LOG[-1]:  # 外链字体加载慢造成超时，页面通常已可用，不再重试
            return True
    return False


def num(s, default=0):
    try:
        return int(float(s.strip().strip('"')))
    except ValueError:
        return default


def carrier_viewport(cid):
    path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'library', 'carriers.json'))
    if not cid:
        return None, '未给载体 id，用默认视口'
    try:
        data = json.load(open(path, encoding='utf-8'))
    except (OSError, ValueError):
        return None, 'carriers.json 不存在或不可读，用默认视口'
    for c in data.get('carriers', []):
        if c.get('id') == cid:
            v = c.get('viewport', {})
            w = v.get('main', v.get('width_css_px'))
            if isinstance(w, list):
                w = w[0]
            h = v.get('height_css_px')
            if isinstance(h, list):
                h = h[-1]
            if not h:
                m = v.get('main')
                h = m[1] if isinstance(m, list) and len(m) > 1 else 900
            if isinstance(v.get('main'), list):
                w = v['main'][0]
            return (int(w), int(h)), '载体 %s 视口 %sx%s' % (cid, w, h)
    return None, '载体 %s 不在 carriers.json，用默认视口' % cid


def main():
    ap = argparse.ArgumentParser(description='按 review.md 截图清单批量截图，写 SHOTS.md 与 console.txt。')
    ap.add_argument('--url', required=True, help='页面地址，如 http://127.0.0.1:8112/page/index.html')
    ap.add_argument('--out', required=True, help='输出目录（不存在会创建）')
    ap.add_argument('--gear', default='mixed', choices=['clear', 'mixed', 'show'], help='档位，写进 SHOTS.md')
    ap.add_argument('--carrier', nargs='?', const='', help='载体 id（见 library/carriers.json）')
    ap.add_argument('--docks', default='', help='停靠点列表，逗号分隔，如 "#s1,#s5"')
    a = ap.parse_args()
    if not os.path.isfile(AB) and not shutil.which('agent-browser'):
        sys.exit('找不到 agent-browser。先执行 export PATH=$PATH:~/.local/bin')
    os.makedirs(a.out, exist_ok=True)
    rows, notes = [], []

    cvp, cmsg = (None, '')
    if a.carrier is not None:
        cvp, cmsg = carrier_viewport(a.carrier)
        notes.append('--carrier：' + cmsg)
    narrow = bool(cvp and cvp[0] < 600)
    dvp = cvp if (cvp and not narrow) else (1440, 900)
    mvp = cvp if narrow else (390, 844)

    state = {'vp': None, 'media': None}

    def setup(vp, media='light'):
        """设置视口与媒体偏好，改了媒体就重新打开页面。"""
        if state['media'] != media:
            ab('set', 'media', *(['light', 'reduced-motion'] if media == 'reduced-motion' else [media]))
            state['media'] = media
            state['vp'] = None
            if not open_url(a.url):
                notes.append('打开页面失败：' + a.url)
        if state['vp'] != vp:
            ab('set', 'viewport', str(vp[0]), str(vp[1]))
            state['vp'] = vp
            time.sleep(0.4)

    def shoot(name, vp, st, use, y=None, wait=1500):
        if y is not None:
            ab('eval', 'window.scrollTo(0,%d)' % y)
        ab('wait', str(wait))
        path = os.path.join(a.out, name + '.png')
        tmp = os.path.join(a.out, name + '.new.png')
        if os.path.exists(tmp):
            os.remove(tmp)
        ab('screenshot', tmp)  # 先拍到临时名，成功才替换，失败时保留上次的旧图
        ok = OK[0] and os.path.isfile(tmp) and os.path.getsize(tmp) > 0
        if ok:
            os.replace(tmp, path)
        else:
            if os.path.exists(tmp):
                os.remove(tmp)
            if os.path.isfile(path):
                notes.append('%s.png 本次截图失败，目录里是上一次的旧图，不能当本次结果' % name)
        rows.append((name + '.png' if ok else name + '（失败）', '%dx%d' % vp, st, use))

    def paged(prefix, vp, media='light'):
        setup(vp, media)
        ab('eval', 'window.scrollTo(0,0)')
        total = num(ab('eval', 'document.documentElement.scrollHeight'), vp[1])
        n = max(1, math.ceil(total / vp[1]))
        picks = list(range(n)) if n <= MAX_PAGES else sorted({round(i * (n - 1) / (MAX_PAGES - 1)) for i in range(MAX_PAGES)})
        for k, i in enumerate(picks, 1):
            shoot('%s-page-%d' % (prefix, k), vp, '整页第 %d / %d 屏，滚动 %d px' % (i + 1, n, i * vp[1]), '整页分屏', y=i * vp[1])
        shoot('%s-end' % prefix, vp, '页尾', '页脚可达', y=max(0, total - vp[1]))
        return total

    # 初始打开
    if not open_url(a.url):
        sys.exit('打开页面失败：' + a.url)
    ab('console', '--clear')

    # 桌面（或宽载体）
    if not narrow:
        setup(dvp)
        shoot('d-fold', dvp, '首屏', '首屏可读、层级', y=0)
        paged('d', dvp)
        setup((768, 1024))
        shoot('t-fold', (768, 1024), '首屏', '平板断点', y=0)
    setup(mvp)
    shoot('m-fold', mvp, '首屏', '手机首屏', y=0)
    paged('m', mvp)

    # 深色、减少动效
    setup(dvp if not narrow else mvp, 'dark')
    shoot('dark-fold', dvp if not narrow else mvp, '深色首屏', '深色对比', y=0)
    setup(dvp if not narrow else mvp, 'reduced-motion')
    shoot('r-fold', dvp if not narrow else mvp, '减少动效首屏', 'Reduce Motion 退路', y=0)

    # 键盘与 hover，用浅色默认状态
    pv = dvp if not narrow else mvp
    state['media'] = None
    setup(pv, 'light')
    ab('eval', 'window.scrollTo(0,0)')
    for i in range(1, 4):
        ab('press', 'Tab')
        shoot('k-%d' % i, pv, 'Tab 第 %d 次' % i, '键盘焦点可见', wait=500)
    ab('eval', 'document.activeElement && document.activeElement.blur()')
    pos = ab('eval', "(()=>{const e=[...document.querySelectorAll('a,button')].find(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.left>=0&&r.top>=0&&r.bottom<=innerHeight&&r.right<=innerWidth});if(!e)return '';const r=e.getBoundingClientRect();return Math.round(r.x+r.width/2)+','+Math.round(r.y+r.height/2)})()").strip().strip('"')
    ab('mouse', 'move', '1', '1')
    shoot('h-rest', pv, '第一个可见 a 或 button，未悬停', 'hover 前', wait=500)
    if pos and ',' in pos:
        x, y = pos.split(',')
        ab('mouse', 'move', x, y)
    else:
        ab('hover', 'a')
        notes.append('首屏内无可点元素，h-hover 用 hover "a" 退路')
    shoot('h-hover', pv, '同一目标悬停', 'hover 后', wait=500)

    # 停靠点
    docks = [d.strip() for d in a.docks.split(',') if d.strip()]
    for i, d in enumerate(docks, 1):
        ab('eval', "location.hash='%s'" % d.lstrip('#').replace("'", ''))
        shoot('stage-%d' % i, pv, '停靠 %s' % d, '舞台状态', wait=3000)

    con = ab('console')
    with open(os.path.join(a.out, 'console.txt'), 'w', encoding='utf-8') as f:
        f.write(con or '（无控制台输出）\n')
    if LOG:
        with open(os.path.join(a.out, 'console.txt'), 'a', encoding='utf-8') as f:
            f.write('\n## 脚本命令失败记录\n' + '\n'.join(LOG) + '\n')

    with open(os.path.join(a.out, 'SHOTS.md'), 'w', encoding='utf-8') as f:
        f.write('# SHOTS\n\n页面：%s。档位：%s。\n\n| 文件名 | 视口 | 状态 | 用途 |\n|---|---|---|---|\n' % (a.url, a.gear))
        for r in rows:
            f.write('| %s |\n' % ' | '.join(r))
        f.write('\n未拍（人工补）：print（clear 档必拍）、fold-open、dark-page、r-page。\n')
        for n in notes:
            f.write('\n注：' + n)
        if LOG:
            f.write('\n\n命令失败 %d 次，详见 console.txt。\n' % len(LOG))
    shots = [r for r in rows if '失败' not in r[0]]
    print('| 文件名 | 视口 | 状态 | 用途 |\n|---|---|---|---|')
    for r in rows:
        print('| %s |' % ' | '.join(r))
    print('\nresult: %d FAIL, %d WARN, %d 人工' % (len(rows) - len(shots), len(LOG), 1))
    sys.exit(1 if len(rows) - len(shots) else 0)


if __name__ == '__main__':
    main()
