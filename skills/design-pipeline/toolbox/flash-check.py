#!/usr/bin/env python3
"""flash-check.py 浮夸度静态检查（flash-rules.md 第 2、3 节）。Python 3.12 标准库。

用途：对已构建的 HTML 页面做浮夸度判定表里"脚本能查"的静态项。
  无限循环、pin 总屏高、Reduce Motion 分支数、WebGL 画布数、backdrop-filter 元素数。
  其余项（动效占屏比例、同屏运动数、首屏可读、首屏时间、遮挡、闪烁）输出"人工"并给一句测法。
什么时候跑：S5 门禁（页面做完后）、S6 验收（每轮评审前）。
输出去哪：stdout 的 Markdown 表整段贴进 `05-评审/ROUND-<n>.md`。
退出码：有 FAIL 为 1，否则 0。

输入读法：除内联 <style>、<script> 外，还内联页面本地的 <link rel=stylesheet>、<script src>，
并跟随 JS 的 import 与 CSS 的 @import（E1 教训：只扫内联会漏掉全部令牌与动效代码）。

已知不能查：
  - 编译后才出现的动效（打包产物外的运行时生成代码）。
  - 相机类页面的 pin 来自自写代码。请在停靠元素上写 data-pin-screens="N"，
    脚本也会按 `return N * vh` 估算停靠体长，结果标"估算"，须人工复核。
  - rAF 是否真的无限循环。脚本只查有无 cancelAnimationFrame 与暂停控件。
  - --shots 的像素差分需要 Pillow。没有 Pillow 时跳过并说明。

用法：python3 -I flash-check.py index.html [--gear clear|mixed|show] [--shots 截图目录]
"""
import argparse
import os
import re
import sys

PIN_MAX = 5.0  # 屏高，flash-rules.md 第 2 节"高"档上限，E1 校准后不变
LOOP_MAX = {'clear': 0, 'mixed': 1, 'show': 2}
MANUAL = [
    ('动效占屏比例', '录屏逐帧差分，算变化像素占视口的最大值。可用 --shots 做两张图粗差分'),
    ('同屏运动元素数', '各停靠屏运行 `document.getAnimations().length`，取最大值'),
    ('首屏可读内容', '加载后 0 ms 截图，看标题、一句说明、主操作是否可读'),
    ('首屏出现内容时间', 'Lighthouse LCP，节流 4G 与中端 CPU'),
    ('对正文的遮挡', '动效层与正文边界框求交，再取背景对比度（>=4.5:1）'),
    ('闪烁', '录屏逐帧看亮度变化，1 秒内闪光不超过 3 次'),
]


MISSING = []
UNRESOLVED = []  # 本地引用但文件不存在（含站点根相对路径）
REMOTE = []  # http(s) 外链，脚本不下载，内容未检查


def read(path):
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            return f.read()
    except OSError:
        MISSING.append(path)
        return ''


def load_sources(html_path, root=None):
    """返回 (html, css, js)。css 与 js 含内联与本地外链（递归 import/@import）。"""
    base = os.path.dirname(os.path.abspath(html_path))
    site_root = os.path.abspath(root) if root else base
    html = read(html_path)
    css, js, seen = [], [], set()
    css += re.findall(r'<style[^>]*>(.*?)</style>', html, re.S | re.I)
    for body in re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', html, re.S | re.I):
        js.append(body)

    def local(ref, frm):
        if ref.startswith('data:'):
            return None
        if re.match(r'^(https?:)?//', ref):
            if ref not in REMOTE:
                REMOTE.append(ref)
            return None
        r = ref.split('?')[0].split('#')[0]
        # 以 / 开头的引用相对站点根（--root，默认为 HTML 所在目录），不是文件系统根
        p = os.path.normpath(os.path.join(site_root, r.lstrip('/')) if r.startswith('/') else os.path.join(frm, r))
        if not os.path.isfile(p):
            note = '%s（引用自 %s）' % (ref, os.path.basename(html_path) if frm == base else os.path.relpath(frm, base))
            if note not in UNRESOLVED:
                UNRESOLVED.append(note)
            return None
        return p if p not in seen else None

    def add_css(p):
        seen.add(p)
        t = read(p)
        css.append(t)
        for r in re.findall(r'@import\s+(?:url\()?["\']?([^"\')\s;]+)', t):
            q = local(r, os.path.dirname(p))
            if q:
                add_css(q)

    def add_js(p):
        seen.add(p)
        t = read(p)
        js.append(t)
        for r in re.findall(r'(?:from|import)\s*\(?\s*["\'](\.{1,2}/[^"\']+)["\']', t):
            q = local(r, os.path.dirname(p))
            if q:
                add_js(q)
        # import(`./stage-${id}.js`) 这类模板：按通配符找同目录文件
        for pre, suf in re.findall(r'import\(\s*`(\.{1,2}/[^`$]*)\$\{[^}]*\}([^`?]*)', t):
            d = os.path.join(os.path.dirname(p), os.path.dirname(pre))
            stem = os.path.basename(pre)
            if os.path.isdir(d):
                for fn in sorted(os.listdir(d)):
                    if fn.startswith(stem) and fn.endswith(suf):
                        q = local(os.path.join(os.path.dirname(pre), fn), os.path.dirname(p))
                        if q:
                            add_js(q)

    for tag in re.findall(r'<link\b[^>]*>', html, re.I):
        if re.search(r'rel=["\']?stylesheet', tag, re.I):
            m = re.search(r'href=["\']([^"\']+)', tag, re.I)
            q = local(m.group(1), base) if m else None
            if q:
                add_css(q)
    for tag in re.findall(r'<script\b[^>]*\bsrc=[^>]*>', html, re.I):
        m = re.search(r'src=["\']([^"\']+)', tag, re.I)
        q = local(m.group(1), base) if m else None
        if q:
            add_js(q)
    return html, '\n'.join(css), '\n'.join(js)


def esc(s):
    return str(s).replace('|', '\\|')


def pin_screens(html, css, js):
    """返回 (屏数, 来源说明, 是否估算)。"""
    parts, est = [], False
    total = 0.0
    for m in re.finditer(r'data-pin\s*=\s*["\']([\d.]+)', html):  # 百分比
        total += float(m.group(1)) / 100
        parts.append('data-pin %s%%' % m.group(1))
    for m in re.finditer(r'data-pin-screens\s*=\s*["\']([\d.]+)', html):
        total += float(m.group(1))
        parts.append('data-pin-screens %s' % m.group(1))
    for m in re.finditer(r'pin\s*:\s*true[^}]*?end\s*:\s*[`"\']\+=\$?\{?\s*([\d.]+)\s*%', js, re.S):
        total += float(m.group(1)) / 100
        parts.append('ScrollTrigger end +=%s%%' % m.group(1))
    if total == 0:
        vals = re.findall(r'return\s+([\d.]+)\s*\*\s*vh', js)
        if vals:
            total = sum(float(x) for x in vals)
            parts.append('return N*vh 估算 %s' % '+'.join(vals))
            est = True
    return total, ', '.join(parts) or '未检出', est


def shots_diff(shots_dir):
    try:
        from PIL import Image, ImageChops  # noqa
    except Exception:
        return None, 'Pillow 不可用，跳过像素差分。人工对照 d-fold 与 r-fold 截图'
    names = sorted(f for f in os.listdir(shots_dir) if f.endswith('.png'))
    a = next((n for n in names if n.startswith('d-fold')), None)
    b = next((n for n in names if n.startswith('r-fold')), None)
    if not (a and b):
        return None, '目录里没有 d-fold 与 r-fold 两张同视口图'
    from PIL import Image, ImageChops
    ia, ib = Image.open(os.path.join(shots_dir, a)).convert('L'), Image.open(os.path.join(shots_dir, b)).convert('L')
    if ia.size != ib.size:
        return None, '两张图尺寸不同，无法差分'
    diff = ImageChops.difference(ia, ib).point(lambda v: 255 if v > 24 else 0)
    ratio = sum(1 for v in diff.getdata() if v) / (ia.size[0] * ia.size[1])
    return ratio, '%s 对 %s，差异像素占 %.1f%%' % (a, b, ratio * 100)


def main():
    ap = argparse.ArgumentParser(description='浮夸度静态检查。读 HTML 与其本地 CSS、JS，输出 Markdown 表。有 FAIL 退出码为 1。')
    ap.add_argument('html', help='页面 index.html 路径')
    ap.add_argument('--gear', default='mixed', choices=list(LOOP_MAX), help='档位：clear、mixed、show。默认 mixed')
    ap.add_argument('--root', help='站点根目录。页面里以 / 开头的引用按此解析，默认为 HTML 所在目录')
    ap.add_argument('--shots', help='截图目录（shots.py 的输出）。有 Pillow 时做 d-fold 与 r-fold 差分')
    a = ap.parse_args()
    html, css, js = load_sources(a.html, a.root)
    rows, fails, warns, manual = [], 0, 0, 0

    def row(item, res, val, why):
        nonlocal fails, warns, manual
        fails += res == 'FAIL'
        warns += res == 'WARN'
        manual += res == '人工'
        rows.append((item, res, val, why))

    # 1 无限循环
    # css 已含内联 <style> 块，HTML 只补 style="..." 属性，避免同一段 CSS 数两次
    attrs = '\n'.join(a or b for a, b in re.findall(r'\bstyle\s*=\s*"([^"]*)"|\bstyle\s*=\s*\'([^\']*)\'', html))
    css_all = css + '\n' + attrs
    inf_css = len(re.findall(r'\binfinite\b', css_all))
    inf_js = len(re.findall(r'\binfinite\b|repeat\s*:\s*-1', js))
    raf = len(re.findall(r'requestAnimationFrame', js))
    caf = len(re.findall(r'cancelAnimationFrame', js))
    pause = bool(re.search(r'暂停|pause|aria-pressed|data-pause', html, re.I))
    n_loop = inf_css + inf_js
    lim = LOOP_MAX[a.gear]
    if n_loop > 2 or (n_loop > 0 and not pause) or (n_loop > lim and a.gear == 'clear'):
        res = 'FAIL'
    elif n_loop > lim:
        res = 'WARN'
    else:
        res = 'PASS'
    row('无限循环动效数', res, 'infinite/repeat:-1 共 %d（CSS %d，JS %d），暂停控件 %s' % (n_loop, inf_css, inf_js, '有' if pause else '无'),
        '%s 档上限 %d，须可暂停。>2 或不可暂停为过量' % (a.gear, lim))
    if raf:
        res = 'PASS' if (caf or pause) else 'WARN'
        row('rAF 循环', res, 'requestAnimationFrame %d 处，cancelAnimationFrame %d 处' % (raf, caf),
            '有取消或暂停路径视为可停。是否真循环须人工读代码')

    # 2 pin 总屏高
    scr, src, est = pin_screens(html, css, js)
    if scr > PIN_MAX:
        res = 'FAIL'
    elif scr > 0 and a.gear == 'clear':
        res = 'WARN'
    else:
        res = 'PASS'
    row('pin 总屏高', res, '%.1f 屏（%s）%s' % (scr, src, '，估算' if est else ''), '上限 %g 屏。相机页按停靠与 pin 计' % PIN_MAX)

    # 3 Reduce Motion
    rm_css = len(re.findall(r'prefers-reduced-motion', css_all))
    rm_js = len(re.findall(r'prefers-reduced-motion', js))
    row('Reduce Motion 退路', 'FAIL' if rm_css + rm_js == 0 else 'PASS', '分支共 %d（CSS %d，JS %d）' % (rm_css + rm_js, rm_css, rm_js),
        '0 处为过量。开启后截图是否完整须人工看 r-fold')

    # 4 WebGL 画布
    cv_html = len(re.findall(r'<canvas\b', html, re.I))
    cv_js = len(re.findall(r'createElement\(\s*["\']canvas', js))
    gl = len([ln for ln in (js + html).splitlines() if re.search(r'getContext\(\s*["\']webgl', ln)])
    row('WebGL 画布数', 'WARN' if gl > 1 else 'PASS', '<canvas> %d，JS 建 canvas %d，getContext(webgl) %d 处' % (cv_html, cv_js, gl),
        '>1 处须确认不在同屏同时运行（软件渲染下 1 到 2 帧每秒）')

    # 5 backdrop-filter
    bf = len(re.findall(r'backdrop-filter\s*:', css_all))
    row('backdrop-filter 元素数', 'WARN' if bf > 3 else 'PASS', '%d 处' % bf, '>3 处在低端机上掉帧')

    for item, how in MANUAL:
        row(item, '人工', '-', how)

    if a.shots:
        ratio, msg = shots_diff(a.shots) if os.path.isdir(a.shots) else (None, '--shots 目录不存在')
        row('截图差分', 'PASS' if ratio is not None else '人工', msg, 'Reduce Motion 开关前后差异过大说明有内容只靠动效出现')

    print('# flash-check %s（档位 %s）\n' % (os.path.basename(os.path.dirname(os.path.abspath(a.html))) + '/' + os.path.basename(a.html), a.gear))
    print('| 项 | 结果 | 实测 | 判定依据 |')
    print('|---|---|---|---|')
    for r in rows:
        print('| %s |' % ' | '.join(esc(x) for x in r))
    if MISSING or UNRESOLVED or REMOTE:
        print('\n未覆盖项：下列引用的内容没有被检查。动效若在这些文件里，上面的 PASS 不代表通过：')
        for m in MISSING + UNRESOLVED:
            print('- 本地读不到：%s' % m)
        for m in REMOTE:
            print('- 外部链接未检查：%s' % m)
        warns += len(MISSING) + len(UNRESOLVED)
    print('\nresult: %d FAIL, %d WARN, %d 人工' % (fails, warns, manual))
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
