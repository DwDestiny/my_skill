// E1 S5：两张图纸的 2D 画布相机 {x, y, s, r}、幕 0b 接缝、P11 换图、小地图、详图引出、首屏签名时刻、舞台模块挂载。
// 机制借自 examples/mechanisms（scroll-camera-path 的站点结构、fluid-ink-pointer 的纤维渗印、depth-parallax-image 的两层速度差），皮肤用方向单 v0.4。
// 补间：自带 rAF 补间从第 0 秒可用；GSAP 在 5 s 内到达时热切换到 gsap.ticker。两者都用本文件的缓动函数，读者看不到两种相机。
import { boot } from './engine/motion-engine-gsap.js';

const root = document.documentElement;
const RM = matchMedia('(prefers-reduced-motion: reduce)').matches;
const $ = (id) => document.getElementById(id);
const $$ = (sel, el = document) => [...el.querySelectorAll(sel)];
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const smooth = (a, b, v) => { const t = clamp((v - a) / (b - a)); return t * t * (3 - 2 * t); };
const easeIO = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const ease2 = (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
const ASSETS = '../assets/generated/';

// ---------- 补间：GSAP 未到时自带 rAF，到了热切换 ----------
let gsap = null;
function tween(dur, fn, done) {
  if (gsap) {
    const k = { t: 0 };
    const tw = gsap.to(k, { t: 1, duration: dur, ease: 'none', onUpdate: () => fn(k.t), onComplete: () => done?.() });
    return { kill: () => tw.kill(), active: () => tw.isActive() };
  }
  let id = 0, on = true; const t0 = performance.now();
  const step = (now) => { if (!on) return; const t = clamp((now - t0) / (dur * 1000)); fn(t); if (t < 1) id = requestAnimationFrame(step); else { on = false; done?.(); } };
  id = requestAnimationFrame(step);
  return { kill: () => { on = false; cancelAnimationFrame(id); }, active: () => on };
}
const t0Boot = performance.now();
const pollGsap = setInterval(() => {
  if (window.gsap) { gsap = window.gsap; gsap.ticker.lagSmoothing(0); root.dataset.tween = 'gsap'; clearInterval(pollGsap); }
  else if (performance.now() - t0Boot > 5000) { root.dataset.tween = 'native'; clearInterval(pollGsap); }
}, 200);

// ---------- 详图引出（所有图幅，桌面与纵向形态都要） ----------
function wireDetail(btn) {
  const d = $(btn.getAttribute('aria-controls')); if (!d) return;
  const close = d.querySelector('.close');
  const set = (open) => {
    d.hidden = !open; btn.setAttribute('aria-expanded', String(open));
    (open ? close || d : btn).focus?.({ preventScroll: true });
  };
  btn.addEventListener('click', () => set(d.hidden));
  close?.addEventListener('click', () => set(false));
  d.addEventListener('keydown', (e) => { if (e.key === 'Escape') { e.stopPropagation(); set(false); } });
}
$$('button.callout[aria-controls]').forEach(wireDetail);
const anyDetailOpen = () => $$('.detail').some((d) => !d.hidden);

// ---------- 首屏签名时刻：标题 → 图签（硫酸纸揭开）→ 相机推近 0.6 s → 章落定 → 渗印 0.8 s → 回正 ----------
const CAM = root.classList.contains('cam');
const hero = $('hero'), heroTb = $('heroTb'), seal = $('seal');
const INK = { size: 288, spread: 0.45, alpha: 0.5, rotate: 4, duration: 800 }; // v0.4 下限：canvas ≥256，渗出 ≥0.4 章宽，终态 ≥0.45

const stampInk = () => import('./ink.js').then((m) => m.bleed(seal, { ...INK, parent: $('sealBox') })).catch(() => {});

let pushed = false, unpushT = 0;
function setPush(on) {
  if (!CAM || RM || pushed === on) return;
  pushed = on;
  if (on) {
    // 推近 1.25 倍，同时把图签中心移向视口中心，放大后的图签整张留在视口内（边距 24 px）
    const K = 1.25, w = heroTb.offsetWidth * K, h = heroTb.offsetHeight * K, vw0 = innerWidth, vh0 = innerHeight;
    const cx = heroTb.offsetLeft + heroTb.offsetWidth / 2, cy = heroTb.offsetTop + heroTb.offsetHeight / 2;
    const gx = clamp(cx + (vw0 / 2 - cx) * 0.35, w / 2 + 24, vw0 - w / 2 - 24), gy = clamp(cy + (vh0 / 2 - cy) * 0.35, h / 2 + 24, vh0 - h / 2 - 24);
    hero.style.transformOrigin = '0 0';
    // 照片放大后仍要盖满视口：平移限制在 [视口 × (1 − K), 0]
    const tx = clamp(gx - K * cx, vw0 * (1 - K), 0), ty = clamp(gy - K * cy, vh0 * (1 - K), 0);
    hero.style.setProperty('--push', `translate(${tx.toFixed(1)}px, ${ty.toFixed(1)}px) scale(${K})`);
  }
  hero.classList.toggle('push', on);
}
let stamped = false;
const afterSeal = () => { if (stamped) return; stamped = true; stampInk().then(() => { unpushT = setTimeout(() => setPush(false), 900); }); };
if (RM) afterSeal();
else {
  setTimeout(() => { if (scrollY < 4) setPush(true); }, 1100);
  seal.addEventListener('animationend', afterSeal, { once: true });
  setTimeout(afterSeal, 2600);
}

// ---------- 图幅登记：几何取自 DOM 的 --x/--y/--w/--h，唯一源 ----------
const ORDER = ['s1', 's2', 's0', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11'];
const READABLE = new Set(['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10']); // 已读计数的 10 个章图幅
const STAGE_MODS = new Set(['s2', 's5', 's8']);
const SH = {};
ORDER.forEach((id, i) => {
  const el = $(id); const g = (k) => parseFloat(el.style.getPropertyValue('--' + k));
  SH[id] = { id, i, el, no: el.dataset.no, dwg: +el.dataset.dwg, x: g('x'), y: g('y'), w: g('w'), h: g('h'),
    stage: el.classList.contains('sheet-stage'), name: el.querySelector('.ov-label')?.textContent.replace(/^\d+/, '') || '' };
});
const DW = [1, 2].map((d) => { const el = $('dwg' + d); return { d, el, paper: el.querySelector('.paper'), content: el.querySelector('.content') }; });

// ---------- 已读铅笔勾 ----------
const read = new Set();
function markRead(id) {
  if (read.has(id) || !READABLE.has(id)) return;
  read.add(id);
  $$(`.m-tick[data-s="${id}"]`).forEach((t) => t.classList.add('on'));
  SH[id].el.classList.add('is-read');
  const li = document.querySelector(`[data-read-list] li[data-sheet="${id}"]`);
  if (li && li.dataset.count !== '0') li.classList.add('on');
  const n = document.querySelector('[data-read-count]');
  if (n) n.textContent = String($$('[data-read-list] li.on:not([data-count="0"])').length);
}

// ---------- 舞台模块：停靠时 import，离开两幅以外时 destroy；模块不存在时静默跳过 ----------
const stages = {};
// terminal = true：挂静态终态（总览、纵向形态）。停靠时若已有终态挂载，先销毁再按非终态重挂，保留落章与渗印时刻
function mountStage(id, terminal = false) {
  if (!STAGE_MODS.has(id)) return null;
  const old = stages[id];
  if (old && (terminal || !old.terminal)) return old;
  if (old) { old.dead = true; try { old.inst?.destroy?.(); } catch (_) { /* 模块自己负责清理 */ } delete stages[id]; }
  const host = SH[id].el.querySelector('.stage-mount'); if (!host) return null;
  const rec = stages[id] = { inst: null, dead: false, played: false, last: null, terminal };
  import(`./stage-${id}.js?v=s6fix`).then((m) => {
    if (rec.dead || typeof m.mount !== 'function') return;
    rec.inst = m.mount(host, { assets: ASSETS, reduced: RM || terminal, webgl: !RM && CAM });
    if (terminal) { rec.inst?.set?.(id === 's5' ? 5 : 1); rec.inst?.play?.(); }
    else if (rec.last != null) drive(id, rec.last);
    if (!CAM && id === 's2') fitFlow(host);
  }).catch(() => { rec.dead = true; if (id === 's8') s8Reveal(); });
  return rec;
}
// 纵向形态：s2 舞台按 1400 x 1100 的设计尺寸整体缩放到图幅宽
function fitFlow(host) {
  const f = () => { const k = host.clientWidth / 1400; host.style.setProperty('--k', k.toFixed(4)); host.style.height = Math.round(1100 * k) + 'px'; };
  f(); addEventListener('resize', f);
}
// 总览：舞台图幅挂终态，12 格都有图形。总览态不调用 unmountFar
function ovStages(d) { ['s2', 's5', 's8'].forEach((id) => { if (SH[id].dwg === d) mountStage(id, true); }); }
function unmountFar(cur) {
  const ci = SH[cur]?.i ?? -9;
  Object.keys(stages).forEach((id) => {
    if (Math.abs(SH[id].i - ci) <= 2) return;
    const rec = stages[id]; rec.dead = true; try { rec.inst?.destroy?.(); } catch (_) { /* 模块自己负责清理 */ }
    delete stages[id];
  });
}
// s2 步骤说明：每步 0.2，当前步高亮
const steps = $$('#s2 li[data-step]');
function stepOn(t) {
  const k = Math.min(5, Math.floor(t * 5) + 1);
  steps.forEach((li) => { const on = +li.dataset.step === k; li.classList.toggle('on', on); on ? li.setAttribute('aria-current', 'step') : li.removeAttribute('aria-current'); });
}
// s8 条文对照：渗印完成（C 派发 s8:inked）后露出；模块失败或超时 2.6 s 也露出
const s8Text = document.querySelector('[data-s8-text]');
function s8Reveal() { s8Text?.classList.remove('is-wait'); }
// 桌面相机形态：阅读图幅内容底边到图签顶边空白 >350 px 时，图幅内 details 默认展开；纵向形态保持折叠。详图（.detail）不自动展开
function gapOf(el) {
  const tb = el.querySelector('.sheet-tb'); if (!tb) return 0;
  const kids = [...el.children].filter((c) => c !== tb && !c.matches('.detail, .ov-label, .sheet-notes'));
  return tb.offsetTop - Math.max(0, ...kids.map((c) => c.offsetTop + c.offsetHeight));
}
if (CAM) (document.fonts?.ready || Promise.resolve()).then(() => {
  $$('.sheet.sheet-read[data-no]').forEach((el) => { if (gapOf(el) > 350) el.querySelectorAll('details').forEach((d) => { d.open = true; }); });
});
// s3 修改云线注记的引出线：从注记上边连到云线格下边（按未缩放尺寸算）
function leaders() {
  $$('.rev-note[data-lead]').forEach((n) => {
    const c = document.getElementById(n.dataset.lead); if (!c) return;
    const sh = n.closest('.sheet'), k = sh.getBoundingClientRect().width / sh.offsetWidth || 1;
    const rn = n.getBoundingClientRect(), rc = c.getBoundingClientRect();
    const lx = (rc.left + rc.width / 2 - rn.left) / k, lh = (rn.top - rc.bottom) / k - 6;
    n.style.setProperty('--lx', lx.toFixed(1) + 'px'); n.style.setProperty('--lh', Math.max(0, lh).toFixed(1) + 'px');
    n.querySelector('.lead path')?.setAttribute('d', `M1 0 V${Math.max(0, lh).toFixed(1)}`);
    n.querySelector('.lead')?.setAttribute('height', Math.max(0, lh).toFixed(1));
  });
}
(document.fonts?.ready || Promise.resolve()).then(leaders); addEventListener('resize', leaders);
window.__gap = () => Object.fromEntries($$('.sheet[data-no]').map((el) => [el.id, gapOf(el)]));
if (CAM && !RM && s8Text) { s8Text.classList.add('is-wait'); $('s8').addEventListener('s8:inked', () => setTimeout(s8Reveal, 300)); }
function drive(id, v) {
  if (id === 's2') stepOn(v);
  const rec = stages[id]; if (!rec) return; rec.last = v;
  const inst = rec.inst; if (!inst) return;
  try {
    if (id === 's2') inst.set?.(v);
    else if (id === 's5') inst.set?.(v);
    else if (id === 's8' && v >= 1 && !rec.played) { rec.played = true; inst.play?.(); setTimeout(() => s8Reveal(), 2600); }
  } catch (_) { /* 舞台错误不拖垮相机 */ }
}

// ---------- 纵向形态（<1280 宽）：图号条跟随，舞台按进入视口挂载终态 ----------
if (!CAM) {
  const links = Object.fromEntries($$('.strip ol a').map((a) => [a.getAttribute('href').slice(1), a]));
  const ol = document.querySelector('.strip ol');
  const io = new IntersectionObserver((es) => es.forEach((e) => {
    if (!e.isIntersecting) return;
    const id = e.target.id;
    Object.values(links).forEach((a) => a.removeAttribute('aria-current'));
    const a = links[id]; if (!a) return;
    a.setAttribute('aria-current', 'true');
    ol.scrollTo({ left: a.offsetLeft - ol.clientWidth / 2 + a.offsetWidth / 2, behavior: RM ? 'auto' : 'smooth' });
    markRead(id);
    if (STAGE_MODS.has(id) && id !== 's5') mountStage(id, true);
  }), { rootMargin: '-45% 0px -50% 0px' });
  ORDER.forEach((id) => io.observe(SH[id].el));
}

// ---------- 相机画布（桌面 ≥1280） ----------
const W = 5380, H = 3180;
const PHOTO = { w: 1536, h: 1024, fx: 1060, fy: 430, span: 900, tilt: 4.5 }; // 照片里图纸的中心、宽度（图像像素）与顺时针倾角
const world = $('world'), photo = $('photo'), heroText = $('heroText');
const bandTb = $('bandTb'), minimap = $('minimap');
let vw, vh, ovS, geo, tbFrom, tbTo, ST = [], A1, B1, END;
const cam = { x: W / 2, y: H / 2, s: 0.268, r: 0 };
let goal = { ...cam, key: 'ov1', dwg: 1 };
let cur = 'ov1', dwgNow = 1, flipR = 0, tw = null, busy = false, hold = false, ovr = null, ovrY = 0;

const TOP = 80, BOT = 70;                 // 阅读图幅停靠：图幅顶边距视口 80 px，读到底边下 70 px
const G0 = () => 0.35 * vh, G1 = () => 0.15 * vh;
function bodyLen(sh) {
  if (sh.id === 's0') return 0.3 * vh;  // 图例 00 按 scale 0.6 停靠，整幅可见，不再纵向读
  if (!sh.stage) return Math.max(0, sh.h + TOP + BOT - vh);
  if (sh.id === 's2') return 2 * vh;     // pin 2 屏，5 步
  if (sh.id === 's5') return 1.0 * vh;   // 5 格依次落定
  if (sh.id === 's8') return 0.6 * vh;   // 到达渗印 1 次，然后读条文
  return 0.5 * vh;                       // s11 总校审栏
}
function dock(key) {
  if (key === 'ov1' || key === 'ov2') return { x: W / 2, y: H / 2, s: ovS, r: 0 };
  const sh = SH[key];
  if (sh.stage) return { x: sh.x + sh.w / 2, y: sh.y + sh.h / 2, s: 0.6, r: 0 };
  // 00 图例：scale 0.6，视口左缘露出图幅 02 右缘，上缘露出轴号行
  if (key === 's0') return { x: sh.x + sh.w / 2 - 150, y: sh.y + sh.h / 2 - 75, s: 0.6, r: 0 };
  return { x: sh.x + sh.w / 2, y: sh.y - TOP + vh / 2, s: 1, r: 0 };
}
const dwgOf = (key) => (key === 'ov1' ? 1 : key === 'ov2' ? 2 : SH[key].dwg);

function measure() {
  vw = innerWidth; vh = innerHeight;
  ovS = Math.min(vw / W, vh / H);
  A1 = 0.6 * vh; B1 = A1 + 0.5 * vh;
  let y = B1; ST = [];
  ORDER.forEach((id) => { const sh = SH[id], len = G0() + bodyLen(sh) + G1(); ST.push({ id, start: y, len, body: bodyLen(sh) }); y += len; });
  ST.push({ id: 'ov2', start: y, len: 0.9 * vh, body: 0 }); END = y + 0.9 * vh;
  root.style.setProperty('--track-h', END + vh + 'px');
  // 照片 object-fit: cover，object-position 78% 50%
  const c = Math.max(vw / PHOTO.w, vh / PHOTO.h);
  const ox = (vw - PHOTO.w * c) * 0.78, oy = (vh - PHOTO.h * c) * 0.5;
  geo = { fx: ox + PHOTO.fx * c, fy: oy + PHOTO.fy * c, m0: (PHOTO.span * c) / (W * ovS) };
  photo.style.transformOrigin = `${geo.fx}px ${geo.fy}px`;
  // 首屏图签 → 图纸 1 总图签带里的图签（FLIP，用布局位置，不受推近影响）
  tbFrom = { x: heroTb.offsetLeft, y: heroTb.offsetTop, w: heroTb.offsetWidth };
  const band = bandTb.parentElement;
  const bx = band.offsetLeft + bandTb.offsetLeft, by = band.offsetTop + bandTb.offsetTop, bw = bandTb.offsetWidth;
  const tx = vw / 2 - (W / 2) * ovS, ty = vh / 2 - (H / 2) * ovS;
  tbTo = { x: tx + bx * ovS, y: ty + by * ovS, k: (bw * ovS) / tbFrom.w };
  // 换图的翻页轴：总览下图纸的左边
  world.style.setProperty('--fold', `${tx}px`);
  world.style.setProperty('--ovx', `${tx}px`); world.style.setProperty('--ovy', `${ty}px`);
  world.style.setProperty('--ovw', `${W * ovS}px`); world.style.setProperty('--ovh', `${H * ovS}px`);
}

function apply() {
  const s = cam.s, tx = vw / 2 - cam.x * s, ty = vh / 2 - cam.y * s;
  const tc = `translate3d(${tx}px, ${ty - cam.r * s}px, 0) scale(${s})`;
  const tp = `translate3d(${tx}px, ${ty - cam.r * 0.88 * s}px, 0) scale(${s})`; // 轴网与纸底 0.88 倍滚速
  DW.forEach((d) => { d.content.style.transform = tc; d.paper.style.transform = tp; });
  world.style.setProperty('--lw', Math.max(1, 0.75 / s).toFixed(3));
  world.style.setProperty('--bub', Math.max(1, 0.7 / s).toFixed(3));
  world.style.setProperty('--ov', smooth(0.55, 0.36, s).toFixed(3));
  root.classList.toggle('is-far', s < 0.5);
  const v = minimap.querySelector('.mm-map.on .m-view');
  if (v) { v.setAttribute('x', cam.x - vw / 2 / s); v.setAttribute('y', cam.y - vh / 2 / s + cam.r); v.setAttribute('width', vw / s); v.setAttribute('height', vh / s); }
}

// 翻页状态：r = 0 图纸 1 在上，r = 1 图纸 1 已翻走，图纸 2 在上
function setFlip(r) {
  flipR = r;
  const [d1, d2] = DW;
  d1.el.style.transform = r > 0 && r < 1 ? `rotateY(${-96 * ease2(r)}deg)` : '';
  d1.el.style.setProperty('--shade', (0.28 * Math.sin(Math.PI * Math.min(1, r * 1.1))).toFixed(3));
  d1.el.style.visibility = r >= 1 ? 'hidden' : 'visible';
  d2.el.style.visibility = r <= 0 ? 'hidden' : 'visible';
  root.classList.toggle('flipping', r > 0 && r < 1);
}
function setDwg(d) {
  dwgNow = d;
  $$('.tabs [role=tab]').forEach((b) => b.setAttribute('aria-selected', String(+b.dataset.dwg === d)));
  $$('.mm-map').forEach((m) => m.classList.toggle('on', +m.dataset.dwg === d));
}

// 相机插值：缩放按对数，平移按 1/s 加权（推近时目标稳定滑向中心）；换排时中途拉远到 0.55
function lerpCam(a, d, t) {
  const la = Math.log(a.s), ld = Math.log(d.s), lo = Math.min(a.s, d.s);
  const far = Math.hypot(d.x - a.x, d.y + d.r - a.y - a.r) * lo > vw * 0.9;
  const dip = far && lo > 0.55 ? Math.log(0.55 / lo) * Math.sin(Math.PI * t) : 0;
  const s = Math.exp(la + (ld - la) * t + dip);
  const ia = 1 / a.s, ib = 1 / d.s;
  const w = dip || Math.abs(ib - ia) < 1e-6 ? t : clamp((1 / Math.exp(la + (ld - la) * t) - ia) / (ib - ia));
  return { x: a.x + (d.x - a.x) * w, y: a.y + (d.y - a.y) * w, s, r: a.r + (d.r - a.r) * t };
}
function flyDur(a, d) {
  const ratio = Math.max(d.s, a.s) / Math.min(d.s, a.s), dist = Math.hypot(d.x - a.x, d.y - a.y) * Math.min(a.s, d.s);
  return Math.min(1.2, ratio > 2 ? 1.0 : dist > vw * 0.9 ? 0.9 : 0.7);
}

function cut() { root.classList.remove('cut'); void world.offsetWidth; root.classList.add('cut'); }

function go(key) {
  const prev = cur; cur = key;
  ORDER.forEach((id) => SH[id].el.classList.toggle('is-here', id === key));
  $$('.mm-map .m-f[data-s]').forEach((r) => r.classList.toggle('cur', r.dataset.s === key));
  if (SH[key]) { mountStage(key); unmountFar(key); } else ovStages(dwgOf(key));
  tw?.kill(); busy = false;
  const tdwg = dwgOf(key);
  if (RM) { if (tdwg !== dwgNow) { setFlip(tdwg === 2 ? 1 : 0); setDwg(tdwg); } Object.assign(cam, goal); apply(); cut(); return; }
  if (tdwg !== dwgNow) return flip(tdwg);
  const a = { ...cam }; busy = true; root.classList.add('moving');
  tw = tween(flyDur(a, goal), (t) => { Object.assign(cam, lerpCam(a, goal, easeIO(t))); apply(); },
    () => { busy = false; root.classList.remove('moving'); update(); });
  void prev;
}

// P11 换图：拉远到总览（0.42 s）→ 图纸 1 向左翻走或翻回（0.36 s）→ 推近到目标（0.42 s），共 1.2 s
function flipFrame(p, a, tdwg) {
  const ov = dock('ov1');
  if (p < 0.35) { Object.assign(cam, lerpCam(a, ov, easeIO(p / 0.35))); setFlip(tdwg === 2 ? 0 : 1); }
  else if (p < 0.65) { Object.assign(cam, ov); const q = (p - 0.35) / 0.3; setFlip(tdwg === 2 ? q : 1 - q); }
  else { setFlip(tdwg === 2 ? 1 : 0); if (dwgNow !== tdwg) setDwg(tdwg); Object.assign(cam, lerpCam(ov, goal, easeIO((p - 0.65) / 0.35))); }
  apply();
}
function flip(tdwg) {
  const a = { ...cam }; busy = true; root.classList.add('moving');
  tw = tween(1.2, (t) => flipFrame(t, a, tdwg), () => { busy = false; root.classList.remove('moving'); setDwg(tdwg); update(); });
  flipA = a; flipT = tdwg;
}
let flipA = null, flipT = 2;

function seam(y) {
  // 幕 0b：照片与图签一起旋正再淡出，矢量图纸与照片同一几何同步推进，淡入到总览
  let q = clamp(y / A1); if (RM) q = q > 0.5 ? 1 : 0;
  const e = easeIO(q), { fx, fy, m0 } = geo, cx = vw / 2, cy = vh / 2, th = PHOTO.tilt;
  const m = m0 + (1 - m0) * e;
  photo.style.transform = `translate(${(cx - fx) * e}px, ${(cy - fy) * e}px) rotate(${-th * e}deg) scale(${m / m0})`;
  photo.style.opacity = 1 - smooth(0.42, 0.82, q);
  world.style.transform = q >= 1 ? '' : `translate(${(fx - cx) * (1 - e)}px, ${(fy - cy) * (1 - e)}px) rotate(${th * (1 - e)}deg) scale(${m})`;
  world.style.opacity = smooth(0.3, 0.72, q);
  heroText.style.opacity = 1 - smooth(0, 0.32, q);
  heroText.style.transform = `translateY(${-48 * e}px)`;
  hero.querySelector('.hero-cap').style.opacity = 1 - smooth(0, 0.2, q);
  const k = 1 + (tbTo.k - 1) * e;
  heroTb.style.transform = `translate(${(tbTo.x - tbFrom.x) * e}px, ${(tbTo.y - tbFrom.y) * e}px) scale(${k}) rotate(${th * (1 - e)}deg)`;
  heroTb.style.opacity = 1 - smooth(0.78, 0.96, q);
  hero.style.visibility = q >= 1 ? 'hidden' : 'visible';
  root.classList.toggle('is-ov', q >= 0.95);
  root.classList.toggle('seaming', q > 0 && q < 1);
  return q;
}

function station(y) {
  if (y < B1) return { id: 'ov1', u: 0, body: 0 };
  for (const s of ST) if (y < s.start + s.len) return { id: s.id, u: y - s.start, body: s.body };
  const s = ST[ST.length - 1]; return { id: s.id, u: s.len, body: 0 };
}

function update() {
  raf = 0;
  if (hold) return;
  const y = scrollY;
  if (y > 2) { setPush(false); clearTimeout(unpushT); }
  seam(y);
  const st = station(y);
  let key = st.id, r = 0;
  if (ovr && Math.abs(y - ovrY) < 2) key = ovr; else ovr = null;
  const sh = SH[key];
  if (sh) {
    const p = st.body ? clamp((st.u - G0()) / st.body) : st.u >= G0() ? 1 : 0;
    if (!sh.stage && sh.id !== 's0') r = clamp(st.u - G0(), 0, st.body);
    if (sh.id === 's1') SH.s1.el.querySelector('.chart svg')?.style.setProperty('--draw', RM ? 1 : clamp((st.u - 0.08 * vh) / (0.37 * vh)).toFixed(3));
    if (sh.id === 's2') drive('s2', p);
    if (sh.id === 's5') drive('s5', Math.min(5, Math.floor(p * 6)));
    if (sh.id === 's8' && !busy) drive('s8', p > 0 || st.u > 0 ? 1 : 0);
    if (p >= 0.9 && (sh.stage || st.body > 0 || st.u > G0())) markRead(key);
  }
  goal = { ...dock(key), r, key };
  if (key !== cur) go(key);
  else if (!busy) { Object.assign(cam, goal); apply(); }
}
let raf = 0;
const onScroll = () => { if (!raf) raf = requestAnimationFrame(update); };

function goTo(key) {
  ovr = null;
  const s = ST.find((t) => t.id === key);
  const y = key === 'ov1' ? A1 + 0.2 * vh : s ? s.start + G0() + 1 : 0;
  scrollTo({ top: Math.ceil(y), behavior: 'instant' });
}
function toOverview() {
  const k = 'ov' + dwgNow;
  if (k === 'ov1') return goTo('ov1');
  ovr = k; ovrY = scrollY; update();
}

function buildMinimap() {
  [1, 2].forEach((d) => {
    const box = minimap.querySelector(`.mm-map[data-dwg="${d}"]`);
    const list = ORDER.map((id) => SH[id]).filter((s) => s.dwg === d);
    box.innerHTML = `<svg viewBox="0 0 5380 3180" aria-hidden="true"><rect class="m-border" x="14" y="14" width="5352" height="3152"/>`
      + list.map((s) => `<rect class="m-f" data-s="${s.id}" x="${s.x}" y="${s.y}" width="${s.w}" height="${s.h}"/>`
        + `<path class="m-tick" data-s="${s.id}" d="M${s.x + s.w - 300} ${s.y + 300} l70 80 l130 -190"/>`).join('')
      + `<rect class="m-band" x="5040" y="14" width="326" height="3152"/><rect class="m-view" x="0" y="0" width="1440" height="900"/></svg>`
      + list.map((s) => `<button class="mm-hit" data-go="${s.id}" type="button" aria-label="转到图幅 ${s.no} ${s.name}" style="--x:${s.x};--y:${s.y};--w:${s.w};--h:${s.h}"><span>${s.no} ${s.name}</span></button>`).join('');
  });
  $$('.mm-hit').forEach((b) => b.addEventListener('click', () => goTo(b.dataset.go)));
  $$('.tabs [role=tab]').forEach((b) => b.addEventListener('click', () => goTo(+b.dataset.dwg === 2 ? 's6' : 's1')));
}

if (CAM) {
  buildMinimap(); setFlip(0); setDwg(1);
  measure(); Object.assign(cam, dock('ov1')); goal = { ...cam, key: 'ov1' }; apply(); update(); ovStages(1);
  addEventListener('scroll', onScroll, { passive: true });
  addEventListener('resize', () => { measure(); update(); });
  document.fonts?.ready.then(() => { measure(); update(); });
  $('toOv').addEventListener('click', toOverview);
  addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !anyDetailOpen() && scrollY > A1) { e.preventDefault(); toOverview(); }
    if ((e.key === 'PageDown' || e.key === 'PageUp') && !e.altKey) {
      const i = SH[cur]?.i ?? -1, j = e.key === 'PageDown' ? i + 1 : i - 1;
      e.preventDefault();
      if (j < 0) goTo('ov1'); else if (j < ORDER.length) goTo(ORDER[j]); else goTo('ov2');
    }
  });
  // 屏幕阅读器与键盘：焦点进入图幅时把相机移过去
  ORDER.forEach((id) => SH[id].el.addEventListener('focusin', () => { if (cur !== id) goTo(id); }));
}

// 检查钩子（截图与验收用）：暂停换图在任意进度，读相机状态
window.__e1 = {
  cam, st: () => ({ cur, dwgNow, flipR, busy, read: [...read], tween: root.dataset.tween || 'pending', stations: ST.map((s) => [s.id, Math.round(s.start)]) }),
  goTo, flipAt(p, tdwg = 2) { tw?.kill(); hold = true; flipFrame(p, flipA || dock('s5'), tdwg); },
  release() { hold = false; update(); },
};

// 动效引擎：mixed 档，GSAP 3.15.0 + ScrollTrigger，Lenis 关闭（相机自己管滚动映射）
boot({ gear: 'mixed', lenis: false }).then(() => {
  if (window.gsap && !gsap) { gsap = window.gsap; gsap.ticker.lagSmoothing(0); root.dataset.tween = 'gsap'; }
  root.dataset.ready = '1';
  if (CAM) update();
});
