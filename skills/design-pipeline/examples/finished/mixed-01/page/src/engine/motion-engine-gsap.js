/*!
 * motion-engine-gsap.js  GSAP + ScrollTrigger + Lenis 适配器（mixed / show 档的默认引擎）
 *
 * 数据属性 API、boot({ gear, setup }) 入口、html.motion 门控与减少动效行为，
 * 与 motion-engine.js 完全相同。本文件只把 reveal / split / scrub / parallax 的实现
 * 换成 GSAP + ScrollTrigger，并可选加 Lenis 平滑滚动。其余（进度条、目录、章节、计数、
 * 磁吸、加载器、driver）直接复用 motion-engine.js。
 *
 * 依赖从 CDN 加载，版本精确固定，带 SRI。本 skill 不分发这些库（GSAP 许可见
 * references/sources-and-credits.md）。
 *
 * 用法：
 *   <script type="module">
 *     import { boot } from './engine/motion-engine-gsap.js';
 *     boot({ gear: 'mixed', lenis: true });   // lenis 可省：mixed 默认 false，show 默认 true
 *   </script>
 *
 * 新增的可选属性：
 *   data-pin="120"   把元素固定在视口内，持续 120% 视口高度（mixed 档只认第一个）。同时写 --p。
 *
 * 安全回退（任一条成立就改用 motion-engine.js 的零依赖实现，内容照常可见）：
 *   - gear 为 clear（clear 档不使用 GSAP）
 *   - 用户要求减少动效（不请求 CDN，不加 html.motion）
 *   - CDN 在 CDN_TIMEOUT 毫秒内没加载完
 * 回退时 <html data-engine="fallback">；成功时 data-engine="gsap"。
 */
import * as base from './motion-engine.js';
import { boot as baseBoot, prefersReducedMotion, splitEl, GEARS } from './motion-engine.js';

export * from './motion-engine.js';

// ---------- 固定的 CDN 版本（升级前先查 npm 发布日期，≥14 天） ----------
export const CDN = {
  gsap: {
    url: 'https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js',
    sri: 'sha384-XmJ9SoHtVOHoQUcKvFAzVXwdkKo1Ie3bhmSoIAkcdsHGaIrVJIkmozyq0FJeb/Ly',
  },
  scrollTrigger: {
    url: 'https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/ScrollTrigger.min.js',
    sri: 'sha384-wl5TeDVvOWt30Pbf8aSo2ZrzsOjddu3avOBvHe+p+OhJt9gP6w9YXmDkN5DK2/dF',
  },
  lenis: {
    url: 'https://cdn.jsdelivr.net/npm/lenis@1.3.26/dist/lenis.min.js',
    sri: 'sha384-jqpi9VmOdhyLoLURgjCn7EpnG9BbnHW57ibIZoeaIU+erWDH3k8fQQg0xH2ySjnw',
  },
};
// 小于 engine.css 的 2.5 秒保险，这样回退时内容不会先闪出再被动画重置。
export const CDN_TIMEOUT = 2200;

function loadScript({ url, sri }) {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = url; s.async = true; s.crossOrigin = 'anonymous';
    if (sri) s.integrity = sri;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error('load failed: ' + url));
    document.head.appendChild(s);
  });
}

/** 在限时内加载库。成功返回 { gsap, ScrollTrigger, Lenis }，失败或超时返回 null。 */
async function loadLibs(wantLenis, timeout) {
  const work = (async () => {
    // GSAP 先于 ScrollTrigger；Lenis 与它们并行
    const core = loadScript(CDN.gsap).then(() => loadScript(CDN.scrollTrigger));
    const lenis = wantLenis ? loadScript(CDN.lenis).catch(() => null) : Promise.resolve();
    await Promise.all([core, lenis]);
    if (!window.gsap || !window.ScrollTrigger) throw new Error('gsap missing');
    return { gsap: window.gsap, ScrollTrigger: window.ScrollTrigger, Lenis: wantLenis ? window.Lenis || null : null };
  })();
  const timer = new Promise((r) => setTimeout(() => r(null), timeout));
  try { return await Promise.race([work, timer]); } catch (_) { return null; }
}

// ---------- GSAP 版入场 ----------
const q = (sel, root = document) => [...root.querySelectorAll(sel)];
const KILLERS = [];

function revealFrom(kind) {
  if (kind === 'fade') return { opacity: 0 };
  if (kind === 'clip') return { clipPath: 'inset(100% 0 0 0)' };
  if (kind === 'scale') return { clipPath: 'inset(12%)', scale: 1.12 };
  return { opacity: 0, y: 32 };
}
const revealTo = (kind) => (kind === 'clip' ? { clipPath: 'inset(0% 0% 0% 0%)' }
  : kind === 'scale' ? { clipPath: 'inset(0%)', scale: 1 } : kind === 'fade' ? { opacity: 1 } : { opacity: 1, y: 0 });

/** 先把全部入场元素放到起始状态。起始状态由 GSAP 内联写入，所以 2.5 秒保险动画不会让它们露出来。 */
function prepareReveals(gsap, g) {
  const items = [];
  q('[data-split]').forEach((el) => {
    if (!g.split) { el.style.visibility = 'visible'; return; }
    const type = el.dataset.split || 'lines';
    const targets = splitEl(el, type);
    gsap.set(targets, { display: 'inline-block', yPercent: 110 });
    el.style.visibility = 'visible';
    items.push({ el, targets, type, split: true });
  });
  q('[data-reveal]').forEach((el) => {
    const kind = el.dataset.reveal || 'up';
    gsap.set(el, { ...revealFrom(kind), visibility: 'visible' });
    items.push({ el, kind, split: false });
  });
  return items;
}

function playItem(gsap, it, g) {
  const delay = parseFloat(it.el.dataset.delay || '0');
  if (it.split) {
    const per = it.type === 'lines' ? g.stagger : it.type === 'words' ? g.stagger * 0.5 : g.stagger * 0.25;
    const dur = (it.type === 'lines' ? g.reveal[1] : g.reveal[0] + 200) / 1000;
    gsap.to(it.targets, { yPercent: 0, duration: dur, delay, ease: 'expo.out', stagger: per / 1000 });
  } else {
    const dur = (it.kind === 'fade' ? g.reveal[0] : g.reveal[1]) / 1000;
    gsap.to(it.el, {
      ...revealTo(it.kind), duration: dur, delay, ease: 'expo.out',
      onComplete: () => gsap.set(it.el, { clearProps: 'opacity,transform,clipPath' }),
    });
  }
}

function wireScroll(gsap, ST, items, g, intro) {
  items.forEach((it) => {
    if (it.el.hasAttribute('data-intro')) { intro.push(() => playItem(gsap, it, g)); return; }
    KILLERS.push(ST.create({ trigger: it.el, start: 'top 90%', once: true, onEnter: () => playItem(gsap, it, g) }));
  });
}

function wireScrub(ST) {
  q('[data-scrub]').forEach((el) => {
    const write = (p) => el.style.setProperty('--p', p.toFixed(4));
    KILLERS.push(ST.create({
      trigger: el, start: 'top bottom', end: 'bottom 40%', // 与 motion-engine.js 的 scrub 区间一致
      onUpdate: (self) => write(self.progress), onRefresh: (self) => write(self.progress),
    }));
  });
}

function wirePin(ST, gear) {
  const pins = q('[data-pin]');
  if (gear === 'mixed' && pins.length > 1) console.warn('[engine] mixed 档最多固定 1 个舞台，其余忽略。');
  (gear === 'mixed' ? pins.slice(0, 1) : pins).forEach((el) => {
    const len = parseFloat(el.dataset.pin || '100');
    KILLERS.push(ST.create({
      trigger: el, start: 'top top', end: `+=${len}%`, pin: true, pinSpacing: true,
      onUpdate: (self) => el.style.setProperty('--p', self.progress.toFixed(4)),
      onRefresh: (self) => el.style.setProperty('--p', self.progress.toFixed(4)),
    }));
  });
}

function wireParallax(gsap, ST, cap) {
  q('[data-parallax]').forEach((el) => {
    const amt = Math.min(cap, parseFloat(el.dataset.parallax || String(cap))) * 100;
    const tw = gsap.fromTo(el, { yPercent: amt }, {
      yPercent: -amt, ease: 'none',
      scrollTrigger: { trigger: el, start: 'top bottom', end: 'bottom top', scrub: true },
    });
    KILLERS.push(tw.scrollTrigger, tw);
  });
}

function wireLenis(gsap, ST, Lenis) {
  const lenis = new Lenis({ lerp: 0.1, smoothWheel: true, anchors: true, autoRaf: false });
  lenis.on('scroll', ST.update);
  const tick = (t) => lenis.raf(t * 1000);
  gsap.ticker.add(tick);
  gsap.ticker.lagSmoothing(0);
  KILLERS.push({ kill() { gsap.ticker.remove(tick); lenis.destroy(); } });
  return lenis;
}

// ---------- 入口 ----------
let started = false;
/**
 * boot({ gear, setup, lenis })：与 motion-engine.js 的 boot 相同，外加 lenis 选项。
 * lenis 缺省：show 为 true，mixed 为 false，clear 不适用。
 */
export async function boot({ gear = 'mixed', setup, lenis } = {}) {
  if (started) return; started = true;
  const root = document.documentElement;
  const useGsap = gear !== 'clear' && !prefersReducedMotion();
  if (!useGsap) { root.dataset.engine = 'fallback'; return baseBoot({ gear, setup }); }

  const wantLenis = lenis ?? gear === 'show';
  const libs = await loadLibs(wantLenis, CDN_TIMEOUT);
  if (!libs) {
    console.warn('[engine] CDN 未在 ' + CDN_TIMEOUT + 'ms 内加载，改用零依赖引擎。');
    root.dataset.engine = 'fallback';
    return baseBoot({ gear, setup });
  }
  const { gsap, ScrollTrigger: ST, Lenis } = libs;
  gsap.registerPlugin(ST);
  root.dataset.engine = 'gsap';
  const g = GEARS[gear] || GEARS.mixed;

  // 字体就绪后再拆字，行的分组才准（最多等 1.5 秒）
  if (document.fonts?.ready) await Promise.race([document.fonts.ready, new Promise((r) => setTimeout(r, 1500))]);

  const items = prepareReveals(gsap, g);
  // 复用零依赖引擎的进度条、目录、章节、计数、磁吸、加载器；接管 reveals / scrub / parallax。
  await baseBoot({ gear, setup, skip: ['reveals', 'scrub', 'parallax'] });

  const intro = [];
  wireScroll(gsap, ST, items, g, intro);
  wireScrub(ST);
  wirePin(ST, gear);
  if (g.parallax) wireParallax(gsap, ST, g.parallax);
  if (wantLenis && Lenis) wireLenis(gsap, ST, Lenis);
  intro.forEach((p) => p());
  // 版面在字体与图片到位后可能变化，刷新一次触发点
  addEventListener('load', () => ST.refresh(), { once: true });
}

/** 撤销 GSAP 的触发器、Lenis 与零依赖引擎的全部监听。 */
export function cleanup() {
  KILLERS.splice(0).forEach((k) => { try { k.kill(); } catch (_) { /* 忽略 */ } });
  base.cleanup();
  started = false;
}
