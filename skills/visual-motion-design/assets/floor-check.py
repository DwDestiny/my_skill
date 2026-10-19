#!/usr/bin/env python3
"""Reference-value check for a built HTML page (gears.md 2.1, review.md 0). Python 3 stdlib only.

Checks the parts of F1-F6 that a script can judge. A pass does NOT prove a good design.
A FAIL means the page is below the reference value of its budget preset (a preset is a starting point, not a quality grade; mood decides how much to hold back).

Page conventions the check reads:
  - chapter sections carry data-chapter and data-layout="<family>"
  - the first-screen visual subject carries data-hero-visual and contains svg / img / canvas / picture,
    or is built with CSS 3D (transform-style: preserve-3d in the page CSS)
  - credibility chips use class "tag"
  - motion hooks: data-reveal, data-counter (engine attributes)

Usage: python3 floor-check.py index.html [--gear clear|mixed|show] [--carrier <id>]
--carrier reads design-pipeline/library/carriers.json (min_font, min_hit, viewport) and adds C1-C3
advisory checks: smallest declared font-size, smallest declared control height, viewport meta.
It does not change F1-F6. When carriers.json is missing it prints one line and runs as --gear only.
Local <link rel=stylesheet> files are read together with inline <style> (the tokens live there).
Exit code 1 when any FAIL.
"""
import argparse
import colorsys
import json
import os
import re
import sys
from html.parser import HTMLParser

FLOOR = {  # budget preset (--gear value) -> reference values (layout families, chips per 1000 visible chars max, body text only; chips in table cells are exempt (components.md 4: one per row), needs reveal)
    'clear': (2, 14, False),
    'mixed': (3, 10, True),
    'show': (4, 10, True),
}


class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.styles, self._in_style = [], False
        self.chapters = []           # (id, layout, text_len, tag_count)
        self._stack = []             # open chapter idx stack by tag depth
        self.cur = None
        self.hero_visual = False
        self.hero_marked = False
        self._hero_depth = 0
        self.depth = 0
        self.attr_counts = {'data-reveal': 0, 'data-counter': 0}
        self.in_script = False
        self.pattern_count = 0
        self.in_cell = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.depth += 1
        if tag == 'style':
            self._in_style = True
        if tag == 'script':
            self.in_script = True
        for k in self.attr_counts:
            if k in a:
                self.attr_counts[k] += 1
        if tag == 'pattern':
            self.pattern_count += 1
        if 'data-chapter' in a and tag == 'section':
            self.cur = {'id': a.get('id', '?'), 'layout': a.get('data-layout', ''), 'text': 0, 'tags': 0, 'cell_tags': 0, 'depth': self.depth}
            self.chapters.append(self.cur)
        if tag in ('td', 'th'):
            self.in_cell += 1
        if self.cur is not None and 'tag' in (a.get('class') or '').split():
            self.cur['cell_tags' if self.in_cell else 'tags'] += 1
        if 'data-hero-visual' in a:
            self._hero_depth = self.depth
            self.hero_marked = True
        if self._hero_depth and tag in ('svg', 'img', 'canvas', 'picture'):
            self.hero_visual = True

    def handle_endtag(self, tag):
        if tag == 'style':
            self._in_style = False
        if tag == 'script':
            self.in_script = False
        if tag in ('td', 'th') and self.in_cell:
            self.in_cell -= 1
        if self.cur is not None and tag == 'section' and self.depth == self.cur['depth']:
            self.cur = None
        if self._hero_depth and self.depth == self._hero_depth:
            self._hero_depth = 0
        self.depth -= 1

    def handle_data(self, data):
        if self._in_style:
            self.styles.append(data)
        elif self.cur is not None and not self.in_script:
            self.cur['text'] += len(data.strip())


def hex_to_hls(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hh, ll, ss = colorsys.rgb_to_hls(r, g, b)
    return hh, ll, ss


def linked_css(html, base):
    out = []
    for tag in re.findall(r'<link\b[^>]*>', html, re.I):
        m = re.search(r'href=["\']([^"\']+)', tag, re.I)
        if m and re.search(r'rel=["\']?stylesheet', tag, re.I) and not re.match(r'^(https?:)?//', m.group(1)):
            fp = os.path.normpath(os.path.join(base, m.group(1).split('?')[0]))
            if os.path.isfile(fp):
                out.append(open(fp, encoding='utf-8', errors='replace').read())
    return '\n'.join(out)


def carrier_checks(args, html, css, fails, warns, notes):
    cj = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'design-pipeline', 'library', 'carriers.json'))
    if not os.path.isfile(cj):
        notes.append('carrier: carriers.json not found, ran as --gear only')
        return
    car = next((c for c in json.load(open(cj, encoding='utf-8')).get('carriers', []) if c.get('id') == args.carrier), None)
    if not car:
        fails.append('C0 carrier %s is not in carriers.json' % args.carrier)
        return
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    mf, mh, vw = car.get('min_font', {}).get('value'), car.get('min_hit', {}), car.get('viewport', {}).get('width_css_px')
    sizes = [float(x) for x in re.findall(r'font-size\s*:\s*([\d.]+)px', css)]
    if mf is None:
        notes.append('C1 min font: carrier gives no value (not verified), skipped')
    else:
        small = sorted({s for s in sizes if s < mf})
        (warns if small else notes).append('C1 %d declared px font-sizes below %s (carrier %s): %s' % (len([s for s in sizes if s < mf]), mf, args.carrier, small[:8] or 'none'))
    hit = mh.get('px') or (mh.get('value') if isinstance(mh.get('value'), (int, float)) else None)
    if hit is None:
        notes.append('C2 min hit area: carrier gives no value (not verified), skipped')
    else:
        low = []
        for sel, body in re.findall(r'([^{}]+)\{([^{}]*)\}', css):
            if re.search(r'(^|[\s,.>#])(button|btn|tap|hit|cta)\b', sel, re.I):
                low += [(sel.strip()[:30], float(v)) for v in re.findall(r'(?<![-\w])(?:min-)?height\s*:\s*([\d.]+)px', body) if float(v) < hit]
        (warns if low else notes).append('C2 %d control rules with a declared height below %s px: %s' % (len(low), hit, low[:4] or 'none'))
    if vw:
        meta = re.search(r'<meta[^>]+name=["\']viewport["\'][^>]*>', html, re.I)
        if not meta or 'device-width' not in meta.group(0):
            (fails if (vw if isinstance(vw, int) else vw[0]) < 600 else warns).append('C3 carrier width %s needs <meta name=viewport content="width=device-width, ...">' % (vw,))
        else:
            notes.append('C3 ok: viewport meta present (carrier width %s)' % (vw,))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('html')
    ap.add_argument('--gear', default='mixed', choices=list(FLOOR), help='budget preset id: clear | mixed | show (kept as --gear for compatibility)')
    ap.add_argument('--carrier', help='carrier id from design-pipeline/library/carriers.json')
    args = ap.parse_args()
    src = open(args.html, encoding='utf-8').read()
    p = P()
    p.feed(src)
    ext_css = linked_css(src, os.path.dirname(os.path.abspath(args.html)))
    css = '\n'.join(p.styles) + '\n' + ext_css
    fam_min, chips_max, need_reveal = FLOOR[args.gear]
    fails, warns, notes = [], [], []

    # F1 structure colour: a chromatic token used often
    tokens = {}
    for name, val in re.findall(r'(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,6})\b', css):
        h, l, s = hex_to_hls(val)
        if s >= 0.25 and 0.12 <= l <= 0.85:
            tokens[name] = (val, round(s, 2))
    used = {n: len(re.findall(r'var\(%s\)' % re.escape(n), src + ext_css)) for n in tokens}
    strong = {n: c for n, c in used.items() if c >= 12}
    if not strong:
        fails.append('F1 no chromatic token is used 12 times or more. chromatic tokens: %s' % (used or 'none'))
    else:
        notes.append('F1 ok: ' + ', '.join('%s x%d' % kv for kv in strong.items()))

    # F2 hero visual
    if not p.hero_visual and p.hero_marked and 'preserve-3d' in css:
        notes.append('F2 ok: hero visual is CSS 3D')
    elif not p.hero_visual:
        fails.append('F2 no [data-hero-visual] element with svg/img/canvas/picture (or CSS 3D) on the first screen')
    else:
        notes.append('F2 ok: hero visual present')

    # F3 layout families
    fams = [c['layout'] for c in p.chapters]
    missing = [c['id'] for c in p.chapters if not c['layout']]
    if missing:
        fails.append('F3 chapters without data-layout: %s' % ', '.join(missing))
    kinds = {f for f in fams if f}
    if len(kinds) < fam_min:
        fails.append('F3 %d layout families, below the reference value of preset %s (%d): %s' % (len(kinds), args.gear, fam_min, sorted(kinds)))
    same = [(a['id'], b['id']) for a, b in zip(p.chapters, p.chapters[1:]) if a['layout'] and a['layout'] == b['layout']]
    if same:
        warns.append('F3 adjacent chapters share one layout: %s' % same[:6])
    if len(kinds) >= fam_min and not missing:
        notes.append('F3 ok: %d families %s' % (len(kinds), sorted(kinds)))

    # F5 chip density
    for c in p.chapters:
        if c['text'] >= 400:
            d = c['tags'] / (c['text'] / 1000)
            if d > chips_max:
                fails.append('F5 chapter %s has %.1f chips per 1000 chars (max %d)' % (c['id'], d, chips_max))
    tot_t = sum(c['tags'] for c in p.chapters)
    tot_c = sum(c['text'] for c in p.chapters)
    tot_cell = sum(c['cell_tags'] for c in p.chapters)
    notes.append('F5 body chips %d (%.1f per 1000 chars), table-row chips %d (one per row, not counted in density)' % (tot_t, tot_t / max(tot_c / 1000, 1), tot_cell))

    # F4 / F6 (advisory)
    if p.pattern_count and not strong:
        warns.append('F4 charts use hatch patterns and the page has no chromatic ramp')
    if need_reveal and (p.attr_counts['data-reveal'] == 0 or p.attr_counts['data-counter'] == 0):
        fails.append('F6 preset %s expects data-reveal and data-counter hooks (found %s)' % (args.gear, p.attr_counts))
    else:
        notes.append('F6 hooks: %s' % p.attr_counts)

    if args.carrier:
        carrier_checks(args, src, css, fails, warns, notes)
    for n in notes:
        print('ok   ', n)
    for w in warns:
        print('WARN ', w)
    for f in fails:
        print('FAIL ', f)
    print('result: %d FAIL, %d WARN (budget preset %s). A pass does not prove a good design.' % (len(fails), len(warns), args.gear))
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
