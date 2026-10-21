#!/usr/bin/env node
// lib.mjs：查库，不整读。library/*.json 最大的有 95 KB，整读会把上下文填满。
// 本脚本按库打印简表（每条一行），或打印一条的全部字段。Node 24，无依赖。
//
// 用法
//   node toolbox/lib.mjs                          列出可查的库、条数、整文件大小
//   node toolbox/lib.mjs <库>                     简表
//   node toolbox/lib.mjs <库> <id>                一条的全部字段
//   node toolbox/lib.mjs <库> --where k=v[,k=v]   过滤：字段 k 含 v（字符串包含；数组任一元素包含；大小写不分）
//   node toolbox/lib.mjs <库> --fields a,b,c      简表只打印这些字段
//   node toolbox/lib.mjs <库> --max 120           简表每个字段最多打印的字符数（默认 70）
// 库名：themes anchors forms expressions palettes references carriers cases directions motions
//
// 例
//   node toolbox/lib.mjs themes                              阶段 2 主题打分前看 25 个主题
//   node toolbox/lib.mjs themes T03                          看一个主题的案例与签名交互
//   node toolbox/lib.mjs anchors --where page_type=team      评审前选同页型锚点
//   node toolbox/lib.mjs expressions --where layer=stage     按幕选表现形式
//   node toolbox/lib.mjs carriers wechat-mini                阶段 1 抄载体数值

import { readFileSync, existsSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const LIB = join(ROOT, 'library');

// 库名 -> 文件、取条目的方式、简表字段
const LIBS = {
  themes: { file: 'themes.json', key: 'themes', brief: ['id', 'name_zh', 'one_liner', 'feasibility_here', 'content_signals'] },
  anchors: { file: 'anchors.json', key: ['high', 'low'], brief: ['id', 'name', 'tier', 'page_type', 'award', 'opened', 'impact_methods', 'stop_power'] },
  forms: { file: 'page-forms.json', key: 'forms', brief: ['id', 'status', 'name_zh', 'one_liner', 'unit', 'chapter_range', 'fit'] },
  expressions: { file: 'expressions.json', key: 'cards', brief: ['id', 'name_zh', 'layer', 'expresses', 'cost', 'example'] },
  palettes: { file: 'palettes.json', key: 'palettes', brief: ['id', 'name_zh', 'fits', 'taboo'] },
  references: { file: 'references.json', key: 'references', brief: ['id', 'name', 'year', 'forms', 'what', 'url'] },
  carriers: { file: 'carriers.json', key: 'auto', brief: ['id', 'name', 'name_zh', 'viewport', 'min_font', 'hit_target'] },
  cases: { file: 'cases.json', key: 'cases', brief: ['id', 'slot', 'purpose', 'name'] },
  directions: { file: 'directions.json', key: 'directions', brief: ['id', 'name', 'mode', 'form'] },
  motions: { file: 'motions.json', key: 'motions', brief: ['id', 'name', 'name_zh', 'what'] },
};

const argv = process.argv.slice(2);
const opt = {};
const pos = [];
for (let i = 0; i < argv.length; i++) {
  if (argv[i].startsWith('--')) {
    const k = argv[i].slice(2);
    opt[k] = argv[i + 1] !== undefined && !argv[i + 1].startsWith('--') ? argv[++i] : true;
  } else pos.push(argv[i]);
}
const out = (s = '') => console.log(s);

function entries(spec, data) {
  if (spec.key === 'auto') {
    // 找第一个"对象数组"或"id -> 对象"的键
    for (const [k, v] of Object.entries(data)) {
      if (k === '_meta') continue;
      if (Array.isArray(v) && v.length && typeof v[0] === 'object') return v;
      if (v && typeof v === 'object' && Object.values(v).every((x) => x && typeof x === 'object')) {
        return Object.entries(v).map(([id, o]) => ({ id, ...o }));
      }
    }
    return [];
  }
  const keys = Array.isArray(spec.key) ? spec.key : [spec.key];
  return keys.flatMap((k) => (data[k] || []).map((e) => (keys.length > 1 ? { group: k, ...e } : e)));
}

const str = (v) => (Array.isArray(v) ? v.map((x) => (typeof x === 'object' ? JSON.stringify(x) : String(x))).join('、') : v && typeof v === 'object' ? JSON.stringify(v) : v === undefined || v === null ? '' : String(v));
const cut = (s, n) => (s.length > n ? s.slice(0, n - 1) + '…' : s);

if (!pos.length) {
  out('可查的库（node toolbox/lib.mjs <库> [id] [--where k=v] [--fields a,b]）：');
  for (const [name, spec] of Object.entries(LIBS)) {
    const p = join(LIB, spec.file);
    if (!existsSync(p)) { out(`  ${name.padEnd(12)} 缺文件 ${spec.file}`); continue; }
    const n = entries(spec, JSON.parse(readFileSync(p, 'utf8'))).length;
    out(`  ${name.padEnd(12)} ${String(n).padStart(4)} 条  ${String(Math.round(statSync(p).size / 1024)).padStart(4)} KB  ${spec.file}`);
  }
  process.exit(0);
}

const name = pos[0];
const spec = LIBS[name];
if (!spec) { console.error(`错误：未知库 ${name}。可用：${Object.keys(LIBS).join(' ')}`); process.exit(1); }
const path = join(LIB, spec.file);
if (!existsSync(path)) { console.error(`错误：缺文件 ${path}`); process.exit(1); }
const data = JSON.parse(readFileSync(path, 'utf8'));
let list = entries(spec, data);
const fileKB = (statSync(path).size / 1024).toFixed(0);

if (pos[1]) {
  const id = pos[1];
  const hit = list.find((e) => String(e.id) === id) || list.find((e) => String(e.id).toLowerCase() === id.toLowerCase() || String(e.name || e.name_zh || '').toLowerCase() === id.toLowerCase());
  if (!hit) { console.error(`错误：${name} 里没有 id ${id}。先 node toolbox/lib.mjs ${name} 看简表。`); process.exit(1); }
  const fields = opt.fields && opt.fields !== true ? String(opt.fields).split(',').map((s) => s.trim()) : null;
  const shown = fields ? Object.fromEntries(Object.entries(hit).filter(([k]) => fields.includes(k))) : hit;
  out(JSON.stringify(shown, null, 2));
  process.exit(0);
}

if (opt.where && opt.where !== true) {
  const conds = String(opt.where).split(',').map((s) => s.trim()).filter(Boolean).map((s) => { const i = s.indexOf('='); return i < 0 ? [s, ''] : [s.slice(0, i).trim(), s.slice(i + 1).trim().toLowerCase()]; });
  list = list.filter((e) => conds.every(([k, v]) => str(e[k]).toLowerCase().includes(v)));
}

const fields = opt.fields && opt.fields !== true ? String(opt.fields).split(',').map((s) => s.trim()) : spec.brief;
const max = Number(opt.max) || 70;
if (!list.length) { out(`${name}：没有匹配的条目。`); process.exit(0); }
for (const e of list) {
  const parts = fields.filter((f) => e[f] !== undefined && e[f] !== null && str(e[f]) !== '').map((f) => (f === 'id' ? String(e.id) : `${f}: ${cut(str(e[f]), max)}`));
  if (e.group && !fields.includes('group')) parts.splice(1, 0, `group: ${e.group}`);
  out(parts.join(' | '));
}
const printed = list.length;
out(`— ${name} 共 ${printed} 条${opt.where ? '（已过滤）' : ''}，整文件 ${fileKB} KB。看一条全文：node toolbox/lib.mjs ${name} <id>`);
