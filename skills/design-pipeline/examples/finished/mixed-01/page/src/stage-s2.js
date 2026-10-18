/* s2 舞台：四层硫酸纸叠加，第 5 步平面竖起成体块。
 * 契约：mount(sheet, opts) -> { set(t), destroy() }
 *   t 0..1 是 pin 进度，5 步各 0.2。步 1-4 描入 A04-1..4，步 5 竖起体块。
 *   opts = { assets: 资产目录（默认 "../assets/generated/"，相对页面），reduced: bool, webgl: bool }
 * 有 WebGL 且不 reduced：步 5 用 three 0.186.0 正交相机（俯角 90 度到 35 度）。
 * 无 WebGL、reduced、或 three 未就绪：步 5 用 SVG 等轴投影。reduced 只切终态，不做描入。
 * 只画视觉，不写文字。颜色走 CSS 变量 --struct --paper --ink --rule-strong --tex。
 */

const THREE_URL = 'https://cdn.jsdelivr.net/npm/three@0.186.0/build/three.module.js';
const PREFETCH_AT = 0.55;           // t 首次到此值就预取 three，早于 0.8
const STAGE_W = 1400, STAGE_H = 1100;
const PLAN = 1240;                  // A04-4 整图边长（图幅 px）
const CX = STAGE_W / 2, CY = 550;   // 建筑中心在舞台内的位置
const WALL_H = 150;                 // 满高（图幅 px）
const SHEET_W = 1220, SHEET_H = 1040;

/* 各层对齐：b = 建筑外墙包围盒 [x0,y0,x1,y1]（该图 1024 px 内），y = 非透明区上下沿（描入遮罩用）。
 * 以 A04-4 为基准，按包围盒中心重合、面积平方根相等缩放。 */
const LAYERS = [
  { n: 1, b: [175, 100, 890, 905], y: [93, 923] },
  { n: 2, b: [185, 140, 880, 865], y: [139, 867] },
  { n: 3, b: [220, 165, 840, 770], y: [47, 964] },
  { n: 4, b: [243, 228, 835, 775], y: [100, 892] },
];
const bw = (b) => Math.sqrt((b[2] - b[0]) * (b[3] - b[1]));
const REF = LAYERS[3].b, REF_S = bw(REF);
const REF_CX = (REF[0] + REF[2]) / 2, REF_CY = (REF[1] + REF[3]) / 2;
for (const L of LAYERS) {
  L.k = REF_S / bw(L.b);
  L.cx = (L.b[0] + L.b[2]) / 2;
  L.cy = (L.b[1] + L.b[3]) / 2;
  L.size = PLAN * L.k;                         // 该层图片显示边长
  L.ox = (512 - L.cx) * L.k * PLAN / 1024;     // 图片中心相对建筑中心的偏移
  L.oy = (512 - L.cy) * L.k * PLAN / 1024;
  L.sx = (L.n - 1) * 8 - 12;                   // 纸张错位，像一叠纸
  L.sy = (L.n - 1) * 8 - 12;
}

/* 主墙矩形，A04-4 的 1024 px 坐标 [x0,y0,x1,y1]。按 A04-4 目测描，精度低，体块升起时平面图还在底下。 */
const WALLS_PX = [
  [338, 230, 486, 244], [520, 230, 835, 244],           // 上外墙
  [820, 230, 835, 752], [655, 738, 835, 752],            // 右外墙、右下外墙
  [652, 244, 666, 460], [652, 500, 666, 772],            // 右侧分户墙
  [705, 415, 830, 427], [705, 527, 830, 538],            // 右侧卫生间上下墙
  [740, 462, 752, 520],
  [243, 328, 257, 718], [243, 328, 345, 340], [243, 705, 430, 718], // 左翼
  [243, 478, 305, 490],
  [338, 244, 350, 490], [338, 478, 430, 490], [416, 535, 430, 715], // 中部左侧
  [430, 670, 545, 684], [607, 670, 666, 684],            // 起居室下沿
  [470, 244, 482, 335], [470, 325, 532, 337], [520, 244, 532, 295], // 上部内墙
];
// 归一化后转为舞台内相对建筑中心的矩形（x, z 为中心，w, d 为尺寸，单位图幅 px）
const WALLS = WALLS_PX.map(([x0, y0, x1, y1]) => {
  const u = PLAN / 1024;
  return {
    x: ((x0 + x1) / 2 - REF_CX) * u, z: ((y0 + y1) / 2 - REF_CY) * u,
    w: (x1 - x0) * u, d: (y1 - y0) * u,
  };
});

const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const ease = (p) => p * p * (3 - 2 * p);
const easeOut = (p) => 1 - Math.pow(1 - p, 3);
const lerp = (a, b, p) => a + (b - a) * p;

/* 进度映射 */
function layerP(t, n) { return clamp((t - (n - 1) * 0.2) / 0.17); } // 描入，步内 85% 完成
function layerOpacity(t, n) {
  // 下一层开始描入，本层淡到 0.35。再下一层开始，再乘 0.8。
  let o = 1;
  if (n < 4) o *= 1 - 0.65 * ease(layerP(t, n + 1));
  if (n < 3) o *= 1 - 0.2 * ease(layerP(t, n + 2));
  return o;
}
function riseP(t) { return clamp((t - 0.8) / 0.2); }

function el(tag, cls, parent) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (parent) parent.appendChild(e);
  return e;
}
function canWebGL() {
  try {
    const c = document.createElement('canvas');
    return !!(c.getContext('webgl2') || c.getContext('webgl'));
  } catch (_) { return false; }
}
function isDark() {
  const d = document.documentElement.dataset.theme;
  return d === 'dark' || (d !== 'light' && matchMedia('(prefers-color-scheme: dark)').matches);
}
/* 深色模式：线稿是深色线，翻成浅色线。红色云线保持偏红。 */
function invertedCanvas(img) {
  const c = document.createElement('canvas');
  c.width = img.naturalWidth; c.height = img.naturalHeight;
  const x = c.getContext('2d');
  x.drawImage(img, 0, 0);
  const d = x.getImageData(0, 0, c.width, c.height), a = d.data;
  for (let i = 0; i < a.length; i += 4) {
    const r = a[i], g = a[i + 1], b = a[i + 2];
    if (r > g + 40 && r > b + 40) { a[i] = Math.min(255, r + 40); a[i + 1] = g + 50; a[i + 2] = b + 50; }
    else { a[i] = 255 - r; a[i + 1] = 255 - g; a[i + 2] = 255 - b; }
  }
  x.putImageData(d, 0, 0);
  return c;
}
function cssVar(name, fb) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fb;
}

export function mount(sheet, opts = {}) {
  const base = (opts.assets || '../assets/generated/').replace(/\/?$/, '/');
  const reduced = !!opts.reduced;
  const glOK = !reduced && opts.webgl !== false && canWebGL();
  let destroyed = false, curT = 0, raf = 0;

  /* ---------- DOM ---------- */
  const root = el('div', 's2-root');
  root.setAttribute('aria-hidden', 'true');
  const stage = el('div', 's2-stage', root);
  const layers = LAYERS.map((L) => {
    const wrap = el('div', 's2-layer', stage);
    const paper = el('i', 's2-paper', wrap);
    paper.style.cssText = `left:${CX - SHEET_W / 2 + L.sx}px;top:${CY - SHEET_H / 2 + L.sy}px;width:${SHEET_W}px;height:${SHEET_H}px`;
    const img = el('img', 's2-draw', wrap);
    img.alt = ''; img.decoding = 'async';
    img.src = `${base}A04-${L.n}.png`;
    img.style.cssText = `left:${CX + L.ox - L.size / 2}px;top:${CY + L.oy - L.size / 2}px;width:${L.size}px;height:${L.size}px`;
    return { L, wrap, paper, img };
  });

  // SVG 等轴投影退路（同一组墙体矩形）
  const iso = el('div', 's2-iso', stage);
  const isoGround = el('img', 's2-iso-ground', iso);
  isoGround.alt = ''; isoGround.src = `${base}A04-4.png`;
  const C30 = Math.cos(Math.PI / 6);
  isoGround.style.cssText = `left:${CX - PLAN / 2 - (REF_CX - 512) * PLAN / 1024}px;top:${CY - PLAN / 2 - (REF_CY - 512) * PLAN / 1024}px;width:${PLAN}px;height:${PLAN}px;` +
    `transform-origin:${PLAN / 2 + (REF_CX - 512) * PLAN / 1024}px ${PLAN / 2 + (REF_CY - 512) * PLAN / 1024}px;` +
    `transform:matrix(${C30},0.5,${-C30},0.5,0,0)`;
  const NS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(NS, 'svg');
  svg.setAttribute('class', 's2-iso-svg');
  svg.setAttribute('viewBox', `0 0 ${STAGE_W} ${STAGE_H}`);
  iso.appendChild(svg);
  const isoG = document.createElementNS(NS, 'g');
  isoG.setAttribute('transform', `translate(${CX} ${CY})`);
  svg.appendChild(isoG);
  const isoOrder = WALLS.map((w, i) => i).sort((a, b) => (WALLS[a].x + WALLS[a].z) - (WALLS[b].x + WALLS[b].z));
  const P = (x, z, y) => `${((x - z) * C30).toFixed(1)},${((x + z) * 0.5 - y).toFixed(1)}`;
  function drawIso(rise) {
    const out = [];
    for (const i of isoOrder) {
      const w = WALLS[i];
      const h = WALL_H * ease(clamp(rise * 1.25 - (w.x + w.z + 700) / 3000));
      const x0 = w.x - w.w / 2, x1 = w.x + w.w / 2, z0 = w.z - w.d / 2, z1 = w.z + w.d / 2;
      // 可见三面：顶面、南面（z1）、东面（x1）
      out.push(
        `<polygon class="s2-f-l" points="${P(x0, z1, 0)} ${P(x1, z1, 0)} ${P(x1, z1, h)} ${P(x0, z1, h)}"/>`,
        `<polygon class="s2-f-r" points="${P(x1, z1, 0)} ${P(x1, z0, 0)} ${P(x1, z0, h)} ${P(x1, z1, h)}"/>`,
        `<polygon class="s2-f-t" points="${P(x0, z0, h)} ${P(x1, z0, h)} ${P(x1, z1, h)} ${P(x0, z1, h)}"/>`);
    }
    isoG.innerHTML = out.join('');
  }
  sheet.appendChild(root);
  root.dataset.dark = isDark() ? '1' : '0';

  /* ---------- 步 1-4 与退路 ---------- */
  function applyFlat(t) {
    const rise = riseP(t);
    for (const { L, wrap, paper, img } of layers) {
      const p = reduced ? 1 : layerP(t, L.n);
      const started = reduced ? t >= (L.n - 1) * 0.2 - 1e-6 : p > 0;
      wrap.style.visibility = started ? 'visible' : 'hidden';
      paper.style.opacity = reduced ? 1 : clamp(p * 6);
      const top = L.y[0], bot = L.y[1], f = 55;
      const pos = top + p * (bot - top + f);
      img.style.setProperty('--a', `${(((pos - f) / 1024) * 100).toFixed(2)}%`);
      img.style.setProperty('--b', `${((pos / 1024) * 100).toFixed(2)}%`);
      wrap.style.opacity = layerOpacity(reduced ? Math.min(t, 0.8) : t, L.n).toFixed(3);
    }
    const stepFive = t >= 0.8;
    const useGL = glReady && !reduced;
    // 步 5：WebGL 就绪则交给 canvas，否则 SVG 等轴
    iso.style.opacity = !stepFive || useGL ? 0 : reduced ? 1 : clamp(rise * 6).toFixed(3);
    if (stepFive && !useGL) drawIso(reduced ? 1 : rise);
    if (stepFive && !useGL) {
      const f = reduced ? 1 : clamp(rise * 6);
      for (const { wrap, L } of layers) {
        wrap.style.opacity = (L.n === 4 ? 0 : layerOpacity(0.8, L.n) * (1 - f)).toFixed(3);
      }
    }
    if (glReady && !reduced) {
      const on = stepFive;
      cv.style.opacity = on ? 1 : 0;
      for (const { wrap } of layers) if (on) wrap.style.visibility = 'hidden';
    } else if (cv) cv.style.opacity = 0;
  }

  /* ---------- WebGL ---------- */
  let THREE = null, glReady = false, loading = false, cv = null;
  let renderer, scene, camera, wallGroup, wallMeshes = [], planeObjs = [], disposables = [], mq = null, ro = null, texLoaded = 0;
  let pixelScale = 1, mo = null;

  async function loadGL() {
    if (loading || !glOK) return;
    loading = true;
    try {
      THREE = await import(/* @vite-ignore */ THREE_URL);
      if (destroyed) return;
      cv = el('canvas', 's2-gl', stage);
      renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true, alpha: true, premultipliedAlpha: true });
      renderer.setClearColor(0x000000, 0);
      scene = new THREE.Scene();
      camera = new THREE.OrthographicCamera(-STAGE_W / 2, STAGE_W / 2, STAGE_H / 2, -STAGE_H / 2, -6000, 6000);
      scene.add(new THREE.AmbientLight(0xffffff, 1.2));
      const dl = new THREE.DirectionalLight(0xffffff, 2.6);
      dl.position.set(-800, 1000, 450); // 左上前方，三个可见面各有一档亮度
      scene.add(dl);
      buildScene();
      resize();
      ro = new ResizeObserver(() => { resize(); queue(); });
      ro.observe(sheet);
      mo = new MutationObserver(themeChanged);
      mo.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
      mq = matchMedia('(prefers-color-scheme: dark)');
      mq.addEventListener('change', themeChanged);
      glReady = true;
      root.dataset.gl = 'loading';
      // 纹理就绪后再交接，避免交接帧是空的
      await Promise.all(planeObjs.map((o) => o.ready));
      if (destroyed) return;
      root.dataset.gl = 'ready';
      applyFlat(curT); queue();
    } catch (err) {
      glReady = false; // 加载失败：留在 SVG 退路
      console.warn('s2: three 不可用，使用 SVG 等轴退路', err && err.message);
    }
  }

  function pickTex(o) {
    if (!isDark()) return o.tex;
    if (!o.texDark) {
      o.texDark = new THREE.CanvasTexture(invertedCanvas(o.srcImg));
      o.texDark.colorSpace = THREE.SRGBColorSpace; o.texDark.anisotropy = 4;
      disposables.push(o.texDark);
    }
    return o.texDark;
  }
  function colors() {
    return {
      struct: cssVar('--struct', '#006761'), paper: cssVar('--paper', '#F4F7F5'),
      ink: cssVar('--ink', '#141a1b'), rule: cssVar('--rule-strong', '#6b7773'),
    };
  }
  let wallMat, edgeMat, paperMats = [], ruleMats = [];
  function themeChanged() {
    root.dataset.dark = isDark() ? '1' : '0';
    setTimeout(recolor, 0); // 令牌先更新，再读
  }
  function recolor() {
    if (!THREE) return;
    const c = colors();
    for (const o of planeObjs) if (o.img) { o.img.map = pickTex(o); o.img.needsUpdate = true; }
    wallMat.color.set(c.struct); edgeMat.color.set(c.paper);
    paperMats.forEach((m) => m.color.set(c.paper));
    ruleMats.forEach((m) => m.color.set(c.rule));
    queue();
  }

  function buildScene() {
    const c = colors();
    wallGroup = new THREE.Group();
    scene.add(wallGroup);
    wallMat = new THREE.MeshLambertMaterial({ color: c.struct });
    edgeMat = new THREE.LineBasicMaterial({ color: c.paper });
    const unit = new THREE.BoxGeometry(1, 1, 1).translate(0, 0.5, 0);
    const unitEdges = new THREE.EdgesGeometry(unit);
    disposables.push(unit, unitEdges, wallMat, edgeMat);
    for (const w of WALLS) {
      const m = new THREE.Mesh(unit, wallMat);
      m.position.set(w.x, 0, w.z);
      m.scale.set(w.w, 0.001, w.d);
      m.add(new THREE.LineSegments(unitEdges, edgeMat));
      m.userData = { delay: clamp((w.x + w.z + 700) / 3000) };
      wallGroup.add(m); wallMeshes.push(m);
    }
    const loader = new THREE.TextureLoader();
    for (const L of LAYERS) {
      const grp = new THREE.Group();
      const pm = new THREE.MeshBasicMaterial({ color: c.paper, transparent: true, opacity: 0.5, depthWrite: false });
      const sheetGeo = new THREE.PlaneGeometry(SHEET_W, SHEET_H).rotateX(-Math.PI / 2);
      const sheetMesh = new THREE.Mesh(sheetGeo, pm);
      sheetMesh.position.set(L.sx, -1, L.sy);
      sheetMesh.renderOrder = L.n * 2;
      const edge = new THREE.LineSegments(new THREE.EdgesGeometry(sheetGeo), new THREE.LineBasicMaterial({ color: c.rule, transparent: true, opacity: 0.6 }));
      edge.position.copy(sheetMesh.position);
      const ready = new Promise((res) => {
        loader.load(`${base}A04-${L.n}.png`, (tex) => {
          tex.colorSpace = THREE.SRGBColorSpace;
          tex.anisotropy = 4;
          o.tex = tex; o.srcImg = tex.image; o.texDark = null;
          const im = new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false });
          const g = new THREE.PlaneGeometry(L.size, L.size).rotateX(-Math.PI / 2);
          const mesh = new THREE.Mesh(g, im);
          mesh.position.set(L.ox, -0.5, L.oy);
          mesh.renderOrder = L.n * 2 + 1;
          grp.add(mesh);
          o.img = im; im.map = pickTex(o); im.needsUpdate = true;
          disposables.push(tex, im, g);
          res();
        }, undefined, () => res());
      });
      const o = { L, grp, pm, ready, img: null, sheetMesh };
      grp.add(sheetMesh, edge);
      scene.add(grp);
      planeObjs.push(o);
      paperMats.push(pm); ruleMats.push(edge.material);
      disposables.push(sheetGeo, pm, edge.geometry, edge.material);
    }
  }

  function resize() {
    if (!renderer) return;
    const r = sheet.getBoundingClientRect();
    pixelScale = sheet.offsetWidth ? r.width / sheet.offsetWidth : 1;
    const pr = Math.min(window.devicePixelRatio || 1, 2) * pixelScale;
    renderer.setPixelRatio(Math.max(0.3, pr));
    renderer.setSize(STAGE_W, STAGE_H, false);
    cv.style.width = STAGE_W + 'px'; cv.style.height = STAGE_H + 'px';
  }

  function renderGL() {
    raf = 0;
    if (!glReady || destroyed || curT < 0.8) return;
    const rise = riseP(curT);
    const e = ease(rise);
    const el_ = lerp(90, 35, e) * Math.PI / 180;
    const yaw = lerp(0, -18, e) * Math.PI / 180;
    // 墙体拉伸，沿对角线错开，像波浪升起
    for (const m of wallMeshes) {
      const p = easeOut(clamp(rise * 1.3 - m.userData.delay * 0.3));
      m.scale.y = Math.max(0.001, WALL_H * p);
    }
    // 三层旧稿向下分开，露出叠层
    const gap = 46 * e;
    for (const o of planeObjs) {
      const L = o.L;
      o.grp.position.y = -(4 - L.n) * gap;
      const op = layerOpacity(0.8, L.n) * (L.n === 4 ? 1 : lerp(1, 0.8, e));
      o.pm.opacity = 0.5 * Math.min(1, op + 0.3);
      if (o.img) o.img.opacity = op;
    }
    const ty = WALL_H * 0.3 * e;
    const R = 2500;
    const h = [Math.sin(yaw), Math.cos(yaw)];
    camera.position.set(h[0] * Math.cos(el_) * R, ty + Math.sin(el_) * R, h[1] * Math.cos(el_) * R);
    camera.up.set(-h[0], 0, -h[1]);
    camera.zoom = lerp(1, 0.88, e);
    camera.updateProjectionMatrix();
    camera.lookAt(0, ty, 0);
    renderer.render(scene, camera);
  }
  function queue() { if (!raf && glReady && !destroyed) raf = requestAnimationFrame(renderGL); }

  /* ---------- 入口 ---------- */
  function set(t) {
    if (destroyed) return;
    curT = clamp(+t || 0);
    if (glOK && !loading && curT >= PREFETCH_AT) loadGL();
    applyFlat(curT);
    queue();
  }
  set(0);

  return {
    set,
    destroy() {
      destroyed = true;
      if (raf) cancelAnimationFrame(raf);
      if (ro) ro.disconnect();
      if (mq) mq.removeEventListener('change', themeChanged);
      if (mo) mo.disconnect();
      disposables.forEach((d) => { try { d.dispose(); } catch (_) {} });
      if (renderer) { renderer.dispose(); try { renderer.forceContextLoss(); } catch (_) {} }
      root.remove();
      wallMeshes = []; planeObjs = []; paperMats = []; ruleMats = [];
    },
  };
}
