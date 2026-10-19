#!/usr/bin/env python3
"""生成 library/cases.md 索引。用法：python3 -I toolbox/cases-index.py [--merge library/cases-batch2.json]
--merge 先把另一份 {"cases":[...]} 合并进 cases.json（按 id 去重，后来者不覆盖），再写索引。"""
import json, sys, os, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, 'library')
CASES = os.path.join(LIB, 'cases.json')
REQ = ['id','slot','purpose','name','why','seen_at','atmosphere_fit','carriers','adapt','reduce_motion','risks','avoids','added','used_in']

def load(p):
    with open(p, encoding='utf-8') as f: return json.load(f)

HC = ('亲核打开','本库已做出','二手摘要')

def check(cases):
    """返回 (缺字段与非法项, 重复 id)。"""
    bad = [(c.get('id'), k) for c in cases for k in REQ if k not in c or c[k] in ('', None)]
    for c in cases:
        for x in c.get('seen_at', []):
            if x.get('how_checked') not in HC: bad.append((c.get('id'), 'how_checked:' + str(x.get('how_checked'))))
        if 'verified' in c and not isinstance(c['verified'], bool): bad.append((c.get('id'), 'verified 须为布尔值'))
    ids = [c.get('id') for c in cases]
    return bad, sorted({i for i in ids if ids.count(i) > 1}, key=str)

d = load(CASES)
cases = d['cases']
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
    tmp = CASES + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f: json.dump(d, f, ensure_ascii=False, indent=1); f.write('\n')
    os.replace(tmp, CASES)
    print(f'合并 {len(merged) - n0} 条，跳过已有 {skipped} 条，共 {len(merged)} 条')

bad, dup = check(cases)
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
with open(os.path.join(LIB, 'cases.md'), 'w', encoding='utf-8') as f: f.write('\n'.join(lines))
print(f'cases.md 写好：{len(cases)} 条，{len(by)} 槽。缺字段 {len(bad)}，重复 id {dup}')
if bad: print(bad[:10])
sys.exit(1 if bad or dup else 0)
