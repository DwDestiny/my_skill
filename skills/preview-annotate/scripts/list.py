#!/usr/bin/env python3
"""按页面分组打印批注。用法：list.py <annotations.json> [--since ISO时间]

Input: preview.sh 工作目录里的 annotations.json
Output: 按页面分组的批注文本，打印到标准输出
Pos: 智能体读取批注的入口
"""
import json
import sys
from collections import defaultdict

path = sys.argv[1]
since = sys.argv[sys.argv.index('--since') + 1] if '--since' in sys.argv else ''
items = [a for a in json.load(open(path, encoding='utf-8')) if a.get('ts', '') > since]
groups = defaultdict(list)
for a in items:
    groups[a['route'].split('?')[0]].append(a)
print(f'共 {len(items)} 条批注，{len(groups)} 个页面')
for route, rows in groups.items():
    print(f'\n## {route}')
    for a in rows:
        print(f"- [{a['id']}] {a['comment']}")
        print(f"    路由 {a['route']} · 视口 {a['viewport']} · 组件 {a['element']} {a['rect']['w']}×{a['rect']['h']}")
        if a.get('text'):
            print(f"    文字：{a['text'][:80]}")
        print(f"    选择器：{a['selector']}")
