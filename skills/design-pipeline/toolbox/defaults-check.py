#!/usr/bin/env python3
"""defaults-check.py 默认值检查（anti-sameness.md 第 2 节 X1 到 X17，X18 到 X20 靠看截图）。Python 3.12 标准库。

用途：对已构建的 HTML 页面查 X 清单里"grep 类"各项，并可与另一个页面比同质化。
  脚本查：X1 X2 X5 X6 X7 X8 X9 X11 X12 X14 X15。
  人工查：X3 X4 X10 X13 X16 X17（看图类），输出"人工"并给一句测法。
什么时候跑：S3 定稿后查方案对应的原型（可选）、S5 门禁、S6 验收。机制 M6、M7 用它。
输出去哪：stdout 的 Markdown 表整段贴进 `05-评审/ROUND-<n>.md`。
退出码：有 FAIL 为 1，否则 0。命中 2 项以上的 FAIL 或 WARN，按 M6 退回 S3。

输入读法：内联页面本地的 <link rel=stylesheet>、<script src>，跟随 import 与 @import
（E1 教训：只扫内联 <style> 会漏掉全部令牌）。

--compare 另一页（html 文件或目录，目录取其中 index.html）：
  比四个维度的相似度：:root 色相直方图、字体族集合、@keyframes 名集合、data-layout 族集合。
  四项相似度的平均 >60% 判"与上一项目同套"FAIL。

已知不能查：
  - 色值只认 #hex、rgb()、hsl()。oklch、color-mix 与 JS 生成的颜色不查。
  - X7 只数取值种类，不判断各块是否真的同款。
  - X14 数 @keyframes 名与 JS 入场位移种类，不看实际视觉。
  - 引擎自带关键帧（如 `engine.css`）也会计入。判定时人工扣除。

用法：python3 -I defaults-check.py index.html [--root 站点根目录] [--compare 另一页或目录 [--compare-root 比较页站点根]]
"""
import argparse
import colorsys
import os
import re
import sys

DEFAULT_FONTS = re.compile(r'\b(inter|roboto|system-ui|-apple-system|blinkmacsystemfont|segoe ui|helvetica neue|arial)\b', re.I)
HEAD_SEL = re.compile(r'(^|[\s,>.#\[])(h[1-3]|display|title|hero|headline|heading|h-?big)\b', re.I)
LABEL_SEL = re.compile(r'(label|tag|eyebrow|meta|chip|kicker|caption|badge|note|small)', re.I)
MANUAL = [
    ('X3', '三卡片行', '看截图与 DOM：一行三张同尺寸卡'),
    ('X4', '居中英雄区加单 CTA', '看 d-fold 首屏截图'),
    ('X10', '装饰编号', '看截图，对照蓝图：内容不是序列却标 01 / 02 / 03'),
    ('X13', '只换一个词颜色或斜体的标题', '看截图'),
    ('X16', '大数字加小标签加渐变强调的 hero', '看 d-fold 首屏截图'),
    ('X17', '组件手法卡同源', '看 03-页面规划.md 的组件手法列：同页 3 张以上卡同一 tasteskill_id 前缀或同一 refs 站点'),
]


MISSING = []
UNRESOLVED = []  # 本地引用但文件不存在（含站点根相对路径）
REMOTE = []  # http(s) 外链，脚本不下载，内容未检查
REMOTE_CSS = []  # 其中的远程样式表（Google Fonts 除外）：令牌可能在里面，影响比较结论


def read(path):
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            return f.read()
    except OSError:
        MISSING.append(path)
        return ''


def load_sources(html_path, root=None):
    """返回 (html, css, js)，含本地外链与递归 import。"""
    base = os.path.dirname(os.path.abspath(html_path))
    site_root = os.path.abspath(root) if root else base
    html = read(html_path)
    css = re.findall(r'<style[^>]*>(.*?)</style>', html, re.S | re.I)
    js = [b for b in re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', html, re.S | re.I)]
    seen = set()

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
        for pre, suf in re.findall(r'import\(\s*`(\.{1,2}/[^`$]*)\$\{[^}]*\}([^`?]*)', t):
            d = os.path.join(os.path.dirname(p), os.path.dirname(pre))
            if os.path.isdir(d):
                for fn in sorted(os.listdir(d)):
                    if fn.startswith(os.path.basename(pre)) and fn.endswith(suf):
                        q = local(os.path.join(os.path.dirname(pre), fn), os.path.dirname(p))
                        if q:
                            add_js(q)

    for tag in re.findall(r'<link\b[^>]*>', html, re.I):
        if re.search(r'rel=["\']?stylesheet', tag, re.I):
            m = re.search(r'href=["\']([^"\']+)', tag, re.I)
            q = local(m.group(1), base) if m else None
            if m and re.match(r'^(https?:)?//', m.group(1)) and not re.search(r'fonts\.(googleapis|gstatic)\.com', m.group(1)) and m.group(1) not in REMOTE_CSS:
                REMOTE_CSS.append(m.group(1))
            if q:
                add_css(q)
    for tag in re.findall(r'<script\b[^>]*\bsrc=[^>]*>', html, re.I):
        m = re.search(r'src=["\']([^"\']+)', tag, re.I)
        q = local(m.group(1), base) if m else None
        if q:
            add_js(q)
    return html, '\n'.join(css), '\n'.join(js)


# ---------- 色值 ----------
HEX = re.compile(r'#([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b')
RGB = re.compile(r'rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)(?:\s*[,/]\s*([\d.]+%?))?')
HSL = re.compile(r'hsla?\(\s*([\d.]+)(?:deg)?[\s,]+([\d.]+)%[\s,]+([\d.]+)%')


def parse_colors(text):
    """返回 [(r,g,b)] 0-255。"""
    out = []
    for m in HEX.finditer(text):
        h = m.group(1)
        if len(h) == 3:
            h = ''.join(c * 2 for c in h)
        out.append(tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)))
    for m in RGB.finditer(text):
        al = m.group(4)  # 半透明色（阴影、遮罩）不是底色，跳过
        if al is not None and (float(al.rstrip('%')) / (100 if al.endswith('%') else 1)) < 0.9:
            continue
        out.append(tuple(min(255, float(x)) for x in m.groups()[:3]))
    for m in HSL.finditer(text):
        hh, ss, ll = float(m.group(1)) / 360, float(m.group(2)) / 100, float(m.group(3)) / 100
        out.append(tuple(round(c * 255) for c in colorsys.hls_to_rgb(hh, ll, ss)))
    return out


def hsl(rgb):
    h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
    return h * 360, s, l


def dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def near(colors, target, thr=40):
    return [c for c in colors if dist(c, target) < thr]


def rules(css):
    """粗解析 CSS 规则，返回 [(选择器, 声明文本)]。忽略 @keyframes 内部层级的精确性。"""
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    return [(s.strip(), d) for s, d in re.findall(r'([^{}]+)\{([^{}]*)\}', css)]


def root_tokens(css):
    out = {}
    for sel, body in rules(css):
        if ':root' in sel:
            for n, v in re.findall(r'(--[\w-]+)\s*:\s*([^;]+)', body):
                out[n] = v.strip()
    return out


def visible_text(html):
    t = re.sub(r'<(script|style)\b.*?</\1>', ' ', html, flags=re.S | re.I)
    return re.sub(r'<[^>]+>', '\x00', t)  # 标签换成分隔符，保留文本边界


def families(css):
    fam = set()
    for v in re.findall(r'font-family\s*:\s*([^;}]+)', css):
        first = v.split(',')[0].strip().strip('"\'')
        if first and not first.startswith('var('):
            fam.add(first.lower())
    for n, v in root_tokens(css).items():
        if 'font' in n:
            first = v.split(',')[0].strip().strip('"\'')
            if first and not first.startswith('var('):
                fam.add(first.lower())
    return fam


def keyframes(css):
    return set(re.findall(r'@keyframes\s+([\w-]+)', css))


def layouts(html):
    return set(re.findall(r'data-layout\s*=\s*["\']([^"\']+)', html))


def hue_hist(css):
    bins = [0] * 13  # 0..11 为 30 度一档，12 为无彩色
    for n, v in root_tokens(css).items():
        for c in parse_colors(v):
            h, s, l = hsl(c)
            bins[12 if s < 0.12 or l < 0.06 or l > 0.96 else int(h // 30) % 12] += 1
    return bins


def jaccard(a, b):
    return len(a & b) / len(a | b) if (a | b) else 0.0


def hist_sim(a, b):
    sa, sb = sum(a) or 1, sum(b) or 1
    return sum(min(x / sa, y / sb) for x, y in zip(a, b))


def pct(x):
    return '%d%%' % round(x * 100)


def main():
    ap = argparse.ArgumentParser(description='默认值检查（X1 到 X16 的 grep 类各项）。读 HTML 与其本地 CSS、JS，输出 Markdown 表。有 FAIL 退出码为 1。')
    ap.add_argument('html', help='页面 index.html 路径')
    ap.add_argument('--root', help='站点根目录。页面里以 / 开头的引用按此解析，默认为 HTML 所在目录')
    ap.add_argument('--compare-root', help='比较页面的站点根目录。默认沿用 --root，没有 --root 时为比较页面所在目录')
    ap.add_argument('--compare', help='另一个页面（html 文件或目录），比同质化')
    a = ap.parse_args()
    if not os.path.isfile(a.html):
        print('错误：无法读取 %s' % a.html)
        sys.exit(2)
    html, css, js = load_sources(a.html, a.root)
    main_incomplete = bool(MISSING or UNRESOLVED or REMOTE_CSS)  # 主页面有没读到的样式资源
    css_nc = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    rows, cnt = [], {'FAIL': 0, 'WARN': 0, '人工': 0}

    def row(item, name, res, val, why):
        cnt[res] = cnt.get(res, 0) + 1
        rows.append((item, name, res, val, why))

    # X1 字体：标题用 Inter/Roboto/系统字体
    hits = []
    toks = root_tokens(css)
    for n, v in toks.items():
        if re.search(r'display|head|title|hero', n, re.I) and 'font' in n and DEFAULT_FONTS.search(v.split(',')[0]):
            hits.append('%s: %s' % (n, v[:40]))
    for sel, body in rules(css_nc):
        m = re.search(r'font-family\s*:\s*([^;]+)', body)
        if m and HEAD_SEL.search(sel) and DEFAULT_FONTS.search(m.group(1).split(',')[0]):
            hits.append('%s: %s' % (sel[:30], m.group(1)[:30]))
    fams = sorted(families(css_nc))
    row('X1', '默认字体作显示字', 'FAIL' if hits else 'PASS', ('；'.join(hits[:3]) if hits else '标题字体族：' + ', '.join(fams[:4])),
        '标题首选字体不得是 Inter、Roboto、系统字体')

    # X2 紫到靛蓝渐变
    purple, total_grad = 0, 0
    for g in re.findall(r'(?:linear|radial|conic)-gradient\(([^;{}]*)', css_nc + html):
        total_grad += 1
        if g.strip().startswith('linear') or True:
            for c in parse_colors(g):
                h, s, l = hsl(c)
                if 250 <= h <= 290 and s > 0.2 and 0.1 < l < 0.9:
                    purple += 1
                    break
    row('X2', '紫到靛蓝渐变', 'FAIL' if purple else 'PASS', '色相 250 到 290 的渐变 %d / 共 %d' % (purple, total_grad), '用户指定的除外')

    # X5 奶油底加陶土
    allc = parse_colors(css_nc)
    bgc = []  # 只取背景令牌与页面级选择器的背景，避免把遮罩、文字墨色当底色
    for sel, body in rules(css_nc):
        page_sel = bool(re.search(r'(^|[\s,])(html|body|:root|main)\b', sel)) and '::' not in sel
        for n, v in re.findall(r'(--[\w-]*(?:bg|background|paper|surface|ground)[\w-]*|background(?:-color)?)\s*:\s*([^;]+)', body):
            if n.startswith('--') or page_sel:
                bgc += parse_colors(re.sub(r'var\([^,)]+,[^)]*\)', '', v))  # var(--x, #fb) 的后备色不算
    cream, clay = [c for c in near(bgc, (0xF4, 0xF1, 0xEA)) if c[0] - c[2] >= 10], near(allc, (0xD9, 0x77, 0x57))
    r5 = 'FAIL' if cream and clay else ('WARN' if cream or clay else 'PASS')
    row('X5', '奶油底加陶土强调', r5, '奶油底（背景类声明）%d，陶土 %d（RGB 距离 <40）' % (len(cream), len(clay)), '奶油须偏暖（R-B>=10）。两者同现为命中，衬线字须看截图')

    # X6 近黑底加酸绿或朱红
    black = [c for c in near(bgc, (0x0B, 0x0B, 0x0B), 24) + near(bgc, (0x11, 0x11, 0x11), 24) if max(c) - min(c) < 8]
    acid = [c for c in allc if (lambda h, s, l: s > 0.7 and 0.4 < l < 0.7 and (70 <= h <= 150 or h <= 12 or h >= 350))(*hsl(c))]
    r6 = 'FAIL' if black and acid else ('WARN' if black else 'PASS')
    row('X6', '近黑底加酸绿或朱红', r6, '近黑底（背景类声明）%d，酸绿或朱红类强调 %d' % (len(black), len(acid)), '近黑与强调同现为命中')

    # X7 圆角与阴影取值种类
    radii = set(v.strip() for v in re.findall(r'border-radius\s*:\s*([^;}]+)', css_nc) if v.strip() not in ('0', '0px', '50%', 'inherit'))
    shadows = set(v.strip() for v in re.findall(r'box-shadow\s*:\s*([^;}]+)', css_nc) if v.strip() != 'none')
    r7 = 'WARN' if (len(radii) == 1 and len(shadows) == 1) else 'PASS'
    row('X7', '同款圆角卡', r7, '圆角 %d 种，阴影 %d 种' % (len(radii), len(shadows)), '各只有 1 种为同款。0 种视为无')

    # X8 全大写
    up = len(re.findall(r'text-transform\s*:\s*uppercase', css_nc))
    row('X8', '全大写 eyebrow', 'WARN' if up else 'PASS', 'text-transform: uppercase %d 处' % up, '中文页出现多为西文小标签，须看是否 eyebrow')

    # X9 点号连接元信息
    text = visible_text(html)
    dots = [t for t in text.split('\x00') if re.search(r'\S\s+·\s+\S', t)]
    row('X9', '点号连接元信息', 'WARN' if dots else 'PASS', '含 " · " 的文本节点 %d 个%s' % (len(dots), ('，如 ' + dots[0].strip()[:24]) if dots else ''), '"A · B · C" 属模板味')

    # X11 等宽字体做小标签
    mono = [sel for sel, body in rules(css_nc) if re.search(r'font-family\s*:[^;]*monospace', body) and LABEL_SEL.search(sel)]
    row('X11', '等宽字体做小标签', 'WARN' if mono else 'PASS', '%d 个选择器%s' % (len(mono), ('，如 ' + mono[0][:30]) if mono else ''), '选择器含 label、tag、meta、chip 等且用 monospace')

    # X12 →
    arrows = [t for t in text.split('\x00') if '→' in t]
    arrows_css = len(re.findall(r'content\s*:\s*["\'][^"\']*→', css_nc))
    row('X12', '链接与按钮后加 →', 'WARN' if arrows or arrows_css else 'PASS', '文本含 → %d 个节点，CSS content 含 → %d 处' % (len(arrows), arrows_css),
        '用在流程图里的箭头是内容，不算。须人工区分')

    # X14 入场类型种类
    kf = keyframes(css_nc)
    ty = len(re.findall(r'translate[YXY]?\(\s*-?[\d.]+(?:px|%|rem)', js))
    row('X14', '每章同一种入场', 'WARN' if len(kf) <= 1 else 'PASS', '@keyframes %d 个（%s），JS 位移写法 %d 处' % (len(kf), ', '.join(sorted(kf)[:5]), ty), '只有 1 种 @keyframes 视为同一种入场。引擎自带的须人工扣除')

    # X15 装饰渐变数
    gr = len(re.findall(r'(?:linear|radial|conic)-gradient\(', css_nc + html))
    row('X15', '渐变洗色作装饰背景', 'WARN' if gr > 4 else 'PASS', '渐变 %d 处' % gr, '>4 处须逐处确认是否承载含义（图表色阶、纸纹除外）')

    for it, name, how in MANUAL:
        row(it, name, '人工', '-', how)

    rows.sort(key=lambda r: int(r[0][1:]))
    name = os.path.basename(os.path.dirname(os.path.abspath(a.html))) + '/' + os.path.basename(a.html)
    print('# defaults-check %s\n' % name)
    print('| 编号 | 默认值 | 结果 | 实测 | 判定依据 |')
    print('|---|---|---|---|---|')
    for r in rows:
        print('| %s |' % ' | '.join(str(x).replace('|', '\\|') for x in r))

    if a.compare:
        p = a.compare
        if os.path.isdir(p):
            p = os.path.join(p, 'index.html') if os.path.isfile(os.path.join(p, 'index.html')) else next(
                (os.path.join(p, f) for f in sorted(os.listdir(p)) if f.endswith('.html')), p)
        if not os.path.isfile(p):
            print('\n--compare 找不到页面：%s' % a.compare)
            cnt['FAIL'] += 1
        else:
            saved = (MISSING[:], UNRESOLVED[:], REMOTE_CSS[:])
            del MISSING[:], UNRESOLVED[:], REMOTE_CSS[:]
            h2, c2, _ = load_sources(p, a.compare_root or a.root)
            cmp_incomplete = bool(MISSING or UNRESOLVED or REMOTE_CSS)  # 比较页有没读到的样式资源
            MISSING[:] = saved[0] + [m for m in MISSING if m not in saved[0]]
            UNRESOLVED[:] = saved[1] + [m for m in UNRESOLVED if m not in saved[1]]
            REMOTE_CSS[:] = saved[2] + [m for m in REMOTE_CSS if m not in saved[2]]
            incomplete = main_incomplete or cmp_incomplete
            c2 = re.sub(r'/\*.*?\*/', '', c2, flags=re.S)
            dims = [
                ('色相直方图（:root 令牌）', hist_sim(hue_hist(css_nc), hue_hist(c2)), '%s 对 %s' % (hue_hist(css_nc), hue_hist(c2))),
                ('字体族集合', jaccard(families(css_nc), families(c2)), '共有 %s' % (sorted(families(css_nc) & families(c2)) or '无')),
                ('@keyframes 名集合', jaccard(keyframes(css_nc), keyframes(c2)), '共有 %s' % (sorted(keyframes(css_nc) & keyframes(c2))[:6] or '无')),
                ('data-layout 族集合', jaccard(layouts(html), layouts(h2)), '共有 %s' % (sorted(layouts(html) & layouts(h2)) or '无')),
            ]
            avg = sum(d[1] for d in dims) / len(dims)
            print('\n## 同质化比较：%s 对 %s\n' % (name, p))
            print('| 维度 | 相似度 | 备注 |')
            print('|---|---|---|')
            for d in dims:
                print('| %s | %s | %s |' % (d[0], pct(d[1]), str(d[2]).replace('|', '\\|')))
            verdict = 'FAIL' if avg > 0.6 else 'PASS'
            if incomplete and verdict == 'PASS':
                verdict = '不完整'  # 比较页的资源没读全，低相似度可能是漏读造成的，不下 PASS 结论
                cnt['WARN'] += 1
            cnt['FAIL'] += verdict == 'FAIL'
            print('| 平均命中率 | %s | %s（阈值 >60%% 为与上一项目同套%s） |' % (pct(avg), verdict, '。两侧页面有样式资源没读到（本地缺失或远程样式表），见未覆盖项，结论不可靠' if incomplete else ''))

    if MISSING or UNRESOLVED or REMOTE:
        print('\n未覆盖项：下列引用的内容没有被检查。令牌或动效若在这些文件里，上面的 PASS 不代表通过：')
        for m in MISSING + UNRESOLVED:
            print('- 本地读不到：%s' % m)
        for m in REMOTE:
            print('- 外部链接未检查：%s' % m)
        cnt['WARN'] += len(MISSING) + len(UNRESOLVED)
    print('\nresult: %d FAIL, %d WARN, %d 人工' % (cnt['FAIL'], cnt['WARN'], cnt['人工']))
    sys.exit(1 if cnt['FAIL'] else 0)


if __name__ == '__main__':
    main()
