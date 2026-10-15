/*!
 * motion-engine.js  视觉与动效 skill 的最小动效引擎（零依赖，ES module，可离线打开）
 *
 * 派生自 juliobsz/skills (awwwards) 的 motion engine。保留其数据属性 API、head 标志、
 * 加载器真实进度与上下限、减少动效门控、单时钟原则。原实现依赖 GSAP + Lenis，
 * 此处用 Web Animations API、IntersectionObserver 与一个 requestAnimationFrame 时钟重写。
 * Copyright (c) 2026 Julio (juliobsz), MIT License. 重写部分 (c) 2026 本仓库作者, MIT License.
 * 完整声明见同目录 LICENSE-MIT.txt。
 *
 * 用法（页面 <head> 内先放 head-flag.html 的内联脚本，再在 body 末尾）：
 *   <script type="module">
 *     import { boot } from './motion-engine.js';
 *     boot({ gear: 'clear' | 'mixed' | 'show' });
 *   </script>
 *
 * 数据属性：
 *   data-reveal="up|fade|clip|scale"   区块入场（滚动到 90% 视口时播放一次）
 *   data-split="lines|words|chars"     文字遮罩逐行/逐词/逐字入场（中文按字切分）
 *   data-intro                         随页面开场播放，不等滚动（hero 用）
 *   data-delay="0.2"                   额外延迟，秒
 *   data-parallax="0.1"                滚动漂移，元素高度的比例（mixed 档上限 0.08，show 档 0.15）
 *   data-magnetic="0.35"               元素向指针微移（仅 show 档，仅精细指针）
 *   data-counter="214" data-decimals="1" data-suffix="%"   真实数字计数一次
 *   data-progress                      阅读进度条（scaleX 0..1）
 *   data-toc                           目录容器，内部 a[href^="#"] 随当前章节加 aria-current
 *   data-scrub                         元素从视口底部进入到其底边升至视口 40% 高度时，写入 CSS 变量 --p（0..1）；减少动效时 --p=1
 *   data-chapter / data-stage          章节进入视口中线时，舞台元素得到 data-state="序号"
 *
 * 减少动效（prefers-reduced-motion: reduce）：不加 html.motion，内容全部可见；
 *   入场、拆字、漂移、磁吸、计数动画全部跳过；进度条、目录高亮、章节状态仍工作（它们是状态，不是装饰）。
 */

// ---------- 环境与缓动 ----------
export const prefersReducedMotion = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
export const isTouch = () => matchMedia('(hover: none), (pointer: coarse)').matches;
export const isMobile = () => matchMedia('(max-width: 767px)').matches;

// 四个缓动名字是契约。值近似 GSAP 的 expo.out / expo.inOut / power3.out / back.out(1.6)。
export const ease = {
  out: 'cubic-bezier(0.16, 1, 0.3, 1)',
  inOut: 'cubic-bezier(0.87, 0, 0.13, 1)',
  soft: 'cubic-bezier(0.33, 1, 0.68, 1)',
  spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)', // 只给反馈类小物件，结构类不用
};

// ---------- 档位预算（与 references/gears.md 一致；改预算先改文档） ----------
export const GEARS = {
  clear: { loader: false, split: false, parallax: 0, magnetic: false, idle: false, reveal: [400, 700], stagger: 60 },
  mixed: { loader: 'short', split: true, parallax: 0.08, magnetic: false, idle: 'signature', reveal: [500, 900], stagger: 70 },
  show: { loader: true, split: true, parallax: 0.15, magnetic: true, idle: true, reveal: [700, 1300], stagger: 80 },
};

// ---------- 一个时钟 ----------
const tick = { fns: new Set(), raf: 0, last: 0 };
function loop(now) {
  const t = now / 1000;
  const dt = tick.last ? Math.min(0.1, t - tick.last) : 0;
  tick.last = t;
  tick.fns.forEach((fn) => fn(t, dt));
  tick.raf = tick.fns.size ? requestAnimationFrame(loop) : 0;
}
function startTick() { if (!tick.raf && !document.hidden) tick.raf = requestAnimationFrame(loop); }
/** 注册每帧回调 fn(t 秒, dt 秒)。返回注销函数。页签隐藏时时钟暂停。 */
export function onTick(fn) { tick.fns.add(fn); startTick(); return () => { tick.fns.delete(fn); }; }
document.addEventListener('visibilitychange', () => {
  if (document.hidden) { cancelAnimationFrame(tick.raf); tick.raf = 0; tick.last = 0; } else startTick();
});

// ---------- 滚动馈送（在时钟里读 scrollY，不自己挂 scroll 监听） ----------
const scroll = { y: 0, velocity: 0, progress: 0 };
const scrollFns = new Set();
let scrollOff = null;
function scrollTick() {
  const max = document.documentElement.scrollHeight - innerHeight;
  const y = scrollY;
  scroll.velocity = y - scroll.y;
  scroll.y = y;
  scroll.progress = max > 0 ? Math.min(1, Math.max(0, y / max)) : 0;
  scrollFns.forEach((fn) => fn(scroll));
}
/** 订阅滚动状态 {y, velocity, progress}。返回注销函数。 */
export function onScroll(fn) {
  scrollFns.add(fn);
  if (!scrollOff) scrollOff = onTick(scrollTick);
  fn(scroll);
  return () => { scrollFns.delete(fn); if (!scrollFns.size && scrollOff) { scrollOff(); scrollOff = null; } };
}
export const scrollState = () => scroll;
/** 滚到目标。减少动效时瞬时到达。 */
export function scrollToTarget(target) {
  const el = typeof target === 'string' ? document.querySelector(target) : target;
  if (!el) return;
  el.scrollIntoView({ behavior: prefersReducedMotion() ? 'auto' : 'smooth', block: 'start' });
}

// ---------- 标志 ----------
export function syncFlags() {
  const h = document.documentElement.classList;
  h.add('js', 'is-booted');
  h.toggle('motion', !prefersReducedMotion());
}

// ---------- 入场：区块 ----------
const registry = []; // 可清理的观察器与动画
const once = (el, cb, margin = '0px 0px -10% 0px') => {
  const io = new IntersectionObserver((es) => {
    es.forEach((e) => { if (e.isIntersecting) { io.unobserve(e.target); cb(); } });
  }, { rootMargin: margin, threshold: 0.05 });
  io.observe(el);
  registry.push(() => io.disconnect());
};
function blockReveal(el, gear) {
  const kind = el.dataset.reveal || 'up';
  const delay = parseFloat(el.dataset.delay || '0') * 1000;
  const [dMin, dMax] = gear.reveal;
  const duration = kind === 'fade' ? dMin : dMax;
  const frames = kind === 'fade' ? [{ opacity: 0 }, { opacity: 1 }]
    : kind === 'clip' ? [{ clipPath: 'inset(100% 0 0 0)' }, { clipPath: 'inset(0 0 0 0)' }]
    : kind === 'scale' ? [{ clipPath: 'inset(12%)', transform: 'scale(1.12)' }, { clipPath: 'inset(0)', transform: 'none' }]
    : [{ opacity: 0, transform: 'translateY(32px)' }, { opacity: 1, transform: 'none' }];
  let played = false;
  const play = () => {
    if (played) return; played = true;
    el.style.visibility = 'visible';
    const a = el.animate(frames, { duration, delay, easing: ease.out, fill: 'both' });
    registry.push(() => a.cancel());
  };
  return play;
}

// ---------- 入场：拆字（中文按字，拉丁按词；lines 按实际换行分组） ----------
const CJK = /[⺀-鿿豈-﫿＀-￯]/;
function tokenize(text, type) {
  const out = [];
  let latin = '';
  const flush = () => { if (latin) { out.push(latin); latin = ''; } };
  for (const ch of text) {
    if (CJK.test(ch)) { flush(); out.push(ch); }
    else if (/\s/.test(ch)) { flush(); out.push(' '); }
    else if (type === 'chars') { flush(); out.push(ch); }
    else latin += ch;
  }
  flush();
  return out;
}
export function splitEl(el, type) {
  const text = el.textContent;
  el.setAttribute('aria-label', text.trim());
  el.textContent = '';
  const units = tokenize(text, type === 'lines' ? 'words' : type).map((u) => {
    if (u === ' ') return document.createTextNode(' ');
    const s = document.createElement('span');
    s.className = 'split-unit'; s.textContent = u; s.setAttribute('aria-hidden', 'true');
    return s;
  });
  units.forEach((n) => el.appendChild(n));
  if (type !== 'lines') return [...el.querySelectorAll('.split-unit')];
  // 按 offsetTop 分行，每行套一个遮罩
  const spans = [...el.querySelectorAll('.split-unit')];
  // 记下原文里哪些单元前有空格。汉字之间不补空格。
  spans.forEach((s) => { s._sp = s.previousSibling && s.previousSibling.nodeType === 3; });
  const lines = []; let top = null; let cur = null;
  spans.forEach((s) => {
    if (s.offsetTop !== top) { top = s.offsetTop; cur = []; lines.push(cur); }
    cur.push(s);
  });
  el.textContent = '';
  return lines.map((ls) => {
    const mask = document.createElement('span'); mask.className = 'split-line';
    const inner = document.createElement('span'); inner.className = 'split-inner'; inner.setAttribute('aria-hidden', 'true');
    ls.forEach((s, i) => { if (i > 0 && s._sp) inner.appendChild(document.createTextNode(' ')); inner.appendChild(s); });
    mask.appendChild(inner); el.appendChild(mask); el.appendChild(document.createTextNode(' '));
    return inner;
  });
}
function splitReveal(el, gear) {
  const type = el.dataset.split || 'lines';
  const delay = parseFloat(el.dataset.delay || '0') * 1000;
  const stagger = type === 'lines' ? gear.stagger : type === 'words' ? gear.stagger * 0.5 : gear.stagger * 0.25;
  const duration = type === 'lines' ? gear.reveal[1] : gear.reveal[0] + 200;
  const targets = splitEl(el, type);
  el.style.visibility = 'visible';
  targets.forEach((t) => { t.style.display = 'inline-block'; t.style.transform = 'translateY(110%)'; });
  let played = false;
  const play = () => {
    if (played) return; played = true;
    targets.forEach((t, i) => {
      const a = t.animate([{ transform: 'translateY(110%)' }, { transform: 'none' }],
        { duration, delay: delay + i * stagger, easing: ease.out, fill: 'both' });
      registry.push(() => a.cancel());
    });
  };
  return play;
}

/** 接线 root 内全部入场。返回 { play } 开场时间线（data-intro 的元素在此播放）。 */
export function initReveals(root = document, gear = GEARS.clear) {
  const introPlays = [];
  if (prefersReducedMotion()) return { play() {} };
  root.querySelectorAll('[data-split]').forEach((el) => {
    if (!gear.split) { el.style.visibility = 'visible'; return; }
    const play = splitReveal(el, gear);
    if (el.hasAttribute('data-intro')) introPlays.push(play); else once(el, play);
  });
  root.querySelectorAll('[data-reveal]').forEach((el) => {
    const play = blockReveal(el, gear);
    if (el.hasAttribute('data-intro')) introPlays.push(play); else once(el, play);
  });
  return { play() { introPlays.forEach((p) => p()); } };
}

// ---------- 漂移、磁吸、计数 ----------
function initParallax(cap) {
  if (prefersReducedMotion()) return;
  const els = [...document.querySelectorAll('[data-parallax]')];
  if (!els.length) return;
  const off = onScroll(() => {
    els.forEach((el) => {
      const amount = Math.min(cap, parseFloat(el.dataset.parallax || String(cap)));
      const r = el.getBoundingClientRect();
      if (r.bottom < 0 || r.top > innerHeight) return;
      const p = (r.top + r.height / 2) / innerHeight - 0.5; // -0.5..0.5
      el.style.transform = `translateY(${(-p * amount * r.height * 2).toFixed(1)}px)`;
    });
  });
  registry.push(off);
}
function initMagnetic() {
  if (isTouch() || prefersReducedMotion()) return;
  document.querySelectorAll('[data-magnetic]').forEach((el) => {
    const k = parseFloat(el.dataset.magnetic || '0.35');
    const move = (e) => {
      const r = el.getBoundingClientRect();
      el.style.translate = `${((e.clientX - r.left - r.width / 2) * k).toFixed(1)}px ${((e.clientY - r.top - r.height / 2) * k).toFixed(1)}px`;
    };
    const leave = () => { el.style.translate = '0px 0px'; };
    el.addEventListener('pointermove', move); el.addEventListener('pointerleave', leave);
    registry.push(() => { el.removeEventListener('pointermove', move); el.removeEventListener('pointerleave', leave); });
  });
}
function initCounters() {
  document.querySelectorAll('[data-counter]').forEach((el) => {
    const end = parseFloat(el.dataset.counter);
    const decimals = parseInt(el.dataset.decimals || '0', 10);
    const suffix = el.dataset.suffix || '';
    const fmt = new Intl.NumberFormat('zh-CN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
    const write = (v) => { el.textContent = fmt.format(v) + suffix; };
    if (prefersReducedMotion()) { write(end); return; }
    write(0);
    once(el, () => {
      const t0 = performance.now(); const D = 1600;
      const off = onTick(() => {
        const p = Math.min(1, (performance.now() - t0) / D);
        write(end * (1 - Math.pow(1 - p, 4)));
        if (p >= 1) off();
      });
    }, '0px 0px -15% 0px');
  });
}

// ---------- 状态类：进度条、目录高亮、章节舞台、scrub ----------
function initProgress() {
  const bars = [...document.querySelectorAll('[data-progress]')];
  if (!bars.length) return;
  registry.push(onScroll(({ progress }) => bars.forEach((b) => { b.style.transform = `scaleX(${progress.toFixed(4)})`; })));
}
function initToc() {
  const toc = document.querySelector('[data-toc]');
  if (!toc) return;
  const links = [...toc.querySelectorAll('a[href^="#"]')];
  const map = new Map(links.map((a) => [a.getAttribute('href').slice(1), a]));
  const sections = [...map.keys()].map((id) => document.getElementById(id)).filter(Boolean);
  if (!sections.length) return;
  const io = new IntersectionObserver((es) => {
    es.forEach((e) => {
      if (!e.isIntersecting) return;
      links.forEach((a) => a.removeAttribute('aria-current'));
      map.get(e.target.id)?.setAttribute('aria-current', 'true');
    });
  }, { rootMargin: '-20% 0px -70% 0px' });
  sections.forEach((s) => io.observe(s));
  registry.push(() => io.disconnect());
}
function initChapters() {
  const stage = document.querySelector('[data-stage]');
  const chapters = [...document.querySelectorAll('[data-chapter]')];
  if (!stage || !chapters.length) return;
  const io = new IntersectionObserver((es) => {
    es.forEach((e) => { if (e.isIntersecting) stage.dataset.state = String(chapters.indexOf(e.target)); });
  }, { rootMargin: '-50% 0px -50% 0px' });
  chapters.forEach((c) => io.observe(c));
  registry.push(() => io.disconnect());
}
function initScrub() {
  const els = [...document.querySelectorAll('[data-scrub]')];
  if (!els.length) return;
  if (prefersReducedMotion()) { els.forEach((el) => el.style.setProperty('--p', '1')); return; }
  registry.push(onScroll(() => {
    els.forEach((el) => {
      const r = el.getBoundingClientRect();
      const p = Math.min(1, Math.max(0, (innerHeight - r.top) / (innerHeight * 0.6 + r.height)));
      el.style.setProperty('--p', p.toFixed(4));
    });
  }));
}

// ---------- 驱动模块（一个变量驱动全部承载概念的视觉） ----------
/**
 * driver(map, apply)：map(progress 0..1) 返回离散状态，apply(state, drift) 把状态写到 DOM。
 * 页面可用 [data-state="0.6"] 钉住某个状态。空闲输入 drift 只在 show 档且允许动效时非零。
 */
export function driver(map, apply, { idle = false } = {}) {
  const pinned = () => { const v = document.querySelector('[data-state-pin]')?.dataset.statePin; return v ? parseFloat(v) : null; };
  let current = 0;
  const offScroll = onScroll(({ progress }) => { current = pinned() ?? progress; apply(map(current), 0); });
  let offIdle = null;
  if (idle && !prefersReducedMotion()) {
    offIdle = onTick((t) => apply(map(current), Math.sin(t * 0.3) * 0.01));
  }
  return () => { offScroll(); offIdle?.(); };
}

// ---------- 加载器（跟随真实进度；下限 1.1 秒，上限 2.6 秒） ----------
let loaderFormat = (p) => String(Math.round(p)).padStart(3, '0');
let loaderExit = null;
/** 自定义计数文字，p 0→100（可以是年份、时间、进度）。 */
export const setLoaderFormat = (fn) => { loaderFormat = fn; };
/** 自定义出场编排：fn(root) 返回 Promise。默认：文字上移 + 底部擦除。 */
export const setLoaderExit = (fn) => { loaderExit = fn; };
const wait = (s) => new Promise((r) => setTimeout(r, s * 1000));
function criticalAssets() {
  const imgs = [...document.querySelectorAll('img[data-critical], [data-intro] img')];
  return [document.fonts.ready, ...imgs.map((i) => (i.complete ? Promise.resolve() : i.decode().catch(() => {})))];
}
export async function runLoader({ min = 1.1, max = 2.6 } = {}) {
  const root = document.getElementById('loader');
  if (!root) return;
  const finish = () => { root.hidden = true; document.documentElement.classList.add('is-loaded'); };
  if (prefersReducedMotion()) {
    await Promise.race([Promise.all(criticalAssets()), wait(max)]);
    await root.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 300, fill: 'forwards' }).finished;
    return finish();
  }
  const count = root.querySelector('[data-loader-count]');
  const bar = root.querySelector('[data-loader-bar]');
  const tasks = criticalAssets();
  let done = 0; let target = 0; let shown = 0;
  tasks.forEach((t) => t.then(() => { done++; target = (done / tasks.length) * 100; }));
  const start = performance.now();
  await new Promise((resolve) => {
    const off = onTick(() => {
      const elapsed = (performance.now() - start) / 1000;
      const timeCap = Math.min(100, (elapsed / min) * 100);
      const goal = elapsed > max ? 100 : Math.min(target, timeCap);
      shown += (goal - shown) * 0.12;
      if (goal === 100 && shown > 99.5) shown = 100;
      if (count) count.textContent = loaderFormat(shown);
      if (bar) bar.style.transform = `scaleX(${shown / 100})`;
      if (shown === 100) { off(); resolve(); }
    });
  });
  if (loaderExit) { await loaderExit(root); return finish(); }
  const outs = [...root.querySelectorAll('[data-loader-out]')];
  await Promise.all(outs.map((el, i) => el.animate([{ transform: 'none' }, { transform: 'translateY(-110%)' }],
    { duration: 700, delay: i * 50, easing: ease.inOut, fill: 'forwards' }).finished));
  await root.animate([{ clipPath: 'inset(0 0 0 0)' }, { clipPath: 'inset(0 0 100% 0)' }],
    { duration: 1000, easing: ease.inOut, fill: 'forwards' }).finished;
  finish();
}

// ---------- 生命周期 ----------
let booted = false;
/**
 * boot({ gear, setup })：一次性启动。gear 为 'clear' | 'mixed' | 'show'。
 * setup 在页面接线前运行一次，用来注册 setLoaderFormat / setLoaderExit / driver。
 * skip：要跳过的模块名数组，可含 'reveals' | 'scrub' | 'parallax'。GSAP 适配器用它接管这三项。
 */
export async function boot({ gear = 'clear', setup, skip = [] } = {}) {
  if (booted) return; booted = true;
  const g = GEARS[gear] || GEARS.clear;
  syncFlags();
  document.documentElement.dataset.gear = gear;
  setup?.();
  initProgress(); initToc(); initChapters();
  if (!skip.includes('scrub')) initScrub();
  const intro = skip.includes('reveals') ? { play() {} } : initReveals(document, g);
  initCounters();
  if (g.parallax && !skip.includes('parallax')) initParallax(g.parallax);
  if (g.magnetic) initMagnetic();
  if (g.loader) await runLoader(g.loader === 'short' ? { min: 0.4, max: 1.2 } : {});
  else document.documentElement.classList.add('is-loaded');
  intro.play();
}
/** 撤销全部观察器、动画与监听（多页应用换页前调用）。 */
export function cleanup() {
  registry.splice(0).forEach((fn) => { try { fn(); } catch (_) { /* 忽略 */ } });
  booted = false;
}
