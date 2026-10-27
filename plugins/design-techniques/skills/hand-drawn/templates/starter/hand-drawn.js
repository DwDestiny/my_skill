/*
 * Input: 页面里的 canvas 与 HTML 元素；HandDrawn.init(opts) 的纸色、墨色、纸纹参数
 * Output: 全局 HandDrawn（纸面高度场、钢笔、彩铅、排线、圈、框、胶带、星、卡纸、花边、手写排字、画布摆放，以及画风景用的 hatchIn、under、云、松、灌木、石、山脊、雾、四边淡出）
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
    // 深坑处的纸色：自带纸底的画布（paperizeN）不能擦成透明，改成在坑里补回纸色
    const pit = document.createElement("canvas"); pit.width = pit.height = S;
    { const q = pit.getContext("2d"); q.drawImage(bg, 0, 0); q.globalCompositeOperation = "destination-in"; q.drawImage(HD.paper.drop, 0, 0); }
    HD.paper.pit = pit;
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
  HD.pathOf = function (c, pts) { c.beginPath(); (Array.isArray(pts[0][0]) ? pts : [pts]).forEach(P => { P.forEach(([x, y], i) => i ? c.lineTo(x, y) : c.moveTo(x, y)); c.closePath(); }); }; // pts 可以是多个多边形
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
    const ang = o.angle ?? -1.08, len = o.len ?? 13, w = o.w ?? 1.6, al = o.alpha || (() => .8);
    // 只在这一笔用到的矩形里清、打颗粒、合成：大画布上画小块也不慢
    const s = SCR.getContext("2d"), T = c.getTransform(), m = len + w * 2, [x0, y0, x1, y1] = box;
    const P = [[x0 - m, y0 - m], [x1 + m, y0 - m], [x0 - m, y1 + m], [x1 + m, y1 + m]].map(([x, y]) => T.transformPoint(new DOMPoint(x, y)));
    const rx = Math.max(0, Math.floor(Math.min(...P.map(p => p.x)))), ry = Math.max(0, Math.floor(Math.min(...P.map(p => p.y))));
    const rw = Math.min(cv.width, Math.ceil(Math.max(...P.map(p => p.x)))) - rx, rh = Math.min(cv.height, Math.ceil(Math.max(...P.map(p => p.y)))) - ry;
    if (rw <= 0 || rh <= 0) return;
    s.setTransform(1, 0, 0, 1, 0, 0); s.clearRect(rx, ry, rw, rh);
    s.setTransform(T); s.save(); if (clip) { HD.pathOf(s, clip); s.clip(); }
    const r = HD.rng(o.seed || 1), N = Math.round((x1 - x0) * (y1 - y0) * o.density);
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
    s.fillStyle = HD.paperPattern(s, HD.paper.tooth, cv); s.fillRect(rx, ry, rw, rh);
    s.globalCompositeOperation = "source-over"; s.globalAlpha = 1;
    c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.globalCompositeOperation = "multiply"; c.drawImage(SCR, rx, ry, rw, rh, rx, ry, rw, rh); c.restore();
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

  // ---------- 场景画具：画一幅有远近的画（天、山、岸、树、云、石）时用 ----------
  // 通用的意思是不依赖具体几何；放进场景、按场景坐标作画的 pl()/几何函数由页面自己写（见 templates/starter/index.html）
  // 钢笔排线（短版）：一组略抖的平行线铺满 box、按 clip 裁；给了 tone(x,y) 就只在比 thr 深的地方下笔。o:{seed, angle, sp, w, alpha, color, step 3, wob 1.2, tone, thr .5, rag .3, gaps .008}
  HD.hatchIn = function (c, clip, box, o) {
    const r = HD.rng(o.seed), n = HD.noise1(o.seed + 5), [x0, y0, x1, y1] = box, st = o.step ?? 3;
    const du = Math.cos(o.angle), dv = Math.sin(o.angle), pu = -dv, pv = du;
    const cs = [[x0, y0], [x1, y0], [x0, y1], [x1, y1]], offs = cs.map(([x, y]) => x * pu + y * pv), ts = cs.map(([x, y]) => x * du + y * dv);
    const oMax = Math.max(...offs), tMin = Math.min(...ts), tMax = Math.max(...ts);
    c.save(); if (clip) { HD.pathOf(c, clip); c.clip(); }
    c.strokeStyle = o.color || HD.opts.ink; c.lineCap = c.lineJoin = "round";
    for (let off = Math.min(...offs) + r() * o.sp, li = 0; off < oMax; off += o.sp * (.75 + r() * .5), li++) {
      c.lineWidth = o.w * (.7 + r() * .6); c.globalAlpha = o.alpha * (.65 + r() * .35);
      c.beginPath(); let on = false;
      for (let t = tMin; t <= tMax; t += st) {
        const k = off + (n(li * 3.1 + t * .02) - .5) * (o.wob ?? 1.2), x = pu * k + du * t, y = pv * k + dv * t;
        if (x < x0 - 2 || x > x1 + 2 || y < y0 - 2 || y > y1 + 2) { on = false; continue; }
        const draw = (!o.tone || o.tone(x, y) > (o.thr ?? .5) + (n(li * 7.7 + t * .06 + 99) - .5) * (o.rag ?? .3)) && r() > (o.gaps ?? .008);
        if (draw) { on ? c.lineTo(x, y) : c.moveTo(x, y); on = true; } else on = false;
      }
      c.stroke();
    }
    c.restore(); c.globalAlpha = 1;
  };
  // 实心物体：先垫一块和页面同纹的纸，挡住后面的线，再在上面画。poly 是点列或多边形数组
  HD.under = function (c, poly) {
    c.save(); HD.pathOf(c, poly); c.setTransform(1, 0, 0, 1, 0, 0);
    c.globalCompositeOperation = "source-over"; c.globalAlpha = 1; c.fillStyle = HD.paperPattern(c, HD.paper.bg, c.canvas); c.fill(); c.restore();
  };
  // 自带纸底的画布不能擦成透明：纸的深坑里改成补回纸色（画布本身是 normal 混合时用这个，线稿层用 paperize）
  HD.paperizeN = function (cv, a = .5) {
    const c = cv.getContext("2d"); c.save(); c.setTransform(1, 0, 0, 1, 0, 0);
    c.globalCompositeOperation = "source-atop"; c.globalAlpha = a; c.fillStyle = HD.paperPattern(c, HD.paper.pit, cv); c.fillRect(0, 0, cv.width, cv.height); c.restore();
  };
  // 画面四边不画死：返回一张小遮罩，边缘按噪声一截截淡回纸里，顶上淡得更慢。W,H 是场景的 CSS 像素
  HD.edgeMask = function (W, H) {
    const q = 4, w = Math.ceil(W / q), h = Math.ceil(H / q), cv = document.createElement("canvas"); cv.width = w; cv.height = h;
    const c = cv.getContext("2d"), D = c.createImageData(w, h), n = HD.noise1(91), m = HD.noise1(92), F = 30 / q, Ft = 64 / q, A = 20 / q;
    const wob = (o, t) => (n(o + t * .05) - .5) * A * 2 + (m(o + t * .3) - .5) * A * .7;
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const e = Math.min((x + wob(0, y)) / F, (w - 1 - x + wob(150, y)) / F, (y + wob(300, x)) / Ft, (h - 1 - y + wob(450, x)) / F);
      const v = Math.min(1, Math.max(0, e)); D.data[(y * w + x) * 4 + 3] = (1 - v * v * (3 - 2 * v)) * 255;
    }
    c.putImageData(D, 0, 0); return cv;
  };
  // 把画布按场景遮罩淡进纸里：mask 来自 edgeMask(W, H)，画布在场景里的位置取 style.left/top，W、H 是场景的 CSS 像素
  HD.fade = function (cv, mask, W, H) {
    const c = cv.getContext("2d"), L = parseFloat(cv.style.left) || 0, T = parseFloat(cv.style.top) || 0, D = HD.DPR;
    c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.globalCompositeOperation = "destination-out";
    c.drawImage(mask, -L * D, -T * D, W * D, H * D); c.restore();
  };
  // 山脊：几层噪声叠出来的起伏，返回 x -> y。R:{y 基线, amp 起伏, seed}
  HD.ridgeFn = function (R) {
    const a = HD.noise1(R.seed), b = HD.noise1(R.seed + 1), d = HD.noise1(R.seed + 2);
    return x => R.y - R.amp * (1.6 * (.6 * a(x * .0042 + 3) + .28 * b(x * .013 + 7) + .12 * d(x * .05)) - .3);
  };
  // 雾：把 y0..y1 一段往下一层层擦淡（destination-out），yb 是擦到的底，a 是最深处擦掉多少
  HD.mist = function (c, y0, y1, X0, X1, yb, a = .82) {
    c.save(); c.globalCompositeOperation = "destination-out";
    const gr = c.createLinearGradient(0, y0, 0, y1); gr.addColorStop(0, "rgba(0,0,0,0)"); gr.addColorStop(1, `rgba(0,0,0,${a})`);
    c.fillStyle = gr; c.fillRect(X0, y0, X1 - X0, yb - y0); c.restore();
  };
  // 一根杆：把线段 a→b 加宽成宽 w 的四边形（给 under/填色用）
  HD.strip = function (a, b, w) { const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1, nx = -dy / L * w / 2, ny = dx / L * w / 2; return [[a[0] + nx, a[1] + ny], [b[0] + nx, b[1] + ny], [b[0] - nx, b[1] - ny], [a[0] - nx, a[1] - ny]]; }
  // 云：自带纸底，一圈鼓包的上沿，底下阴面排线。(x,y) 云底中心，sc 大小（宽约 200*sc）
  HD.cloud = function (c, x, y, sc, seed) {
    const r = HD.rng(seed), n = 4 + Math.floor(r() * 3), w = 200 * sc, out = [], tops = [];
    const bumps = Array.from({length: n}, (_, i) => { const t = (i + .5) / n, R = (19 + r() * 11 + Math.sin(t * Math.PI) * 21) * sc; return [x - w / 2 + t * w, y - Math.sin(t * Math.PI) * 13 * sc - R * .15, R]; });
    const base = y + 13 * sc, [fx0, , fR] = bumps[0], [lx, , lR] = bumps[n - 1];
    out.push([fx0 - fR * .85, base]);
    bumps.forEach(([bx, by, R], i) => {
      const a0 = i ? Math.PI * 1.1 : Math.PI * .92, a1 = i === n - 1 ? Math.PI * 2.08 : Math.PI * 1.9, seg = [];
      for (let q = 0; q <= 10; q++) { const a = a0 + (a1 - a0) * q / 10; seg.push([bx + Math.cos(a) * R, by + Math.sin(a) * R]); }
      out.push(...seg); tops.push(seg);
    });
    out.push([lx + lR * .85, base]);
    const bot = []; for (let px = lx + lR * .85; px > fx0 - fR * .85; px -= 12 * sc) bot.push([px, base + Math.sin(px * .07 + seed) * 1.6 * sc]);
    out.push(...bot);
    HD.under(c, out);
    c.save(); c.fillStyle = "rgba(255,253,248,.55)"; HD.pathOf(c, out); c.fill(); c.restore();
    const bb = HD.bounds(out);
    HD.pencil(c, out, bb, {seed: seed + 1, color: "#a3b8d2", angle: -1.08, len: 9 * sc, w: 1.3 * sc, density: .5 / (sc * sc), tooth: .5, alpha: (px, py) => .8 * Math.max(0, Math.min(1, (py - (y - 12 * sc)) / (26 * sc)))});
    HD.hatchIn(c, out, [bb[0], y - 2 * sc, bb[2], base + 2], {seed: seed + 2, angle: -.12, sp: 2.6 * sc, w: .55 * sc, alpha: .5, color: "#5d6f8c", tone: (px, py) => (py - y) / (13 * sc), thr: .35, rag: .5});
    tops.forEach((sg, i) => HD.pen(c, sg, {w: 1.3 * sc, seed: seed + 10 + i, jit: .35}));
    HD.pen(c, [[lx + lR * .85, base], ...bot], {w: .8 * sc, seed: seed + 30, jit: .5, alpha: .45});
    // 鼓包相接处向里卷一小笔
    for (let i = 1; i < n; i += 2) { const [bx, by, R] = bumps[i]; const a = Math.PI * 1.25; HD.pen(c, [[bx + Math.cos(a) * R * .55, by + Math.sin(a) * R * .55 + 6 * sc], [bx + Math.cos(a + .5) * R * .5, by + Math.sin(a + .5) * R * .5 + 8 * sc], [bx + Math.cos(a + 1) * R * .38, by + Math.sin(a + 1) * R * .38 + 9 * sc]], {w: .8 * sc, seed: seed + 40 + i, jit: .2, alpha: .4}); }
  };
  // 松树：一根干加四层锯齿枝，从下往上画，上一层的纸底盖住下一层的线。(x,y) 是树根，高约 84*sc
  HD.pine = function (c, x, y, sc, seed) {
    const top = y - 84 * sc, tiers = 4;
    HD.under(c, [[x - 1.6 * sc, y], [x - 1.6 * sc, y - 22 * sc], [x + 1.6 * sc, y - 22 * sc], [x + 1.6 * sc, y]]);
    HD.pen(c, [[x, y], [x, y - 22 * sc]], {w: 2.2 * sc, seed, jit: .3});
    for (let i = tiers - 1; i >= 0; i--) { // 从下往上：上一层的纸底盖住下一层的线
      const ya = top + i * 15 * sc, yb = ya + 30 * sc, hw = (9 + i * 6.5) * sc, rr = HD.rng(seed + i), pts = [[x, ya], [x + hw * .5, ya + (yb - ya) * .55], [x + hw, yb]];
      const zz = 5 + i; for (let q = 1; q < zz; q++) pts.push([x + hw - 2 * hw * q / zz, yb - (q % 2 ? 4.5 : 0) * sc - rr() * 1.5 * sc]);
      pts.push([x - hw, yb], [x - hw * .5, ya + (yb - ya) * .55]);
      HD.under(c, pts);
      HD.pencil(c, pts, [x - hw, ya, x + hw, yb], {seed: seed + 10 + i, color: "#79a26d", angle: -1.08, len: 7 * sc, w: 1.3 * sc, density: 1 / (sc * sc), tooth: .45, alpha: px => px > x ? .9 : .6});
      HD.hatchIn(c, pts, [x - hw, ya, x + hw, yb], {seed: seed + 20 + i, angle: 1.2, sp: 2.4 * sc, w: .65 * sc, alpha: .65, tone: (px, py) => (px - x) / hw * .8 + (py - ya) / (yb - ya) * .5, thr: .4});
      HD.pen(c, pts, {closed: true, w: 1.1 * sc, seed: seed + 30 + i, jit: .3});
    }
  };
  // 灌木：半圆的一丛，彩铅打绿、右下排线。(x,y) 是底，R 半径
  HD.bush = function (c, x, y, R, seed) {
    const n = HD.noise1(seed), pts = [];
    for (let i = 0; i < 26; i++) { const a = Math.PI + i / 25 * Math.PI, rr = R * (1 + .14 * Math.sin(a * 6 + seed) + (n(i * .5) - .5) * .2); pts.push([x + Math.cos(a) * rr * 1.25, y + Math.sin(a) * rr]); }
    HD.under(c, pts);
    HD.pencil(c, pts, HD.bounds(pts), {seed: seed + 1, color: "#86ab73", angle: -1.08, len: 6 * R / 14, w: 1.2, density: 1, tooth: .45, alpha: () => .8});
    HD.hatchIn(c, pts, HD.bounds(pts), {seed: seed + 2, angle: 1.1, sp: 2.3, w: .6, alpha: .6, tone: (px, py) => (px - x) / R * .7 + (py - y + R) / R * .4, thr: .55});
    HD.pen(c, pts, {w: 1, seed: seed + 3, jit: .3});
  };
  // 草丛：三笔短草。(tx,ty) 是根，sz 大小
  HD.tuft = function (c, tx, ty, sz, sd) {
    const rr = HD.rng(sd);
    for (let q = 0; q < 3; q++) { const a = -Math.PI / 2 + (rr() - .5) * 1.1, L = (4 + rr() * 6) * sz, bx = tx + (q - 1) * 1.7 * sz; HD.pen(c, [[bx, ty], [bx + Math.cos(a) * L, ty + Math.sin(a) * L]], {w: .8 * sz, seed: sd + q, jit: .15, color: "#3d5c34", alpha: .85}); }
  };
  // 河里的石头：半露出水面，两边各一道水纹。(x,y) 是水面位置，R 大小
  HD.rock = function (c, x, y, R, seed) {
    const n = HD.noise1(seed), pts = [];
    for (let i = 0; i < 16; i++) { const a = i / 16 * Math.PI * 2, rr = R * (.82 + n(i * .7) * .36); pts.push([x + Math.cos(a) * rr * 1.25, Math.min(y + R * .3, y + Math.sin(a) * rr * .8)]); }
    const bb = HD.bounds(pts);
    HD.under(c, pts);
    HD.pencil(c, pts, bb, {seed: seed + 1, color: "#a99e8c", angle: -1.08, len: R * .4, w: 1.3, density: 1.2 * 22 / R, tooth: .5, alpha: (px, py) => .45 + .4 * ((px - bb[0]) / (bb[2] - bb[0]))});
    HD.hatchIn(c, pts, bb, {seed: seed + 2, angle: 1.0, sp: 2.6, w: .65, alpha: .6, tone: (px, py) => (px - x) / R * .6 + (py - y + R * .6) / R * .6, thr: .55});
    HD.pen(c, pts, {closed: true, w: 1.3, seed: seed + 3, jit: .4});
    HD.pen(c, [[x - R * 1.5, y + R * .36], [x - R * 1.2, y + R * .34]], {w: .9, seed: seed + 4, jit: .2, alpha: .7, color: "#3d5d78"});
    HD.pen(c, [[x + R * 1.2, y + R * .38], [x + R * 1.6, y + R * .36]], {w: .9, seed: seed + 5, jit: .2, alpha: .7, color: "#3d5d78"});
  };

  root.HandDrawn = HD;
})(window);
