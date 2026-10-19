#!/usr/bin/env python3
"""生成 library/cases.md 索引。用法：python3 -I toolbox/cases-index.py [--merge library/cases-batch2.json | --thin]
--merge 先把另一份 {"cases":[...]} 合并进 cases.json（按 id 去重，后来者不覆盖），再写索引。"""
import json, sys, os, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, 'library')
CASES = os.path.join(LIB, 'cases.json')
REQ = ['id','slot','purpose','name','why','seen_at','atmosphere_fit','carriers','adapt','reduce_motion','risks','avoids','added','used_in']

def load(p):
    with open(p, encoding='utf-8') as f: return json.load(f)

HC = ('亲核打开','本库已做出','二手摘要')

LISTS = ('atmosphere_fit','carriers','adapt','avoids','used_in')
STRS = ('id','slot','purpose','name','why','added','reduce_motion','risks')

def check(cases):
    """返回 (缺字段与非法项, 重复 id)。类型也校验：写索引要用，类型错会让渲染崩溃。"""
    bad = []
    for c in cases:
        if not isinstance(c, dict): bad.append((None, '条目须为对象')); continue
        i = c.get('id')
        for k in REQ:
            if k not in c or c[k] in ('', None): bad.append((i, k))
        for k in LISTS:
            if k in c and not (isinstance(c[k], list) and all(isinstance(x, str) for x in c[k])): bad.append((i, k + ' 须为字符串列表'))
        for k in STRS:
            if k in c and not isinstance(c[k], str): bad.append((i, k + ' 须为字符串'))
        sa = c.get('seen_at')
        if sa is not None and not (isinstance(sa, list) and all(isinstance(x, dict) for x in sa)): bad.append((i, 'seen_at 须为对象列表')); continue
        for x in sa or []:
            if x.get('how_checked') not in HC: bad.append((i, 'how_checked:' + str(x.get('how_checked'))))
            if 'verified' in x and not isinstance(x['verified'], bool): bad.append((i, 'seen_at.verified 须为布尔值，日期写在 verified_at'))
        if 'verified' in c: bad.append((i, 'verified 写在 seen_at 每项里，不写在条目上'))
    ids = [c.get('id') for c in cases if isinstance(c, dict)]
    return bad, sorted({i for i in ids if ids.count(i) > 1}, key=str)

def render(cases):
    """在内存里生成 cases.md 文本。非法数据先由 check 拦下，这里不再处理。"""
    by = {}
    for c in cases: by.setdefault(c['slot'], []).append(c)
    hc = lambda c: '、'.join(sorted({s.get('how_checked', '二手摘要') for s in c['seen_at']}))
    lines = ['# 案例索引', '', f'由 `toolbox/cases-index.py` 生成，不手改。共 {len(cases)} 条，{len(by)} 个槽。发牌：`node toolbox/deal.mjs --slot <槽> --purpose "<目的>" --carrier <id>`。字段与补库规则见 `stages/3-components.md` 第 6、7 节。', '']
    lines.append('| 槽 | 条数 | 本库已做出 | 亲核打开 | 二手摘要 |'); lines.append('|---|---|---|---|---|')
    for s in sorted(by):
        cs = by[s]; cnt = lambda k: sum(1 for c in cs if any(x.get('how_checked') == k for x in c['seen_at']))
        lines.append(f"| {s} | {len(cs)} | {cnt('本库已做出')} | {cnt('亲核打开')} | {cnt('二手摘要')} |")
    lines.append('')
    for s in sorted(by):
        lines += [f'## {s}', '', '| id | 名字 | 目的 | 为什么好 | 适合氛围 | 载体 | 核验 | 用过 |', '|---|---|---|---|---|---|---|---|']
        for c in sorted(by[s], key=lambda c: c['id']):
            lines.append(f"| `{c['id']}` | {c['name']} | {c['purpose']} | {c['why']} | {'、'.join(c['atmosphere_fit'])} | {','.join(c['carriers'])} | {hc(c)} | {','.join(c['used_in']) or '—'} |")
        lines.append('')
    return '\n'.join(lines), len(by)

def write_both(d, md):
    """两份文件先写临时名，都成功后再替换，避免 cases.json 已改而 cases.md 没写。"""
    t1, t2 = CASES + '.tmp', os.path.join(LIB, 'cases.md.tmp')
    try:
        with open(t1, 'w', encoding='utf-8') as f: json.dump(d, f, ensure_ascii=False, indent=1); f.write('\n')
        with open(t2, 'w', encoding='utf-8') as f: f.write(md)
    except Exception:
        for t in (t1, t2):
            if os.path.exists(t): os.remove(t)
        raise
    MD = os.path.join(LIB, 'cases.md')
    old_json = open(CASES, 'rb').read()
    os.replace(t1, CASES)
    try:
        os.replace(t2, MD)
    except Exception as e:
        # 第二次替换失败：把 cases.json 退回旧内容，保持两份一致。退回也失败就明说，不报成功
        try:
            with open(t1, 'wb') as f: f.write(old_json)
            os.replace(t1, CASES)
            msg = 'cases.json 已退回旧内容，两份文件仍一致。'
        except Exception as e2:
            msg = f'退回失败（{e2!r}）。cases.json 已是新内容，cases.md 是旧的：修好权限后运行 python3 -I toolbox/cases-index.py 重建 cases.md。'
        if os.path.exists(t2): os.remove(t2)
        print(f'写 cases.md 失败（{e!r}）。{msg}')
        sys.exit(1)

d = load(CASES)
cases = d['cases']
if '--thin' in sys.argv:
    # 库薄体检：条数少于 THIN_N，或可信条数（亲核打开、本库已做出至少一条来源）少于 THIN_TRUST。起点值，不是通过线
    THIN_N, THIN_TRUST = 6, 3
    # 先按合法槽建空表，零条案例的槽也要列出并判薄
    by = {s: [] for s in d.get('_meta', {}).get('slots', [])}
    for c in cases: by.setdefault(c.get('slot'), []).append(c)
    ok = lambda c: any(x.get('how_checked') in ('亲核打开', '本库已做出') for x in c.get('seen_at', []))
    print(f'库薄体检（条数 <{THIN_N} 或 可信条数 <{THIN_TRUST} 判薄；可信 = 亲核打开或本库已做出）')
    print('| 槽 | 条数 | 可信 | 判定 |'); print('|---|---|---|---|')
    thin = []
    for s in sorted(by, key=str):
        n, t = len(by[s]), sum(1 for c in by[s] if ok(c))
        flag = n < THIN_N or t < THIN_TRUST
        if flag: thin.append(s)
        print(f'| {s} | {n} | {t} | {"薄，建议补调研" if flag else "够"} |')
    print(f'薄槽 {len(thin)} 个：{"、".join(map(str, thin)) or "无"}。补调研步骤见 stages/3-components.md 第 5.5 节。')
    sys.exit(0)
if '--merge' in sys.argv:
    other = load(os.path.join(ROOT, sys.argv[sys.argv.index('--merge') + 1]))
    merged, have, skipped = list(cases), {c.get('id') for c in cases}, 0
    n0 = len(cases)
    for c in other['cases']:
        if c.get('id') in have: skipped += 1; continue
        have.add(c.get('id')); merged.append(c)
    # 同批重复也算重复：按原始合并结果再校验一遍，重复入库前先拦下
    batch_ids = [c.get('id') for c in other['cases']]
    batch_dup = sorted({i for i in batch_ids if batch_ids.count(i) > 1}, key=str)
    bad, dup = check(merged)
    dup = sorted(set(dup) | set(batch_dup), key=str)
    if bad or dup:
        print(f'合并失败，未写任何文件。缺字段或非法项 {len(bad)}：{bad[:10]}，重复 id {dup}')
        sys.exit(1)
    d['cases'] = cases = merged
    d['_meta']['case_count'] = len(cases)
    d['_meta']['slots'] = sorted({c['slot'] for c in cases})
    d['_meta']['checked'] = datetime.date.today().isoformat()
    md, nslots = render(cases)
    write_both(d, md)
    print(f'合并 {len(merged) - n0} 条，跳过已有 {skipped} 条，共 {len(merged)} 条')
    print(f'cases.md 写好：{len(cases)} 条，{nslots} 槽。缺字段 0，重复 id []')
    sys.exit(0)

bad, dup = check(cases)
if bad or dup:
    print(f'未写 cases.md。缺字段或非法项 {len(bad)}：{bad[:10]}，重复 id {dup}')
    sys.exit(1)
md, nslots = render(cases)
tmp = os.path.join(LIB, 'cases.md.tmp')
with open(tmp, 'w', encoding='utf-8') as f: f.write(md)
os.replace(tmp, os.path.join(LIB, 'cases.md'))
print(f'cases.md 写好：{len(cases)} 条，{nslots} 槽。缺字段 0，重复 id []')
