#!/usr/bin/env node
// pick-form.mjs: pick page forms for design-pipeline (R5 section 3.2, ten rules).
// Node 24, no dependencies.
//
// Usage
//   node toolbox/pick-form.mjs --task explainer|launch|prototype|datastory --chapters <n>
//        --reading skim|sequential --carrier desktop_web|mobile_web|miniprogram（也接受 carriers.json 的 9 个 id）
//        [--options 3]
//
// Method
//   1. Start with all forms in library/page-forms.json.
//   2. Run the rules in order. A rule either excludes forms, boosts forms (+1), or penalises forms (-2).
//   3. Base score = fit for the task (high 3, mid 2, low 1). Sort by score, then by id.
//   4. Forms with status "not-recommended" join the pool only if no other candidate remains.
//   5. Rule 10: at least one pick that is not P13.
//      Rules 3 and 4 no longer exist (removed with the old budget presets). Other rule numbers are unchanged.
// The script does not tune rules to match the quick-reference table in R5 section 3.3.

import { readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const DATA = JSON.parse(readFileSync(join(ROOT, 'library', 'page-forms.json'), 'utf8'));
const FORMS = DATA.forms;

const argv = process.argv.slice(2);
const opt = {};
for (let i = 0; i < argv.length; i++) {
  if (!argv[i].startsWith('--')) continue;
  const k = argv[i].slice(2);
  opt[k] = argv[i + 1] !== undefined && !argv[i + 1].startsWith('--') ? argv[++i] : true;
}

// carriers.json 的 id -> 本脚本的三类页面载体。原生 App 与小程序之外的端按最近的页面形态猜：
//   wechat-mini alipay-mini -> miniprogram。ios android harmony mobile-web -> mobile_web（手机竖屏页面）。
//   desktop-web macos windows -> desktop_web（桌面宽屏页面）。
const CARRIER_ALIAS = {
  'wechat-mini': 'miniprogram', 'alipay-mini': 'miniprogram',
  ios: 'mobile_web', android: 'mobile_web', harmony: 'mobile_web', 'mobile-web': 'mobile_web',
  'desktop-web': 'desktop_web', macos: 'desktop_web', windows: 'desktop_web',
};
if (opt.carrier in CARRIER_ALIAS) opt.carrier = CARRIER_ALIAS[opt.carrier];

const TASKS = ['explainer', 'launch', 'prototype', 'datastory'];
const TASK_ZH = { explainer: '讲解页', launch: '发布页', prototype: '产品原型', datastory: '数据叙事' };
const READINGS = ['skim', 'sequential'];
const CARRIERS = ['desktop_web', 'mobile_web', 'miniprogram'];
const FIT = { high: 3, mid: 2, low: 1 };
const FIT_ZH = { high: '高', mid: '中', low: '低' };

const HELP_FLAGS = ['task', 'chapters', 'reading', 'carrier', 'options', 'help'];
const badFlags = argv.filter((a) => a.startsWith('--') && !HELP_FLAGS.includes(a.slice(2)));
if (opt.help || argv.length === 0 || badFlags.length) {
  if (badFlags.length) console.log(`未知参数: ${badFlags.join(' ')}`);
  console.log(`用法: node toolbox/pick-form.mjs --task ${TASKS.join('|')} --chapters <n> --reading ${READINGS.join('|')} --carrier <id> [--options 3]
--carrier 合法值: ${CARRIERS.join(' ')}
  也接受 carriers.json 的 9 个 id: ${Object.keys(CARRIER_ALIAS).join(' ')}
本命令只打印用法，不选形态。`);
  process.exit(0);
}

function usage(msg) {
  if (msg) console.error('错误: ' + msg);
  console.error('用法: node toolbox/pick-form.mjs --task explainer|launch|prototype|datastory --chapters <n> ' +
    '--reading skim|sequential --carrier desktop_web|mobile_web|miniprogram [--options 3]');
  process.exit(2);
}
const oneOf = (name, list) => (list.includes(opt[name]) ? opt[name] : usage(`--${name} 取值必须是 ${list.join('|')}`));
const task = oneOf('task', TASKS);
const reading = oneOf('reading', READINGS);
const carrier = oneOf('carrier', CARRIERS);
const chapters = Number(opt.chapters);
if (!Number.isInteger(chapters) || chapters < 1) usage('--chapters 必须是正整数');
const want = Math.min(3, Math.max(1, Number(opt.options ?? 3) || 3));

// ---------- state ----------
const state = new Map(FORMS.map((f) => [f.id, { f, excluded: [], boosts: [], score: FIT[f.fit[task]] }]));
const notes = [];
const exclude = (ids, rule, why) => {
  for (const id of ids) {
    const s = state.get(id);
    if (s && !s.excluded.some((e) => e.rule === rule)) s.excluded.push({ rule, why });
  }
};
const boost = (ids, rule, why, delta = 1) => {
  for (const id of ids) {
    const s = state.get(id);
    if (!s) continue;
    s.score += delta;
    s.boosts.push({ rule, why, delta });
  }
};

// ---------- rules (R5 3.2, in order) ----------
// Rule 1
if (task === 'prototype') {
  const keep = ['P12', 'P14', 'P11', 'P09'];
  exclude(FORMS.map((f) => f.id).filter((id) => !keep.includes(id)), 1, '产品原型只在 P12、P14、P11、P09 中选');
  exclude(['P02', 'P15'], 1, '产品原型排除 P02、P15');
}
// Rule 2
if (carrier === 'miniprogram') {
  exclude(['P02', 'P07'], 2, '小程序排除 P02、P07');
  notes.push('规则 2: P04 在小程序只能用 scroll-view 横向，不用 pin。');
  boost(['P12', 'P03', 'P05'], 2, '小程序优先 P12、P03、P05');
}
// Rule 5
if (reading === 'skim') {
  exclude(['P05', 'P04'], 5, '快速跳读排除 P05、P04 作主形态');
  boost(['P01', 'P06', 'P11', 'P12'], 5, '快速跳读优先 P01、P06、P11、P12');
  notes.push('规则 5: 快速跳读必须带全局目录。');
}
// Rule 6
if (reading === 'sequential') boost(['P03', 'P13', 'P05', 'P08'], 6, '顺序讲解优先 P03、P13、P05、P08');
// Rule 7
if (chapters >= 10) {
  exclude(['P02', 'P07'], 7, '10 章以上排除 P02、P07');
  boost(['P11', 'P13'], 7, '10 章以上用 P11 分房间，或 P13');
}
// Rule 8
if (chapters >= 3 && chapters <= 5) {
  boost(['P05', 'P12'], 8, '3 到 5 章 P05、P12 可以撑住');
  boost(['P01'], 8, '3 到 5 章 P01 的画布会显得空', -2);
}
// Rule 9
if (task === 'datastory') boost(['P03', 'P10', 'P08', 'P06'], 9, '数据叙事优先 P03、P10、P08、P06');

// ---------- pool and pick (rule 10) ----------
const byScore = (a, b) => b.score - a.score || a.f.id.localeCompare(b.f.id);
const live = [...state.values()].filter((s) => s.excluded.length === 0);
let pool = live.filter((s) => s.f.status !== 'not-recommended').sort(byScore);
const flagged = live.filter((s) => s.f.status === 'not-recommended').sort(byScore);
if (pool.length === 0) {
  pool = flagged;
  notes.push('没有其他候选，才给出标"不推荐"的形态。');
}
const picks = pool.slice(0, want);
const rest = pool.slice(want);

if (picks.length > 0 && picks.every((s) => s.f.id === 'P13')) {
  const cand = rest.find((s) => s.f.id !== 'P13');
  if (cand) {
    notes.push(`规则 10: 用 ${cand.f.id} 替换一个 P13，至少一个候选不是 P13。`);
    picks.pop();
    picks.push(cand);
  } else {
    notes.push('规则 10: 没有非 P13 的候选可用。');
  }
}
picks.sort(byScore);

// ---------- output ----------
const out = (s = '') => console.log(s);
const rangeText = (f) => `${f.chapter_range[0]} 到 ${f.chapter_range[1]} ${f.unit}`;
const whyLine = (s) => {
  const f = s.f;
  const parts = [`${TASK_ZH[task]}适合度${FIT_ZH[f.fit[task]]}`];
  for (const b of s.boosts) parts.push(`规则 ${b.rule}${b.delta < 0 ? ' 减分' : ''}: ${b.why}`);
  const c = f.carriers[carrier];
  if (typeof c === 'string') parts.push(`${carrier} 退化: ${c}`);
  return parts.join('。') + '。';
};

out(`输入: task=${task}(${TASK_ZH[task]}) chapters=${chapters} reading=${reading} carrier=${carrier} options=${want}`);
out(`推荐 ${picks.length} 种形态:`);
picks.forEach((s, i) => {
  const f = s.f;
  const mark = f.status === 'not-recommended' ? ' [不推荐]': '';
  out(`${i + 1}. ${f.id} ${f.name_zh}${mark}: ${f.one_liner}`);
  out(`   数量范围=${rangeText(f)} 分数=${s.score}`);
  out(`   为什么是它: ${whyLine(s)}`);
});
if (rest.length) out(`备选(未入选): ${rest.slice(0, 3).map((s) => `${s.f.id}(${s.score})`).join(' ')}`);
const dropped = [...state.values()].filter((s) => s.excluded.length);
if (dropped.length || flagged.length) {
  out('被排除:');
  for (const s of dropped) out(`- ${s.f.id} ${s.f.name_zh}: ${s.excluded.map((e) => `规则 ${e.rule} (${e.why})`).join('；')}`);
  if (picks.every((p) => p.f.status !== 'not-recommended'))
    for (const s of flagged) out(`- ${s.f.id} ${s.f.name_zh} [不推荐]: ${s.f.not_recommended_reason}`);
}
for (const n of notes) out(`注: ${n}`);
out('提示: 用“纯瀑布流三问”检查结果。Q1 骨架是否全相同，Q2 滚动是否只改变位置，Q3 读者能否一眼看到全局并跳章。三问都为“是”就是纯瀑布流。');
