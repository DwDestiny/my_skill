#!/usr/bin/env node
// deal.mjs: deal direction cards for design-pipeline step S3 (art direction).
// Node 24, no dependencies.
//
// Usage
//   node toolbox/deal.mjs --carrier web-desktop --gear mixed --topic 讲解 --audience 业务人员 [--mode read] [--options 3] [--seed 7]
//   node toolbox/deal.mjs --commit <direction-id> --project <name> --carrier <c> --gear <g>
//                         [--topic t] [--palette id] [--form id,id] [--outcome 好|一般|差] [--note text]
//   node toolbox/deal.mjs --add-history <direction-id> --project <name> [--carrier c --gear g --topic t --note text]
//   node toolbox/deal.mjs --slot <slot> --purpose "<goal>" --carrier <c> [--options 3] [--seed 7]
//                         deal component pattern cards (S4) from library/component-patterns.json
//   node toolbox/deal.mjs --list
//
// Flags
//   --carrier  carriers.json 的 9 个 id（wechat-mini alipay-mini ios android harmony mobile-web desktop-web macos windows），
//              也接受卡片的 medium 写法（web-desktop web-mobile mp-weixin app-ios app-android mac win）。硬过滤 card.medium。
//   --gear     clear | mixed | show (hard filter: gear must be >= card.gear_floor)
//   --mode     persuade | operate | read | experience (optional hard filter)
//   --topic, --audience  soft weights only (x3 per match, no hard filter)
//   --options  number of cards to deal (default 3)
//   --seed     integer, makes a deal reproducible
//   --seed-history  id[,id...]  treat these direction ids as recently used (merged with history).
//                   Use it when the last project did not run this plugin and history is empty.
//   --add-history   id  write one manual record to history/history.json (no deal). Needs --project.
//                   The record carries source:"manual". --carrier and --gear are optional.
//
// Rules (from the archived PLAN.md sections 6.2 and 6.3, 作者的私有归档（不在本仓库）)
//   1. Skip the direction ids used in the last 5 history entries. If the pool is too small, use the full pool.
//   2. Weight = 1 / (1 + use_count). Outcome "差" for the same carrier and topic halves the weight.
//   3. Any two dealt cards differ on at least 3 of 5 axes. If impossible, relax to 2, then 1, and print a note.
//
// Sources
//   library/directions.json         own cards (source "design-pipeline")
//   ../design-taste-frontend/library/directions.json   tasteskill cards
//   History: history/history.json (not in Git).
//
// Attribution: the card field structure and the deal-and-history idea come from tasteskill
// (Leonxlnx/taste-skill, MIT). Cards without medium/mode/axes get defaults, and inferred axes carry inferred:true.

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const HIST = join(ROOT, 'history', 'history.json');
const GEARS = ['clear', 'mixed', 'show'];
const AXES = ['paper_band', 'display_style', 'accent_hue', 'layout_family', 'stage_kind'];

// ---------- args ----------
const argv = process.argv.slice(2);
const opt = {};
for (let i = 0; i < argv.length; i++) {
  if (!argv[i].startsWith('--')) continue;
  const k = argv[i].slice(2);
  const v = argv[i + 1] !== undefined && !argv[i + 1].startsWith('--') ? argv[++i] : true;
  opt[k] = v;
}
const out = (s = '') => console.log(s);

// ---------- 载体别名 ----------
// carriers.json 的 id -> 卡片 medium 值。卡片库里目前只出现 web-desktop web-mobile mp-weixin app-ios app-android。
// 没有直接对应的载体（alipay-mini harmony macos windows）按最近的 medium 猜：
//   alipay-mini 与 wechat-mini 同为小程序，用 mp-weixin。harmony 与 android 同为手机原生，用 app-android。
//   macos 与 windows 是桌面端，用 web-desktop（卡片里的 mac、win 也接受）。
const CARRIER_MEDIUM = {
  'wechat-mini': ['mp-weixin'],
  'alipay-mini': ['mp-weixin'],
  ios: ['app-ios'],
  android: ['app-android'],
  harmony: ['app-android'],
  'mobile-web': ['web-mobile'],
  'desktop-web': ['web-desktop'],
  macos: ['web-desktop', 'mac'],
  windows: ['web-desktop', 'win'],
};
// 卡片写法 -> carriers.json id（用于显示）
const MEDIUM_TO_ID = { 'web-desktop': 'desktop-web', 'web-mobile': 'mobile-web', 'mp-weixin': 'wechat-mini', 'app-ios': 'ios', 'app-android': 'android', mac: 'macos', win: 'windows' };
const CARRIER_IDS = Object.keys(CARRIER_MEDIUM);
const normCarrier = (c) => (c ? (CARRIER_MEDIUM[c] ? c : MEDIUM_TO_ID[c] || null) : null);

// ---------- 帮助 ----------
const KNOWN = ['carrier', 'gear', 'mode', 'topic', 'audience', 'options', 'seed', 'seed-history', 'commit', 'add-history', 'project', 'palette', 'form', 'outcome', 'note', 'list', 'help', 'slot', 'components', 'set-components', 'purpose'];
const SLOTS = ['nav', 'hero', 'cards', 'rows', 'steps', 'panel', 'overlay', 'footer'];
const unknown = argv.filter((a) => a.startsWith('--') && !KNOWN.includes(a.slice(2)));
if (opt.help || argv.length === 0 || unknown.length) {
  if (unknown.length) out(`未知参数：${unknown.join(' ')}`);
  out(`用法
  node toolbox/deal.mjs --carrier <id> --topic <主题> --audience <受众> [--mode persuade|operate|read|experience] [--options 3] [--seed 7]
  node toolbox/deal.mjs --commit <方向id> --project <名> --carrier <id> [--gear 旧字段可省] [--topic t] [--palette id] [--form id,id] [--outcome 好|一般|差] [--note 文字]
  node toolbox/deal.mjs --add-history <方向id> --project <名> [--carrier c --gear g --topic t --note 文字]
  node toolbox/deal.mjs --slot <槽> --purpose "<目的>" --carrier <id> [--options 3] [--seed 7]   阶段 3 发案例，槽见 library/cases.json
  --commit 与 --add-history 可加 --components slot:id,slot:id 记组件手法卡
  node toolbox/deal.mjs --set-components --project <名> --components slot:id,slot:id   阶段 3 选定后补写到该项目最近一条记录
  node toolbox/deal.mjs --list
  node toolbox/deal.mjs --help

--carrier 合法 id（共 ${CARRIER_IDS.length} 个）：${CARRIER_IDS.join(' ')}
  也接受卡片的写法：${Object.keys(MEDIUM_TO_ID).join(' ')}
本命令只打印用法，不发牌。`);
  process.exit(0);
}

// ---------- loading ----------
const readJson = (p) => JSON.parse(readFileSync(p, 'utf8'));
const asArray = (d) => (Array.isArray(d) ? d : d.directions || []);

function inferTaste(c) {
  const tc = (c.typeClasses && c.typeClasses[0]) || 'unknown';
  const pt = c.paletteTags || [];
  const hues = ['teal', 'amber', 'blue', 'green', 'vermilion', 'yellow', 'magenta', 'none'];
  let h = 0;
  for (const ch of c.id) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return {
    ...c,
    medium: c.medium || ['web-desktop', 'web-mobile'],
    mode: c.mode || ['persuade'],
    gear_floor: c.gear_floor || 'mixed',
    taboo: c.taboo || (c.pitfalls ? `代价：${c.pitfalls}` : ''),
    form: c.form || [],
    refs: c.refs || [],
    axes: c.axes || {
      paper_band: pt.includes('dark-neutral') ? 'dark-slate' : pt.includes('light-neutral') ? 'light-white' : 'mid-field',
      display_style: tc,
      accent_hue: hues[h % hues.length],
      layout_family: (c.sectionTags && c.sectionTags[0]) || 'unknown',
      stage_kind: c.motion || 'none',
      inferred: true,
    },
    source: c.source || 'tasteskill',
  };
}

function loadCards() {
  const cards = [];
  const own = join(ROOT, 'library', 'directions.json');
  if (existsSync(own)) cards.push(...asArray(readJson(own)).map((c) => ({ ...c, source: c.source || 'design-pipeline' })));
  else console.error('提示：找不到 library/directions.json');
  const cands = [
    join(ROOT, '..', 'design-taste-frontend', 'library', 'directions.json'),
    join(ROOT, '..', '..', 'design-taste-frontend', 'library', 'directions.json'),
    join(ROOT, '..', '..', 'skills', 'design-taste-frontend', 'library', 'directions.json'),
  ];
  const t = cands.find(existsSync);
  if (t) cards.push(...asArray(readJson(t)).map(inferTaste));
  else console.error('提示：找不到 tasteskill 的 directions.json，只使用自研卡。');
  const seen = new Set();
  return cards
    .map((c) => (c.axes ? c : inferTaste(c)))
    .filter((c) => (seen.has(c.id) ? false : seen.add(c.id)));
}

// 只有文件不存在才算空历史。损坏时：写路径停止（strict），读路径警告后按空历史发牌。
function loadHist(strict = false) {
  let raw;
  try { raw = readFileSync(HIST, 'utf8'); } catch (e) {
    if (e && e.code === 'ENOENT') return { entries: [] };
    return histBad(strict);
  }
  try { return JSON.parse(raw); } catch { return histBad(strict); }
}
function histBad(strict) {
  if (strict) { console.error(`错误：history.json 无法解析，已停止，原文件未改动：${HIST}`); process.exit(1); }
  console.error(`警告：history.json 无法解析，本次按空历史发牌，原文件未改动：${HIST}`);
  return { entries: [] };
}

// ---------- rng ----------
let seed = opt.seed !== undefined && opt.seed !== true ? Number(opt.seed) : Math.floor(Math.random() * 2 ** 31);
const startSeed = seed;
const rnd = () => {
  seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
  let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};
function pickWeighted(items, w) {
  const tot = items.reduce((s, x) => s + w(x), 0);
  let r = rnd() * tot;
  for (const x of items) { r -= w(x); if (r <= 0) return x; }
  return items[items.length - 1];
}

// ---------- helpers ----------
const arr = (x) => (Array.isArray(x) ? x : x ? [x] : []);
const axesDiff = (a, b) => AXES.filter((k) => a.axes?.[k] !== b.axes?.[k]).length;
const firstSentence = (s = '') => (s.split(/(?<=[。.!?])\s*/)[0] || s).trim();

// ---------- component pattern cards (S4) ----------
function parseComponents(v) {
  if (!v || v === true) return [];
  return String(v).split(',').map((x) => x.trim()).filter(Boolean).map((x) => { const [slot, id] = x.split(':'); return { slot, id }; });
}
function loadPatterns() {
  const p = join(ROOT, 'library', 'component-patterns.json');
  if (!existsSync(p)) return null;
  const d = readJson(p);
  return Array.isArray(d) ? d : d.cards || [];
}

// ---------- commands ----------
const cards = loadCards();
const LIB = join(ROOT, 'library');
function loadCases() {
  for (const f of ['cases.json', 'component-patterns.json']) {
    const fp = join(LIB, f);
    if (existsSync(fp)) { const d = JSON.parse(readFileSync(fp, 'utf8')); return d.cases || d.cards || null; }
  }
  return null;
}

if (opt.slot) {
  const slot = String(opt.slot);
  const all = loadCases();
  if (!all) { console.error('错误：找不到 library/cases.json'); process.exit(1); }
  const slots = [...new Set(all.map((c) => c.slot))].sort();
  if (!slots.includes(slot)) { console.error(`错误：--slot 只能是 ${slots.join(' ')}`); process.exit(1); }
  const carrierRaw = opt.carrier && opt.carrier !== true ? opt.carrier : null;
  const carrier = normCarrier(carrierRaw);
  if (carrierRaw && !carrier) { console.error(`错误：未知 --carrier ${carrierRaw}。合法 id：${CARRIER_IDS.join(' ')}`); process.exit(1); }
  const cm = carrier ? CARRIER_MEDIUM[carrier] : null;
  const purpose = opt.purpose && opt.purpose !== true ? String(opt.purpose) : '';
  const N = Math.max(1, Number(opt.options) || 3);
  const inSlot = all.filter((c) => c.slot === slot);
  const byCarrier = inSlot.filter((c) => { const cs = arr(c.carriers).length ? arr(c.carriers) : arr(c.medium); return !cm || cs.some((m) => cm.includes(m) || normCarrier(m) === carrier); });
  // 目的筛选：按词命中 purpose / name / why，命中 ≥3 条才收窄，否则全给
  // 中文无空格：把目的切成 2 字片段，命中 ≥2 个片段算命中
  const chunks = purpose ? purpose.replace(/[，。、；：,.;:!?！？"“”'‘’（）()\s]+/g, ' ').split(' ').filter(Boolean) : [];
  const toks = [...new Set(chunks.flatMap((w) => (w.length <= 2 ? [w] : Array.from({ length: w.length - 1 }, (_, i) => w.slice(i, i + 2)))))];
  const STOP = new Set(['让人', '一眼', '可以', '知道', '第一', '一个', '怎么', '什么', '本页', '读者', '用户']);
  const hit = (c) => { const t = `${c.purpose || ''} ${c.name || ''} ${c.why || ''}`; return toks.filter((k) => !STOP.has(k) && t.includes(k)).length >= 2; };
  let pool = byCarrier;
  let narrowed = false;
  if (toks.length) { const m = byCarrier.filter(hit); if (m.length >= 3) { pool = m; narrowed = true; } }
  const hist = loadHist().entries || [];
  const recent = new Set(hist.slice(-5).flatMap((e) => arr(e.components).filter((x) => x.slot === slot).map((x) => x.id)));
  const useCount = (id) => hist.filter((e) => arr(e.components).some((x) => x.id === id)).length;
  out(`发案例：slot=${slot} carrier=${carrier || '任意'} purpose=${purpose || '-'} seed=${startSeed}`);
  out(`该槽共 ${inSlot.length} 条，载体筛后 ${byCarrier.length} 条${toks.length ? (narrowed ? `，目的命中 ${pool.length} 条` : '，目的命中不足 3 条，全池发') : ''}。`);
  if (!pool.length) { out('没有可用案例。去掉 --carrier，或写"库外自拟"，收口后补库。'); out('库薄提示：该槽无可发案例，先做补调研（stages/3-components.md 第 5.5 节）。'); process.exit(0); }
  let dealPool = pool.filter((c) => !recent.has(c.id));
  if (recent.size && dealPool.length) out(`已排除最近 5 条使用史里同槽用过的案例：${[...recent].join(', ')}`);
  if (!dealPool.length) { dealPool = pool; out('最近 5 条已用尽可用池，回到全池。'); }
  const dealt = [];
  let left = dealPool.slice();
  while (dealt.length < N && left.length) { const p = pickWeighted(left, (c) => 1 / (1 + useCount(c.id))); dealt.push(p); left = left.filter((c) => c.id !== p.id); }
  if (dealt.length < N) out(`说明：只发出 ${dealt.length} 条（可用池不足 ${N} 条，全给）。`);
  // 库薄提示：命中池少于 3 条，或发出的卡里没有一条亲核打开或本库已做出
  const trusted = (c) => arr(c.seen_at).some((r) => r.how_checked === '亲核打开' || r.how_checked === '本库已做出');
  if (pool.length < N || !dealt.some(trusted)) out(`库薄提示：${pool.length < N ? `命中池只有 ${pool.length} 条` : '发出的卡全是二手摘要'}。先做补调研（stages/3-components.md 第 5.5 节），再决定选卡或库外自拟。`);
  out();
  dealt.forEach((c, i) => {
    out(`=== 案例 ${String.fromCharCode(65 + i)}：${c.name}（${c.id}）  载体 ${(arr(c.carriers).length ? arr(c.carriers) : arr(c.medium)).join(',')}`);
    out(`目的：${c.purpose || c.idea || ''}`);
    out(`为什么好：${c.why || ''}`);
    if (c.structure) out(`结构起点：${c.structure}`);
    if (c.mechanism) out(`机制：${arr(c.mechanism).join(', ') || c.mechanism}`);
    out(`适合氛围：${arr(c.atmosphere_fit).join('、') || '未写'}（提示，不是过滤）`);
    if (c.depends_on && c.depends_on !== "无") out(`依赖条件：${c.depends_on}`);
    arr(c.adapt).forEach((q, k) => out(`改写提问 ${k + 1}：${q}`));
    out(`Reduce Motion：${c.reduce_motion || '未写'}`);
    out(`避开：${arr(c.avoids).join(', ') || '无'}   实现：${c.impl || '无'}   tasteskill：${arr(c.tasteskill_id).join(', ') || '无'}`);
    arr(c.seen_at).slice(0, 3).forEach((r) => out(`出处：${r.site || r.name} ${r.year || '?'}（${r.how_checked || (r.verified ? '已核' : '二手摘要')}）`));
    arr(c.refs).slice(0, 3).forEach((r) => out(`出处：${r.name} ${r.year || '?'}${r.verified ? '' : '（二手摘要）'}`));
    if (c.risks) out(`风险：${c.risks}`);
    out();
  });
  out('下一步：选 1 条填进 design.md 第 2 节"案例 id"列，回答改写提问写"本页怎么改"。都不合适写"库外自拟"，收口后补库。选定后 --set-components --project <名> --components slot:id。');
  process.exit(0);
}

if (opt.list) {
  out(`可用方向卡 ${cards.length} 张`);
  for (const c of cards) out(`${c.id.padEnd(26)} ${c.source.padEnd(16)} ${arr(c.medium).join(',')}  floor=${c.gear_floor}  ${c.name}`);
  process.exit(0);
}

if (opt['set-components']) {
  if (!opt.project || opt.project === true) { console.error('错误：--set-components 需要 --project'); process.exit(1); }
  const comps = parseComponents(opt.components);
  if (!comps.length) { console.error('错误：--set-components 需要 --components slot:id,slot:id'); process.exit(1); }
  const h = loadHist(true);
  h.entries = h.entries || [];
  const idx = h.entries.map((e) => e.project).lastIndexOf(opt.project);
  if (idx < 0) { console.error(`错误：history 里没有项目 ${opt.project}。先在 S3 用 --commit 记录。`); process.exit(1); }
  const seen = new Set();
  h.entries[idx].components = [...arr(h.entries[idx].components), ...comps].filter((x) => { const k = `${x.slot}:${x.id}`; if (seen.has(k)) return false; seen.add(k); return true; });
  writeFileSync(HIST, JSON.stringify(h, null, 2) + '\n');
  out(`已补写组件手法：${opt.project} -> ${h.entries[idx].components.map((x) => `${x.slot}:${x.id}`).join(', ')}`);
  process.exit(0);
}

if (opt['add-history']) {
  const id = String(opt['add-history']);
  if (!cards.find((c) => c.id === id)) { console.error(`错误：未知方向 id ${id}。用 --list 查看。`); process.exit(1); }
  if (!opt.project || opt.project === true) { console.error('错误：--add-history 需要 --project'); process.exit(1); }
  if (opt.gear && !GEARS.includes(opt.gear)) { console.error('错误：--gear 只能是 clear mixed show'); process.exit(1); }
  const sv = (k) => (opt[k] && opt[k] !== true ? opt[k] : null);
  const h = loadHist(true);
  const entry = {
    date: new Date().toISOString().slice(0, 10),
    project: opt.project,
    carrier: sv('carrier'),
    gear: sv('gear'),
    topic: sv('topic'),
    direction: id,
    palette: sv('palette'),
    form: arr(cards.find((c) => c.id === id).form),
    outcome: sv('outcome'),
    note: sv('note') || '',
    components: parseComponents(opt.components),
    source: 'manual',
  };
  h.entries = h.entries || [];
  h.entries.push(entry);
  mkdirSync(dirname(HIST), { recursive: true });
  writeFileSync(HIST, JSON.stringify(h, null, 2) + '\n');
  out(`已追加手工记录：${entry.project} -> ${id}（history 共 ${h.entries.length} 条）`);
  process.exit(0);
}

if (opt.commit) {
  const id = String(opt.commit);
  if (!cards.find((c) => c.id === id)) { console.error(`错误：未知方向 id ${id}。用 --list 查看。`); process.exit(1); }
  for (const k of ['project', 'carrier']) if (!opt[k] || opt[k] === true) { console.error(`错误：--commit 需要 --${k}`); process.exit(1); }
  if (opt.gear && !GEARS.includes(opt.gear)) { console.error('错误：--gear 只能是 clear mixed show'); process.exit(1); }
  if (opt.outcome && !['好', '一般', '差'].includes(opt.outcome)) { console.error('错误：--outcome 只能是 好 一般 差'); process.exit(1); }
  const h = loadHist(true);
  const entry = {
    date: new Date().toISOString().slice(0, 10),
    project: opt.project,
    carrier: opt.carrier,
    gear: opt.gear && opt.gear !== true ? opt.gear : null,
    topic: opt.topic && opt.topic !== true ? opt.topic : null,
    direction: id,
    palette: opt.palette && opt.palette !== true ? opt.palette : null,
    form: opt.form && opt.form !== true ? String(opt.form).split(',') : arr(cards.find((c) => c.id === id).form),
    outcome: opt.outcome || null,
    note: opt.note && opt.note !== true ? opt.note : '',
    components: parseComponents(opt.components),
  };
  h.entries = h.entries || [];
  h.entries.push(entry);
  mkdirSync(dirname(HIST), { recursive: true });
  writeFileSync(HIST, JSON.stringify(h, null, 2) + '\n');
  out(`已记录：${entry.date} ${entry.project} ${entry.carrier}/${entry.gear} -> ${id}（history 共 ${h.entries.length} 条）`);
  process.exit(0);
}

// ---------- deal ----------
const carrierRaw = opt.carrier && opt.carrier !== true ? opt.carrier : null;
const carrier = normCarrier(carrierRaw);
if (carrierRaw && !carrier) { console.error(`错误：未知 --carrier ${carrierRaw}。合法 id：${CARRIER_IDS.join(' ')}`); process.exit(1); }
const carrierMedium = carrier ? CARRIER_MEDIUM[carrier] : null;
const gear = opt.gear && opt.gear !== true ? opt.gear : null;
const mode = opt.mode && opt.mode !== true ? opt.mode : null;
const topic = opt.topic && opt.topic !== true ? opt.topic : null;
const audience = opt.audience && opt.audience !== true ? opt.audience : null;
const N = Math.max(1, Number(opt.options) || 3);
if (gear && !GEARS.includes(gear)) { console.error('错误：--gear 只能是 clear mixed show'); process.exit(1); }

let pool = cards.filter((c) => {
  if (carrierMedium && !arr(c.medium).some((m) => carrierMedium.includes(m) || normCarrier(m) === carrier)) return false;
  if (gear && GEARS.indexOf(gear) < GEARS.indexOf(c.gear_floor || 'clear')) return false;
  if (mode && !arr(c.mode).includes(mode)) return false;
  return true;
});
out(`发牌：carrier=${carrier || '任意'} gear=${gear || "任意"} mode=${mode || '任意'} topic=${topic || '-'} audience=${audience || '-'} seed=${startSeed}`);
out(`过滤后可用 ${pool.length} 张。`);
if (pool.length === 0) { out('没有可用卡。放宽 --gear 或 --mode，或先补自研卡。'); process.exit(0); }

const hist = loadHist().entries || [];
const seedHist = opt['seed-history'] && opt['seed-history'] !== true ? String(opt['seed-history']).split(',').map((x) => x.trim()).filter(Boolean) : [];
const recent = new Set([...hist.slice(-5).map((e) => e.direction), ...seedHist]);
const fresh = pool.filter((c) => !recent.has(c.id));
let dealPool = pool;
if (recent.size) {
  if (fresh.length >= N) { dealPool = fresh; out(`已排除最近 5 次用过的方向：${[...recent].join(', ')}`); }
  else if (fresh.length > 0) { dealPool = fresh; out(`最近 5 次用过的方向已排除（${[...recent].join(', ')}），剩 ${fresh.length} 张，少于 ${N}。`); }
  else out('最近 5 次已用尽可用池，回到全池。');
}

const useCount = (id) => hist.filter((e) => e.direction === id).length;
const bad = (id) => hist.some((e) => e.direction === id && e.outcome === '差' && normCarrier(e.carrier) === carrier && (!topic || e.topic === topic));
const text = (c) => `${c.name} ${c.idea} ${arr(c.sectors).join(' ')}`;
const match = (c, key, q) => {
  if (!q) return 0;
  let n = 0;
  if (arr(c[key]).some((x) => String(x).includes(q) || q.includes(String(x)))) n++;
  if (text(c).includes(q)) n++;
  return n;
};
const weight = (c) => {
  let w = 1 / (1 + useCount(c.id));
  if (bad(c.id)) w *= 0.5;
  w *= 3 ** Math.min(2, match(c, 'topics', topic));
  w *= 3 ** Math.min(2, match(c, 'audience', audience));
  return w;
};

const dealt = [];
let minDiff = 3;
let relaxed = false;
let left = dealPool.slice();
while (dealt.length < N && left.length) {
  let cand = dealt.length === 0 ? left : left.filter((c) => dealt.every((d) => axesDiff(c, d) >= minDiff));
  while (!cand.length && minDiff > 1) {
    minDiff--; relaxed = true;
    cand = left.filter((c) => dealt.every((d) => axesDiff(c, d) >= minDiff));
  }
  if (!cand.length) break;
  const p = pickWeighted(cand, weight);
  dealt.push(p);
  left = left.filter((c) => c.id !== p.id);
}
if (relaxed) out(`说明：凑不齐两两 3 轴不同，已放宽到至少 ${minDiff} 轴。`);
if (dealt.length < N) out(`说明：只发出 ${dealt.length} 张（可用池不足 ${N} 张）。`);
out();

dealt.forEach((c, i) => {
  out(`=== 方向 ${String.fromCharCode(65 + i)}：${c.name}（${c.id}）  来源 ${c.source}`);
  out(`点子：${firstSentence(c.idea)}`);
  out(`axes：${AXES.map((k) => `${k}=${c.axes[k]}`).join('  ')}${c.axes.inferred ? '  （推断）' : ''}`);
  out(`form：${arr(c.form).join(', ') || '无'}   载体：${arr(c.medium).join(',')}   模式：${arr(c.mode).join(',')}   预算预设下限：${c.gear_floor}`);
  const rf = arr(c.refs).slice(0, 2);
  if (rf.length) rf.forEach((r) => out(`参照：${r.name} ${r.url || ''}（${r.year || '?'}）${r.what || ''}`));
  else if (arr(c.seenIn).length) out(`参照：tasteskill 研究站 ${arr(c.seenIn).slice(0, 2).join(', ')}`);
  else out('参照：无');
  const tb = (c.taboo || '未写').replace(/^代价：/, '');
  out(`选它的代价：${tb.length > 160 ? tb.slice(0, 160) + '...' : tb}`);
  out();
});
if (dealt.length > 1) {
  const pairs = [];
  for (let i = 0; i < dealt.length; i++) for (let j = i + 1; j < dealt.length; j++) pairs.push(`${dealt[i].id}~${dealt[j].id}:${axesDiff(dealt[i], dealt[j])}`);
  out(`两两 axes 差异数：${pairs.join('  ')}`);
}
out('下一步：选定后用 --commit <id> --project <名> --carrier <c> 记录。');
