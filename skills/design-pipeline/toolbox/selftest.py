#!/usr/bin/env python3
"""selftest.py 工具自测：历史 bug 的回归检查（12 项）。Python 3.12 标准库。

用途：把 design-pipeline 复制到临时目录，对 shots、defaults-check、cases-index、deal、flash-check 各跑一个坏输入。
用法：python3 -I toolbox/selftest.py（需要 node）。每项输出 PASS 或 FAIL，任一失败退出码 1，不碰真实库与真实 history。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(cmd, cwd, env=None, timeout=60):
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)


def rd(p):
    with open(p, 'rb') as f:
        return f.read()


def t_shots(P, tmp):
    bindir = os.path.join(tmp, 'bin')
    os.makedirs(bindir)
    fake = os.path.join(bindir, 'agent-browser')
    with open(fake, 'w') as f:
        f.write('#!/bin/sh\ncase "$1" in\n  screenshot) exit 1;;\n  eval) echo 1800;;\n  *) echo ok;;\nesac\n')
    os.chmod(fake, 0o755)
    out = os.path.join(tmp, 'shots-out')
    os.makedirs(out)
    with open(os.path.join(out, 'd-fold.png'), 'wb') as f:
        f.write(b'old')
    env = dict(os.environ, PATH=bindir + os.pathsep + os.environ['PATH'])
    run([sys.executable, '-I', os.path.join(P, 'toolbox', 'shots.py'), '--url', 'http://127.0.0.1:1/x', '--out', out], tmp, env)
    md = rd(os.path.join(out, 'SHOTS.md')).decode('utf-8') if os.path.isfile(os.path.join(out, 'SHOTS.md')) else ''
    table = '\n'.join(ln for ln in md.splitlines() if ln.startswith('|'))
    return 'd-fold（失败）' in table and 'd-fold.png' not in table.replace('d-fold（失败）', ''), 'SHOTS.md 表格中 d-fold 未标失败'


def t_defaults(P, tmp):
    r = run([sys.executable, '-I', os.path.join(P, 'toolbox', 'defaults-check.py'), os.path.join(tmp, 'nope.html')], tmp)
    return r.returncode != 0, '不存在的 HTML 退出码为 %d' % r.returncode


def t_cases(P, tmp):
    cj = os.path.join(P, 'library', 'cases.json')
    before = rd(cj)
    bad = {'cases': [{'id': 'dup-x', 'slot': 'hero'}, {'id': 'dup-x', 'slot': 'hero'}]}
    with open(os.path.join(P, 'library', 'batch.json'), 'w', encoding='utf-8') as f:
        json.dump(bad, f)
    r = run([sys.executable, '-I', os.path.join(P, 'toolbox', 'cases-index.py'), '--merge', 'library/batch.json'], tmp)
    return r.returncode == 1 and rd(cj) == before, '退出码 %d，cases.json %s' % (r.returncode, '未变' if rd(cj) == before else '被改')


def t_deal(P, tmp):
    deal = os.path.join(P, 'toolbox', 'deal.mjs')
    lst = run(['node', deal, '--list'], tmp).stdout
    ls = lst.splitlines()
    cid = ls[next(k for k, ln in enumerate(ls) if ln.startswith('可用方向卡')) + 1].split()[0]
    hp = os.path.join(P, 'history', 'history.json')
    os.makedirs(os.path.dirname(hp), exist_ok=True)
    with open(hp, 'wb') as f:
        f.write(b'{"entries": [{"project": "a"')
    before = rd(hp)
    r = run(['node', deal, '--add-history', cid, '--project', 't'], tmp)
    return r.returncode != 0 and rd(hp) == before and '无法解析' in r.stderr, '退出码 %d，history %s，id=%s' % (r.returncode, '未变' if rd(hp) == before else '被改', cid)


def t_flash(P, tmp):
    h = os.path.join(tmp, 'loops.html')
    with open(h, 'w', encoding='utf-8') as f:
        f.write('<!doctype html><style>.a{animation:x 1s infinite}.b{animation:y 2s infinite}</style><body>暂停</body>')
    r = run([sys.executable, '-I', os.path.join(P, 'toolbox', 'flash-check.py'), h], tmp)
    line = next((ln for ln in r.stdout.splitlines() if '无限循环动效数' in ln), '')
    return 'infinite/repeat:-1 共 2（CSS 2' in line, line[:80]


def t_shots_keep(P, tmp):
    bindir = os.path.join(tmp, 'bin')
    os.makedirs(bindir)
    fake = os.path.join(bindir, 'agent-browser')
    with open(fake, 'w') as f:
        f.write('#!/bin/sh\ncase "$1" in\n  screenshot) exit 1;;\n  eval) echo 1800;;\n  *) echo ok;;\nesac\n')
    os.chmod(fake, 0o755)
    out = os.path.join(tmp, 'shots-out')
    os.makedirs(out)
    with open(os.path.join(out, 'd-fold.png'), 'wb') as f:
        f.write(b'old')
    env = dict(os.environ, PATH=bindir + os.pathsep + os.environ['PATH'])
    run([sys.executable, '-I', os.path.join(P, 'toolbox', 'shots.py'), '--url', 'http://127.0.0.1:1/x', '--out', out], tmp, env)
    kept = os.path.isfile(os.path.join(out, 'd-fold.png')) and rd(os.path.join(out, 'd-fold.png')) == b'old'
    left = [n for n in os.listdir(out) if n.endswith('.new.png')]
    return kept and not left, '旧图%s，残留临时图 %d 个' % ('保留' if kept else '被删', len(left))


def t_cases_types(P, tmp):
    cj, md = os.path.join(P, 'library', 'cases.json'), os.path.join(P, 'library', 'cases.md')
    before = (rd(cj), rd(md))
    with open(cj, encoding='utf-8') as f:
        c = dict(json.load(f)['cases'][0])
    c['id'] = 'type-bad-x'
    c['atmosphere_fit'] = 42
    c['seen_at'] = [{'site': 's', 'url': 'u', 'year': 2026, 'how_checked': '亲核打开', 'verified': '2026-10-19'}]
    with open(os.path.join(P, 'library', 'batch.json'), 'w', encoding='utf-8') as f:
        json.dump({'cases': [c]}, f, ensure_ascii=False)
    r = run([sys.executable, '-I', os.path.join(P, 'toolbox', 'cases-index.py'), '--merge', 'library/batch.json'], tmp)
    same = (rd(cj), rd(md)) == before
    return r.returncode == 1 and same and 'Traceback' not in r.stderr, '退出码 %d，cases.json 与 cases.md %s，stderr %d 字符' % (r.returncode, '未变' if same else '被改', len(r.stderr))


def _site(tmp, css_exists):
    d = os.path.join(tmp, 'site')
    os.makedirs(d)
    with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8') as f:
        f.write('<!doctype html><link rel="stylesheet" href="/style.css"><link rel="stylesheet" href="https://cdn.example.com/x.css"><body>x</body>')
    if css_exists:
        with open(os.path.join(d, 'style.css'), 'w', encoding='utf-8') as f:
            f.write(':root{--a:#336699}.x{animation:k 1s infinite}')
    return os.path.join(d, 'index.html')


def t_root_missing(P, tmp):
    h = _site(tmp, False)
    out = ''
    for name in ('defaults-check.py', 'flash-check.py'):
        r = run([sys.executable, '-I', os.path.join(P, 'toolbox', name), h], tmp)
        out += r.stdout
        if '未覆盖项' not in r.stdout or '/style.css' not in r.stdout or 'cdn.example.com' not in r.stdout:
            return False, '%s 没有列出缺失的 /style.css 或外部链接' % name
    return True, '两个脚本都列出 /style.css 与外部链接'


def t_root_found(P, tmp):
    h = _site(tmp, True)
    r = run([sys.executable, '-I', os.path.join(P, 'toolbox', 'flash-check.py'), h], tmp)
    line = next((ln for ln in r.stdout.splitlines() if '无限循环动效数' in ln), '')
    local_ok = '本地读不到' not in r.stdout and 'CSS 1' in line
    return local_ok, line[:80]


def t_compare_root(P, tmp):
    d = os.path.join(tmp, 'site')
    os.makedirs(os.path.join(d, 'a'))
    with open(os.path.join(d, 'a', 'index.html'), 'w', encoding='utf-8') as f:
        f.write('<!doctype html><link rel="stylesheet" href="/style.css"><body>x</body>')
    with open(os.path.join(d, 'style.css'), 'w', encoding='utf-8') as f:
        f.write(':root{--a:#336699;--b:#cc5533}@keyframes k{}body{font-family:"Foo"}')
    h, dc = os.path.join(d, 'a', 'index.html'), os.path.join(P, 'toolbox', 'defaults-check.py')
    ok1 = run([sys.executable, '-I', dc, h, '--root', d, '--compare', h], tmp).stdout
    ok2 = run([sys.executable, '-I', dc, h, '--compare', h], tmp).stdout
    a = '| 平均命中率 | 0% | PASS' not in ok1 and '读不到' not in ok1.split('同质化比较')[-1]
    b = '不完整' in ok2 and '| 平均命中率 | 0% | PASS' not in ok2
    return a and b, '带 --root 时比较页读到 CSS：%s，不带时标不完整：%s' % (a, b)


def t_cases_rollback(P, tmp):
    L = os.path.join(P, 'library')
    cj = os.path.join(L, 'cases.json')
    with open(cj, encoding='utf-8') as f:
        c = dict(json.load(f)['cases'][0])
    c['id'] = 'new-rollback-x'
    with open(os.path.join(L, 'batch.json'), 'w', encoding='utf-8') as f:
        json.dump({'cases': [c]}, f, ensure_ascii=False)
    before = rd(cj)
    os.remove(os.path.join(L, 'cases.md'))
    os.mkdir(os.path.join(L, 'cases.md'))  # 让第二次替换失败
    r = run([sys.executable, '-I', os.path.join(P, 'toolbox', 'cases-index.py'), '--merge', 'library/batch.json'], tmp)
    left = [n for n in os.listdir(L) if n.endswith('.tmp')]
    return r.returncode == 1 and rd(cj) == before and not left and '失败' in r.stdout, '退出码 %d，cases.json %s，残留临时文件 %d 个' % (r.returncode, '已退回' if rd(cj) == before else '停在新内容', len(left))


def t_compare_both_sides(P, tmp):
    d = os.path.join(tmp, 'site')
    os.makedirs(d)
    full = os.path.join(d, 'full.html')
    miss = os.path.join(d, 'miss.html')
    rem = os.path.join(d, 'remote.html')
    with open(os.path.join(d, 'style.css'), 'w', encoding='utf-8') as f:
        f.write(':root{--a:#336699;--b:#cc5533}@keyframes k{}body{font-family:"Foo"}')
    for path, link in ((full, '/style.css'), (miss, '/missing.css'), (rem, 'https://cdn.example.com/theme.css')):
        with open(path, 'w', encoding='utf-8') as f:
            f.write('<!doctype html><link rel="stylesheet" href="%s"><body>x</body>' % link)
    dc = os.path.join(P, 'toolbox', 'defaults-check.py')
    a = run([sys.executable, '-I', dc, miss, '--root', d, '--compare', full], tmp).stdout
    b = run([sys.executable, '-I', dc, full, '--root', d, '--compare', rem], tmp).stdout
    oka = '| PASS' not in a.split('平均命中率')[-1].split('\n')[0] and '不完整' in a
    okb = '| PASS' not in b.split('平均命中率')[-1].split('\n')[0] and '不完整' in b
    return oka and okb, '主页面缺资源：%s，比较页远程样式表：%s' % ('不判 PASS' if oka else '仍判 PASS', '不判 PASS' if okb else '仍判 PASS')


def main():
    tests = [('shots 失败截图不被旧 PNG 冒充', t_shots), ('defaults-check 读不到主 HTML', t_defaults),
             ('cases-index 同 id 缺字段不写库', t_cases), ('deal 损坏 history 不覆盖', t_deal),
             ('flash-check 内联循环不重复计数', t_flash),
             ('shots 失败时保留上次旧图', t_shots_keep), ('cases-index 类型错误不崩溃不写库', t_cases_types),
             ('根相对 CSS 缺失与外链列入未覆盖项', t_root_missing), ('根相对 CSS 存在时被读入', t_root_found),
             ('--compare 沿用 root，读不全时不判 PASS', t_compare_root), ('cases-index 第二次替换失败时退回', t_cases_rollback),
             ('--compare 任一侧资源读不全都不判 PASS', t_compare_both_sides)]
    fails = 0
    for name, fn in tests:
        with tempfile.TemporaryDirectory() as tmp:
            P = os.path.join(tmp, 'dp')
            shutil.copytree(SRC, P, ignore=shutil.ignore_patterns('__pycache__'))
            try:
                ok, info = fn(P, tmp)
            except Exception as e:
                ok, info = False, '异常 %r' % e
        fails += not ok
        print('%s  %s  (%s)' % ('PASS' if ok else 'FAIL', name, info))
    print('%d 项，%d 失败' % (len(tests), fails))
    sys.exit(1 if fails else 0)


main()
