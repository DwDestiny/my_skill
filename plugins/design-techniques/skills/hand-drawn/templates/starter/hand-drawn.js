/*
 * Input: 页面里的 canvas 与 HTML 元素；HandDrawn.init(opts) 的纸色、墨色、纸纹参数
 * Output: 全局 HandDrawn（纸面高度场、钢笔、彩铅、排线、圈、框、胶带、星、卡纸、花边、手写排字、画布摆放）
 * Pos: hand-drawn 手法的画具包。无依赖，经典 <script> 引入，file:// 直接打开也能用
 *
 * 默认数值来自已验证的一次讲课页（2026-10-27），用户评价纸面、颗粒、字体“很好了”。数值是锚点，可按题材改。
 */
(function (root) {
  "use strict";
  const HD = {};
  HD.DPR = Math.min(2, root.devicePixelRatio || 1);

  // ---------- 默认值：暖奶油纸、暖黑墨 ----------
  HD.opts = {
    tile: 512,                       // 纸纹平铺块，CSS 像素
    paper: [241, 233, 214],          // 纸色 #f1e9d6
    ink: "#2b2420",                  // 暖黑钢笔
    rule: "#b3a487",                 // 花边、分隔虚线
    accent: "#e0a84f",               // 星、胶带的主色
    tapeColor: "rgba(224,168,79,.34)",
    layers: [[200, .46], [64, .26], [16, .12]], // 高度场三层：格数 × 权重
    grain: .16,                      // 逐像素白噪声权重
    light: .07,                      // 左上来光的凹凸强度
    fibres: 170, specks: 28,         // 纤维短弧、杂点
    toothThr: .47, toothSoft: .17,   // 彩铅进不去的凹处
    dropThr: .28, dropSoft: .12,     // 墨也断开的深坑
    keepThr: .22, keepSoft: .1, keepMax: .3, // HTML 大字遮罩：最多去掉 30%
    seed: 7,
  };

  // ---------- 随机与噪声：带种子，每次画出来一样 ----------
  HD.rng = function (seed) {
    let a = seed >>> 0;
    return () => { a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  };
  // 一维平滑噪声，返回 0..1
  HD.noise1 = function (seed) {
    const r = HD.rng(seed), v = Array.from({length: 512}, r);
    return x => { const i = Math.floor(x), f = x - i, a = v[i & 511], b = v[(i + 1) & 511]; return a + (b - a) * f * f * (3 - 2 * f); };
  };
  // 可平铺的二维值噪声：cells 格首尾相接，铺满 S×S
  HD.vnoise = function (S, cells, seed) {
    const g = Array.from({length: cells * cells}, HD.rng(seed)), out = new Float32Array(S * S), k = cells / S;
    for (let y = 0; y < S; y++) {
      const fy = y * k, j = fy | 0, ty = fy - j, sy = ty * ty * (3 - 2 * ty), r0 = j * cells, r1 = (j + 1) % cells * cells;
      for (let x = 0; x < S; x++) {
        const fx = x * k, i = fx | 0, tx = fx - i, sx = tx * tx * (3 - 2 * tx), i1 = (i + 1) % cells;
        const a = g[r0 + i] + (g[r0 + i1] - g[r0 + i]) * sx, b = g[r1 + i] + (g[r1 + i1] - g[r1 + i]) * sx;
        out[y * S + x] = a + (b - a) * sy;
      }
    }
    return out;
  };

  // ---------- 纸：一张高度场派生出纸面、彩铅齿、墨缺口、大字遮罩，颗粒才对得上 ----------
  HD.init = function (o = {}) {
    const O = Object.assign(HD.opts, o), DPR = HD.DPR, S = Math.round(O.tile * DPR), r = HD.rng(O.seed);
    const L = O.layers.map(([cells, w], i) => [HD.vnoise(S, cells, O.seed * 3 + i), w]);
    const M = HD.vnoise(S, 4, O.seed * 3 + 9);
    const h = new Float32Array(S * S); let lo = 9, hi = -9;
    for (let p = 0; p < h.length; p++) { let v = r() * O.grain; for (const [A, w] of L) v += A[p] * w; h[p] = v; if (v < lo) lo = v; if (v > hi) hi = v; }
    for (let p = 0; p < h.length; p++) h[p] = (h[p] - lo) / (hi - lo);
    const clamp = v => v < 0 ? 0 : v > 1 ? 1 : v;
    const mk = f => { const c = document.createElement("canvas"); c.width = c.height = S; const x = c.getContext("2d"), d = x.createImageData(S, S); for (let p = 0; p < h.length; p++) f(d.data, p); x.putImageData(d, 0, 0); return c; };
    const P = O.paper;
    // 纸面：左上来光，凸处亮、凹处暗，再叠极淡的大块深浅
    const bg = mk((D, p) => {
      const x = p % S, y = (p / S) | 0, a = h[(y + S - 1) % S * S + (x + S - 1) % S], b = h[(y + 1) % S * S + (x + 1) % S];
      const l = 1 + (a - b) * O.light + (h[p] - .5) * .05 + (M[p] - .5) * .035;
      D[p * 4] = P[0] * l; D[p * 4 + 1] = P[1] * l; D[p * 4 + 2] = P[2] * l; D[p * 4 + 3] = 255;
    });
    // 纤维与杂点：短弧线有深有浅，跨边的画九次保证平铺无缝
    const x = bg.getContext("2d"), fr = HD.rng(O.seed + 24);
    for (let i = 0; i < O.fibres; i++) {
      const px = fr() * S, py = fr() * S, a = fr() * Math.PI, len = (6 + fr() * 24) * DPR, bend = (fr() - .5) * len * .5, dark = fr() < .55;
      x.strokeStyle = dark ? `rgba(118,94,60,${.05 + fr() * .08})` : `rgba(255,252,242,${.22 + fr() * .3})`; x.lineWidth = (.35 + fr() * .5) * DPR;
      for (const ox of [-S, 0, S]) for (const oy of [-S, 0, S]) {
        const sx = px + ox, sy = py + oy, ex = sx + Math.cos(a) * len, ey = sy + Math.sin(a) * len;
        x.beginPath(); x.moveTo(sx, sy); x.quadraticCurveTo((sx + ex) / 2 - Math.sin(a) * bend, (sy + ey) / 2 + Math.cos(a) * bend, ex, ey); x.stroke();
      }
    }
    for (let i = 0; i < O.specks; i++) { const R = (.3 + fr() * .7) * DPR; x.fillStyle = `rgba(92,70,44,${.12 + fr() * .25})`; x.beginPath(); x.ellipse(fr() * S, fr() * S, R, R * (.6 + fr() * .4), fr() * 3, 0, 7); x.fill(); }
    HD.paper = {
      S, h, bg,
      tooth: mk((D, p) => { D[p * 4 + 3] = clamp((O.toothThr - h[p]) / O.toothSoft) * 255; }),
      drop: mk((D, p) => { D[p * 4 + 3] = clamp((O.dropThr - h[p]) / O.dropSoft) * 255; }),
      keep: mk((D, p) => { D[p * 4 + 3] = (1 - O.keepMax * clamp((O.keepThr - h[p]) / O.keepSoft)) * 255; }),
    };
    // 页面背景用 --paper-img，HTML 大字用 --ink-mask（background-size / mask-size 写 tile px）
    const set = (cv, name) => new Promise(res => cv.toBlob(b => { document.documentElement.style.setProperty(name, `url(${URL.createObjectURL(b)})`); res(); }));
    return Promise.all([set(HD.paper.bg, "--paper-img"), set(HD.paper.keep, "--ink-mask")]);
  };

  // 纸纹按页面坐标对齐：画布在页面哪里，就取纸纹的哪一块
  HD.paperPattern = function (c, tile, cv) {
    const p = c.createPattern(tile, "repeat"), r = cv.getBoundingClientRect(), D = HD.DPR;
    p.setTransform(new DOMMatrix([1, 0, 0, 1, -Math.round((r.left + root.scrollX) * D), -Math.round((r.top + root.scrollY) * D)])); return p;
  };
  // 画完一层后，把纸的深坑里的墨擦掉一些（a 越大缺口越明显）
  HD.paperize = function (cv, a = .55) {
    const c = cv.getContext("2d"); c.save(); c.setTransform(1, 0, 0, 1, 0, 0);
    c.globalCompositeOperation = "destination-out"; c.globalAlpha = a; c.fillStyle = HD.paperPattern(c, HD.paper.drop, cv); c.fillRect(0, 0, cv.width, cv.height); c.restore();
  };

  // ---------- 画布摆放 ----------
  // 画布铺满 ref 元素，按 ref 的 CSS 像素作画
  HD.fitTo = function (cv, ref) {
    const D = HD.DPR;
    cv.width = Math.max(1, Math.round(ref.clientWidth * D)); cv.height = Math.max(1, Math.round(ref.clientHeight * D));
    const c = cv.getContext("2d"); c.setTransform(D, 0, 0, D, 0, 0); return c;
  };
  // 在父元素坐标里放一块小画布，返回按父元素坐标作画的 ctx
  HD.place = function (cv, x, y, w, h) {
    const D = HD.DPR;
    Object.assign(cv.style, {left: x + "px", top: y + "px", width: w + "px", height: h + "px"});
    cv.width = Math.max(1, Math.round(w * D)); cv.height = Math.max(1, Math.round(h * D));
    const c = cv.getContext("2d"); c.setTransform(D, 0, 0, D, -x * D, -y * D); return c;
  };
  // 同上，但按图的逻辑坐标作画（k = CSS 像素 / 逻辑单位）
  HD.placeIn = function (cv, k, x0, y0, w, h) { const c = HD.place(cv, x0 * k, y0 * k, w * k, h * k); c.scale(k, k); return c; };

  // ---------- 几何小工具 ----------
  HD.pathOf = function (c, pts) { c.beginPath(); pts.forEach(([x, y], i) => i ? c.lineTo(x, y) : c.moveTo(x, y)); c.closePath(); };
  HD.resample = function (pts, step, closed) {
    const P = closed ? [...pts, pts[0]] : pts, out = [];
    for (let i = 0; i < P.length - 1; i++) {
      const [x1, y1] = P[i], [x2, y2] = P[i + 1], d = Math.hypot(x2 - x1, y2 - y1) || 1;
      const nx = -(y2 - y1) / d, ny = (x2 - x1) / d, k = Math.max(1, Math.round(d / step));
      for (let s = 0; s < k; s++) out.push([x1 + (x2 - x1) * s / k, y1 + (y2 - y1) * s / k, nx, ny]);
    }
    const L = P[P.length - 1]; out.push([L[0], L[1], 0, 0]); return out;
  };
  HD.bounds = function (pts) { const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]); return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)]; };
  // 三次贝塞尔上一点
  HD.bez = function (P, t) { const m = 1 - t; return [0, 1].map(k => m * m * m * P[0][k] + 3 * m * m * t * P[1][k] + 3 * m * t * t * P[2][k] + t * t * t * P[3][k]); };

  // ---------- 画具 ----------
  // 钢笔：一笔主线加一笔细的复描，线位按噪声轻微摆动
  // o: {w 线宽 1.3, jit 摆幅 .8, alpha, color, seed, closed}
  HD.pen = function (c, pts, o = {}) {
    const n = HD.noise1(o.seed || 1), q = HD.resample(pts, 4, o.closed), jit = o.jit ?? .8;
    c.lineJoin = c.lineCap = "round"; c.strokeStyle = o.color || HD.opts.ink;
    for (let pass = 0; pass < 2; pass++) {
      c.beginPath();
      q.forEach(([x, y, nx, ny], i) => { const j = (n(i * .19 + pass * 40) - .5) * jit * 2; i ? c.lineTo(x + nx * j, y + ny * j) : c.moveTo(x + nx * j, y + ny * j); });
      if (o.closed) c.closePath();
      c.lineWidth = (o.w ?? 1.3) * (pass ? .5 : 1); c.globalAlpha = (o.alpha ?? 1) * (pass ? .45 : .92); c.stroke();
    }
    c.globalAlpha = 1;
  };

  // 彩铅：同一角度的短笔触，深浅由 alpha(x,y) 决定，最后按同一张纸的齿打出颗粒，再 multiply 落到画布
  // o: {color, seed, angle -1.08, len 13, w 1.6, density 每平方单位笔数, alpha(x,y) 0..1, op 整体不透明, tooth 齿的强度 .6}
  let SCR = null;
  HD.pencil = function (c, clip, box, o) {
    const cv = c.canvas;
    if (!SCR || SCR.width !== cv.width || SCR.height !== cv.height) { SCR = document.createElement("canvas"); SCR.width = cv.width; SCR.height = cv.height; }
    const s = SCR.getContext("2d"); s.setTransform(1, 0, 0, 1, 0, 0); s.clearRect(0, 0, SCR.width, SCR.height);
    s.setTransform(c.getTransform()); s.save(); if (clip) { HD.pathOf(s, clip); s.clip(); }
    const r = HD.rng(o.seed || 1), [x0, y0, x1, y1] = box, N = Math.round((x1 - x0) * (y1 - y0) * o.density);
    const ang = o.angle ?? -1.08, len = o.len ?? 13, w = o.w ?? 1.6, al = o.alpha || (() => .8);
    s.lineCap = "round"; s.strokeStyle = o.color;
    for (let i = 0; i < N; i++) {
      const x = x0 + r() * (x1 - x0), y = y0 + r() * (y1 - y0);
      if (r() > al(x, y)) continue;
      const L = len * (.6 + r() * .8), a = ang + (r() - .5) * .2, dx = Math.cos(a) * L / 2, dy = Math.sin(a) * L / 2;
      s.globalAlpha = (.22 + r() * .45) * (o.op ?? 1); s.lineWidth = w * (.7 + r() * .7);
      s.beginPath(); s.moveTo(x - dx, y - dy); s.lineTo(x + dx, y + dy); s.stroke();
    }
    s.restore();
    s.setTransform(1, 0, 0, 1, 0, 0); s.globalCompositeOperation = "destination-out"; s.globalAlpha = o.tooth ?? .6;
    s.fillStyle = HD.paperPattern(s, HD.paper.tooth, cv); s.fillRect(0, 0, SCR.width, SCR.height);
    s.globalCompositeOperation = "source-over"; s.globalAlpha = 1;
    c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.globalCompositeOperation = "multiply"; c.drawImage(SCR, 0, 0); c.restore();
  };

  // 墨线排线：一组平行线，只画在 tone(x,y,lr) > thr 的地方；几层不同阈值、角度叠起来，暗处自然更密
  // o: {angle 弧度, sp 线距 5.6, thr, w .8, alpha .85, seed, tone(x,y,lr) 0..1, level(x,y,lr) 0..1 可选：
  //     每根线按 level 分段改墨色，越大越实；lr 是这根线的随机数，用来错开分界处的起笔}
  HD.hatch = function (c, clip, box, o) {
    const r = HD.rng(o.seed || 1), n = HD.noise1((o.seed || 1) + 2000), [x0, y0, x1, y1] = box;
    const du = Math.cos(o.angle || 0), dv = Math.sin(o.angle || 0), pu = -dv, pv = du;
    const cs = [[x0, y0], [x1, y0], [x0, y1], [x1, y1]];
    const offs = cs.map(([x, y]) => x * pu + y * pv), ts = cs.map(([x, y]) => x * du + y * dv);
    const oMin = Math.min(...offs), oMax = Math.max(...offs), tMin = Math.min(...ts), tMax = Math.max(...ts);
    const sp = o.sp ?? 5.6, base = o.alpha ?? .85, lvlF = o.level;
    c.save(); if (clip) { HD.pathOf(c, clip); c.clip(); }
    c.strokeStyle = o.color || HD.opts.ink; c.lineCap = "round";
    let li = 0;
    for (let off = oMin + r() * sp; off < oMax; off += sp * (.7 + r() * .6), li++) {
      const lr = r(), lw = (o.w ?? .8) * (.65 + r() * .6);
      let on = false, lvNow = null;
      const flush = () => { if (lvNow !== null) { c.globalAlpha = base * (lvlF ? .45 + .55 * lvNow : 1); c.lineWidth = lw; c.stroke(); } c.beginPath(); on = false; };
      c.beginPath();
      for (let t = tMin; t <= tMax; t += 2.5) {
        const x = pu * off + du * t, y = pv * off + dv * t;
        if (x < x0 - 2 || x > x1 + 2 || y < y0 - 3 || y > y1 + 3) { on = false; continue; }
        const lv = lvlF ? lvlF(x, y, lr) : 1;
        if (lv !== lvNow) { const keep = on, px = c._hx, py = c._hy; flush(); lvNow = lv; if (keep) { c.moveTo(px, py); on = true; } }
        const T = o.tone(x, y, lr) + (n(li * 5.3 + t * .045) - .5) * .16;
        const draw = T > o.thr && r() > .015;
        const k = (n(li * 2.7 + t * .012) - .5) * 1.8 + (n(li * 9.1 + t * .08) - .5) * .5, X = x + pu * k, Y = y + pv * k;
        c._hx = X; c._hy = Y;
        if (draw) { on ? c.lineTo(X, Y) : c.moveTo(X, Y); on = true; } else on = false;
      }
      flush();
    }
    c.restore(); c.globalAlpha = 1;
  };
  // 已验证的四层排线：两层顺向、两层交叉；阈值逐档升高，深处一层层加上去
  HD.HATCH_LAYERS = [
    {seed: 1, angle: 0, sp: 5.6, thr: .16, w: .8, alpha: .85},
    {seed: 2, angle: 0, sp: 5.6, thr: .42, w: .75, alpha: .8},
    {seed: 3, angle: .5, sp: 5.4, thr: .6, w: .7, alpha: .75},
    {seed: 4, angle: -.5, sp: 5.4, thr: .78, w: .7, alpha: .75},
  ];

  // 手画的圈：起笔收笔略过头，半径带一点抖。填色时取前 n-3 个点
  HD.ring = function (cx, cy, R, seed, n = 40) {
    const w = HD.noise1(seed);
    return Array.from({length: n}, (_, k) => { const a = -1.9 + k / (n - 3) * Math.PI * 2.06, rr = R * (1 + (w(k * .4) - .5) * .1); return [cx + Math.cos(a) * rr, cy + Math.sin(a) * rr]; });
  };
  // 手画的圆角框（点列，交给 pen 画）
  HD.rbox = function (x, y, w, h, rad) {
    const pts = [], arc = (cx, cy, a0) => { for (let k = 0; k <= 4; k++) { const a = a0 + k / 4 * Math.PI / 2; pts.push([cx + Math.cos(a) * rad, cy + Math.sin(a) * rad]); } };
    arc(x + w - rad, y + rad, -Math.PI / 2); arc(x + w - rad, y + h - rad, 0); arc(x + rad, y + h - rad, Math.PI / 2); arc(x + rad, y + rad, Math.PI);
    return pts;
  };
  // 纸胶带：半透明长条，两头撕成锯齿。x,y 为中心，L 长，T 宽，a 角度
  HD.tape = function (c, x, y, L, T, a, color, seed) {
    const r = HD.rng(seed), n = 5, pts = [[-L / 2, -T / 2], [L / 2, -T / 2]];
    for (let i = 1; i <= n; i++) pts.push([L / 2 + (i % 2 ? 3 : -1.5) + (r() - .5) * 2, -T / 2 + T * i / n]);
    pts.push([-L / 2, T / 2]);
    for (let i = n - 1; i >= 1; i--) pts.push([-L / 2 + (i % 2 ? -3 : 1.5) + (r() - .5) * 2, -T / 2 + T * i / n]);
    c.save(); c.translate(x, y); c.rotate(a); c.fillStyle = color || HD.opts.tapeColor; HD.pathOf(c, pts); c.fill();
    c.globalAlpha = .3; c.strokeStyle = "#fffaf0"; c.lineWidth = .8; c.beginPath(); c.moveTo(-L / 2 + 4, -T / 2 + 2.5); c.lineTo(L / 2 - 5, -T / 2 + 2); c.stroke();
    c.restore();
  };
  // 小星星涂鸦：四角星，填一点彩铅色
  HD.sparkle = function (c, x, y, R, seed, fill) {
    const pts = [];
    for (let k = 0; k < 8; k++) { const a = k * Math.PI / 4 - Math.PI / 2, rr = k % 2 ? R * .28 : R; pts.push([x + Math.cos(a) * rr, y + Math.sin(a) * rr]); }
    if (fill) { c.save(); c.globalAlpha = .6; c.fillStyle = fill; HD.pathOf(c, pts); c.fill(); c.restore(); }
    HD.pen(c, pts, {closed: true, w: Math.max(.8, R * .09), seed, jit: .25});
  };
  // 一张浅色卡纸：边缘手裁略抖，落一点影子；纸纹取同一张纸再提亮（普通混合，multiply 不会变亮）
  // k = 当前 ctx 的缩放（CSS 像素 / 逻辑单位）；shadow 按设备像素算，要手乘 DPR·k
  HD.paperCard = function (c, x, y, w, h, seed, k = 1) {
    const n = HD.noise1(seed), pts = [], D = HD.DPR;
    const edge = (x1, y1, x2, y2, o) => {
      const L = Math.hypot(x2 - x1, y2 - y1), N = Math.max(2, Math.round(L / 10));
      for (let i = 0; i < N; i++) { const t = i / N, j = (n(o + i * .7) - .5) * 1.6; pts.push([x1 + (x2 - x1) * t - (y2 - y1) / L * j, y1 + (y2 - y1) * t + (x2 - x1) / L * j]); }
    };
    edge(x, y, x + w, y, 0); edge(x + w, y, x + w, y + h, 50); edge(x + w, y + h, x, y + h, 100); edge(x, y + h, x, y, 150);
    const p = c.createPattern(HD.paper.bg, "repeat"); p.setTransform(new DOMMatrix().scale(1 / D));
    c.save(); c.shadowColor = "rgba(70,50,25,.2)"; c.shadowBlur = 16 * D * k; c.shadowOffsetX = 2 * D * k; c.shadowOffsetY = 6 * D * k;
    c.fillStyle = p; HD.pathOf(c, pts); c.fill(); c.restore();
    c.save(); c.fillStyle = "rgba(255,252,244,.42)"; HD.pathOf(c, pts); c.fill(); c.restore();
    HD.pen(c, pts, {closed: true, w: .8, alpha: .35, color: HD.opts.rule, seed: seed + 1, jit: .3});
    return pts;
  };
  // 手抄报花边：一道钢笔边，内圈一圈小点，四角各一颗星。m = 边距（桌面 20，手机 6）
  HD.frame = function (c, W, H, m, seed) {
    const col = HD.opts.rule, r = HD.rng(seed + 2);
    HD.pen(c, [[m, m], [W - m, m], [W - m, H - m], [m, H - m]], {closed: true, w: 1.1, alpha: .6, color: col, seed, jit: .9});
    const m2 = m + 7; c.fillStyle = col; c.globalAlpha = .55;
    const dots = (x1, y1, x2, y2) => { const L = Math.hypot(x2 - x1, y2 - y1); for (let s = 0; s < L; s += 9) { c.beginPath(); c.arc(x1 + (x2 - x1) * s / L + (r() - .5), y1 + (y2 - y1) * s / L + (r() - .5), .9 + r() * .5, 0, 7); c.fill(); } };
    dots(m2, m2, W - m2, m2); dots(W - m2, m2, W - m2, H - m2); dots(W - m2, H - m2, m2, H - m2); dots(m2, H - m2, m2, m2);
    c.globalAlpha = 1;
    [[m, m], [W - m, m], [W - m, H - m], [m, H - m]].forEach(([x, y], i) => HD.sparkle(c, x, y, m > 12 ? 9 : 6, seed + 10 + i, HD.opts.accent));
  };
  // 页眉标签底下贴一条胶带。R = {x,y,w,h}，在画布坐标里
  HD.tagTape = function (c, R, seed, color) { HD.tape(c, R.x + R.w / 2 + 2, R.y + R.h * .52, R.w + 26, R.h * .92, -.015, color || HD.opts.tapeColor, seed); };
  // 一段线越走越断：实线段越来越短、空隙越来越长、墨越来越淡（用于“断掉”“没走到”）
  // at(s) 给出弧长 s 处的点；从 s0 走到 s1
  HD.fadeDash = function (c, at, s0, s1, o = {}) {
    const r = HD.rng(o.seed || 1), T = s1, ps = o.scale || 1, run = (a, b) => { const n = Math.max(2, Math.ceil((b - a) / 3)); return Array.from({length: n + 1}, (_, i) => at(a + (b - a) * i / n)); };
    let s = s0, i = 0;
    while (s < T) {
      const f = s / T, len = Math.max(1.2, Math.pow(1 - f, 1.7) * (o.len0 || 52)) * ps, gap = ((f - s0 / T) * 70 + 3 + r() * 4) * ps, alpha = 1 - .95 * f * f;
      if (alpha < .1) break;
      HD.pen(c, run(s, Math.min(T, s + len)), {w: (o.w || 2.8) * (1 - .6 * f) * ps, alpha, seed: (o.seed || 1) + 10 + i++, jit: .5});
      s += len + gap;
    }
  };

  // ---------- HTML 文字也按手写排：每个字的基线和倾斜略有不同 ----------
  // 逐字包 <span class="ch" style="--i:序号">；CSS 里给 .ch 写 display:inline-block，
  // “抖一下”的动画用独立的 translate / rotate 属性，才能和这里的 transform 叠加
  HD.handset = function (el, seed, amp = 1) {
    const r = HD.rng(seed); let idx = 0;
    const walk = node => [...node.childNodes].forEach(ch => {
      if (ch.nodeType === 3) {
        const f = document.createDocumentFragment();
        [...ch.textContent].forEach(t => {
          if (!t.trim()) { f.append(t); return; }
          const s = document.createElement("span"); s.className = "ch"; s.textContent = t; s.style.setProperty("--i", idx++);
          s.style.transform = `translateY(${((r() - .5) * .07 * amp).toFixed(3)}em) rotate(${((r() - .5) * 3.2 * amp).toFixed(2)}deg)`; f.append(s);
        });
        ch.replaceWith(f);
      } else if (ch.nodeType === 1 && ch.tagName !== "BR") walk(ch);
    });
    walk(el);
  };
  // 图里的文字标签：HTML 绝对定位，按图的逻辑坐标放（百分比），字号用 cqw 随图缩放
  // o: {size 逻辑字号, cls, ax 水平锚点百分比（-50 居中，0 左齐，-100 右齐）, color, jitter 种子}
  HD.label = function (box, W, H, x, y, text, o = {}) {
    const el = document.createElement("span");
    el.className = "lb " + (o.cls || "");
    el.style.left = (x / W * 100) + "%"; el.style.top = (y / H * 100) + "%";
    el.style.fontSize = (o.size / W * 100) + "cqw";
    el.style.transform = `translate(${o.ax ?? -50}%, -50%)`;
    if (o.color) el.style.color = o.color;
    const r = HD.rng(o.jitter ?? 700);
    el.innerHTML = [...text].map((ch, k) => ch === " " ? " " : `<span class="ch" style="--i:${k};transform:translateY(${((r() - .5) * .08).toFixed(3)}em) rotate(${((r() - .5) * 3).toFixed(2)}deg)">${ch}</span>`).join("");
    box.appendChild(el); return el;
  };
  // 字体先显式加载再画：fonts.ready 可能在字体开始加载前就返回
  HD.fontsReady = function (specs) {
    return Promise.all(specs.map(([fam, sample]) => document.fonts.load(`1em "${fam}"`, sample))).then(() => document.fonts.ready);
  };

  root.HandDrawn = HD;
})(window);
