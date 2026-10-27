/*
 * Input: 成对图（底层 base + 揭示层 top，同构图、像素对齐）、页面里带 data-scene 的舞台、可选热点与吊灯坐标
 * Output: 固定全屏 WebGL 画布：指针光 / 吊灯 / 空闲巡游驱动的墨迹场，墨迹内显示揭示层；热点说明牌按光的位置浮出
 * Pos: layered-reveal 手法的引擎，无依赖；起手页 index.html 用 LayeredReveal.mount() 调用
 */
(function (root) {
'use strict';

// 默认值 = 已验证页面（2026-10-23）的数值。是锚点，不是配方。
const DEF = {
  imageSize: [1536, 1024],  // 成对图原图像素；热点、吊灯坐标都按这个写
  inkRes: [512, 320],       // 墨迹场分辨率，低一点更柔
  dprMax: 1.5,
  bg: [0.024, 0.031, 0.055],     // 有色深蓝黑底
  baseTint: [0.80, 0.84, 0.92],  // 底层混向的冷灰蓝
  baseMix: 0.42,                 // 底层混合系数；投影增亮档用 0.65
  baseGamma: 1.35,               // 保留底层自身明暗：pow(lum, 1.35)
  topGain: 1.3,                  // 揭示层提亮
  warm: [0.95, 0.60, 0.25],      // 光边暖色
  decay: 0.993, fade: 0.0012,    // 墨迹每 60fps 帧的保留比例与减量 → 痕迹多久褪（按真实时间折算，低帧率不拖尾）
  curl: 0.0016, push: 0.6,       // 卷曲噪声平流强度、指针速度推墨强度
  thresh: [0.22, 0.62],          // 墨迹显影阈值（smoothstep 两端）
  edgeNoise: 0.38,               // fbm 扰动阈值 → 边缘像水墨
  edgeDark: [0.12, 0.28],        // 光边压暗（无图 / 有图）
  lampLevel: 0.9, lampRadius: 230, // 固定吊灯亮度、半径（原图像素）
  follow: 0.91,                  // 光跟手的缓动，越接近 1 越慢
  idleMs: 4000, tourMs: 3200,    // 空闲多久开始巡游、每个热点停多久
  fadeOutMs: 600, fadeInMs: 900, // 换章：场景图化回底纹、再化入
  pinRadius: 0.2,                // 热点感应半径（占屏高）
  narrowAt: 760,                 // 窄屏：图放下半屏，按焦点横向取景
  stages: '[data-scene]',
  onFrame: null                  // ({scene, stage, light:[x,y], pin, seen, lit}) => void
};

function mount(canvas, scenes, opt) {
  const o = Object.assign({}, DEF, opt || {});
  const [IW, IH] = o.imageSize;
  const W = () => innerWidth, H = () => innerHeight, narrow = () => innerWidth <= o.narrowAt;
  const rm = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const stages = [...document.querySelectorAll(o.stages)];
  stages.forEach(st => { st._sc = scenes[st.dataset.scene]; });
  const f = x => (+x).toFixed(5), v3 = a => `vec3(${a.map(f).join(',')})`;

  // ── 图片位置：桌面 cover，窄屏放在下半屏并以焦点横向取景
  function geo(sc) {
    const w = W(), h = H(); let k, ox, oy;
    if (narrow()) {
      k = h * 0.46 / IH; const fx = sc.fxNow ?? sc.fx ?? IW / 2;
      ox = Math.min(0, Math.max(w - IW * k, w / 2 - fx * k)); oy = h - IH * k - h * 0.16;
    } else {
      k = Math.max(w / IW, h / IH) * 1.04;
      ox = sc.align === 'right' ? w - IW * k + w * 0.01 : sc.align === 'left' ? -w * 0.05 : (w - IW * k) / 2;
      oy = (h - IH * k) * (sc.vy ?? 0.5);
    }
    return { k, ox, oy };
  }
  function placePins() {
    stages.forEach(st => { const sc = st._sc; if (!sc || !sc.pins) return; const g = geo(sc);
      sc.pins.forEach(p => { p.lx = g.ox + p.x * g.k; p.ly = g.oy + p.y * g.k;
        if (p.el) { p.el.style.left = p.lx + 'px'; p.el.style.top = p.ly + 'px'; } }); });
  }

  // ── 当前舞台：视口中线所在的 data-scene 元素
  let want = null, wantStage = null, cur = null, curStage = null, lit = 0;
  function pick() {
    const mid = H() / 2;
    for (const st of stages) { const r = st.getBoundingClientRect();
      if (r.top <= mid && r.bottom >= mid) { want = st.dataset.scene; wantStage = st; return; } }
  }
  addEventListener('scroll', pick, { passive: true }); pick();
  if (!want && stages[0]) { want = stages[0].dataset.scene; wantStage = stages[0]; }

  const gl = canvas.getContext('webgl2', { antialias: false, premultipliedAlpha: false });
  // ── 无 WebGL：舞台直接铺揭示层，说明牌全显
  if (!gl) {
    document.documentElement.classList.add('lr-nogl');
    stages.forEach(st => { const sc = st._sc; if (!sc) return;
      if (sc.top) st.style.background = `linear-gradient(rgba(6,8,14,.5),rgba(6,8,14,.5)),url(${sc.top}) center/cover`;
      (sc.pins || []).forEach(p => p.el && p.el.classList.add('on', 'seen')); });
    placePins(); addEventListener('resize', placePins);
    return { setLit() {}, geo, still() {} };
  }

  const half = !!gl.getExtension('EXT_color_buffer_float');
  const V = `#version 300 es
in vec2 p;out vec2 uv;void main(){uv=p*.5+.5;gl_Position=vec4(p,0,1);}`;
  const NOISE = `vec2 h2(vec2 i){i=vec2(dot(i,vec2(127.1,311.7)),dot(i,vec2(269.5,183.3)));return fract(sin(i)*43758.5453)*2.-1.;}
float n2(vec2 x){vec2 i=floor(x),f=fract(x),u=f*f*(3.-2.*f);return mix(mix(dot(h2(i),f),dot(h2(i+vec2(1,0)),f-vec2(1,0)),u.x),mix(dot(h2(i+vec2(0,1)),f-vec2(0,1)),dot(h2(i+vec2(1,1)),f-vec2(1,1)),u.x),u.y);}
float fbm(vec2 x){float a=.5,r=0.;for(int i=0;i<5;i++){r+=a*n2(x);x=x*2.03+17.;a*=.5;}return r;}`;
  // 墨：curl noise 平流 + 扩散 + 衰减；指针一盏灯，另有最多四盏固定吊灯（竖向椭圆）
  const ADV = `#version 300 es
precision highp float;in vec2 uv;out vec4 o;uniform sampler2D d;uniform vec2 m,mv;uniform float t,asp,lamp,px,lr,dec,fd;uniform vec4 L[4];
${NOISE}
void main(){
 vec2 q=uv*vec2(asp,1.)*2.2+t*.04,e=vec2(.01,0);
 vec2 c=vec2(n2(q+e.yx)-n2(q-e.yx),-(n2(q+e)-n2(q-e)))/(2.*e.x);
 vec2 dm=(uv-m)*vec2(asp,1.);float g=exp(-dot(dm,dm)*lr);
 vec2 a=uv-(c*${f(o.curl)}+mv*${f(o.push)}*g);
 float k=texture(d,a).r*.4+(texture(d,a+vec2(px,0)).r+texture(d,a-vec2(px,0)).r+texture(d,a+vec2(0,px)).r+texture(d,a-vec2(0,px)).r)*.15;
 k=k*dec-fd;
 k=max(k,lamp*g);
 for(int i=0;i<4;i++){vec2 z=(uv-L[i].xy)*vec2(asp,.5);k=max(k,L[i].z*exp(-dot(z,z)*L[i].w)*(.92+.08*n2(uv*9.+t*.3+float(i))));}
 o=vec4(clamp(k,0.,1.),0,0,1);}`;
  const SHOW = `#version 300 es
precision highp float;in vec2 uv;out vec4 o;uniform sampler2D d,rel,real;uniform vec2 res,org,isz;uniform float t,asp,mode,ia;
${NOISE}
void main(){
 vec2 p=vec2(uv.x*res.x,(1.-uv.y)*res.y);vec2 iu=(p-org)/isz;
 float ins=step(0.,iu.x)*step(iu.x,1.)*step(0.,iu.y)*step(iu.y,1.);
 vec3 bg=${v3(o.bg)};
 vec2 w=uv*vec2(asp,1.);
 // 底纹始终是暗色大理石；场景图按羽化边与 ia 叠上去，换章时化入化出
 float v=fbm(w*1.6+fbm(w*3.)*.8);float vein=1.-smoothstep(.0,.05,abs(v-.05));
 vec3 relief=bg+vec3(.012,.014,.02)*(v+.5)+vec3(.02,.024,.03)*vein;
 vec3 site=relief*1.3+vec3(.045,.032,.017)+vec3(.04,.028,.014)*vein;
 float a=0.;
 if(mode>.5){
  vec3 r=texture(rel,iu).rgb;float lum=pow(dot(r,vec3(.3,.59,.11)),${f(o.baseGamma)});
  float fe=smoothstep(0.,.12,iu.y)*smoothstep(1.,.84,iu.y)*smoothstep(0.,.05,iu.x)*smoothstep(1.,.96,iu.x);
  a=ins*fe*ia;
  relief=mix(relief,mix(bg,${v3(o.baseTint)},lum*${f(o.baseMix)}),a);
  site=mix(site,texture(real,iu).rgb*${f(o.topGain)},a);
 }
 float dk=texture(d,uv).r;
 float n=fbm(w*4.+vec2(fbm(w*2.+t*.05),fbm(w*2.-t*.04))*1.2+t*.02);
 float fine=n2(w*38.+t*.1)*.5+.5;
 float m=smoothstep(${f(o.thresh[0])},${f(o.thresh[1])},dk+n*${f(o.edgeNoise)}+(fine-.5)*.06*dk);
 float edge=smoothstep(.02,.3,m)*(1.-smoothstep(.3,.75,m));
 vec3 col=mix(relief,site,m);
 col*=1.-edge*mix(${f(o.edgeDark[0])},${f(o.edgeDark[1])},a);
 col+=${v3(o.warm)}*edge*.045+vec3(.9,.62,.3)*m*.03;
 col+=(fract(sin(dot(p+t,vec2(12.9898,78.233)))*43758.5453)-.5)*.025;
 o=vec4(col,1);}`;

  function prog(src) {
    const mk = (t, s) => { const x = gl.createShader(t); gl.shaderSource(x, s); gl.compileShader(x);
      if (!gl.getShaderParameter(x, gl.COMPILE_STATUS)) console.error(gl.getShaderInfoLog(x)); return x; };
    const p = gl.createProgram(); gl.attachShader(p, mk(gl.VERTEX_SHADER, V)); gl.attachShader(p, mk(gl.FRAGMENT_SHADER, src));
    gl.bindAttribLocation(p, 0, 'p'); gl.linkProgram(p);
    const u = {}; return { p, u: n => u[n] ??= gl.getUniformLocation(p, n) };
  }
  const pa = prog(ADV), ps = prog(SHOW);
  gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
  function tex(w, h, img) {
    const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
    if (img) gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
    else gl.texImage2D(gl.TEXTURE_2D, 0, half ? gl.RGBA16F : gl.RGBA8, w, h, 0, gl.RGBA, half ? gl.HALF_FLOAT : gl.UNSIGNED_BYTE, null);
    [gl.TEXTURE_MIN_FILTER, gl.TEXTURE_MAG_FILTER].forEach(x => gl.texParameteri(gl.TEXTURE_2D, x, gl.LINEAR));
    [gl.TEXTURE_WRAP_S, gl.TEXTURE_WRAP_T].forEach(x => gl.texParameteri(gl.TEXTURE_2D, x, gl.CLAMP_TO_EDGE));
    return t;
  }
  const N = o.inkRes;
  function fbo() { const t = tex(N[0], N[1]); const fb = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0); return { t, f: fb }; }
  let A = fbo(), B = fbo();
  function clearInk() { [A, B].forEach(x => { gl.bindFramebuffer(gl.FRAMEBUFFER, x.f); gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT); }); }

  let DT = 16.7, m = [0.62, 0.5], target = [0.62, 0.5], mv = [0, 0], tm = 0, idle = 0, tour = 0, last = 0, lamp = 0;
  let G = { k: 1, ox: 0, oy: 0 }, stTop = 0, ia = 0;
  const Lz = [0, 0, 0, 0], seen = new Set();

  // 吊灯：前 lit 盏渐亮；坐标换成屏幕 uv，半径换成高斯系数
  function lampsU(sc) {
    const a = new Float32Array(16); if (!sc.lamps) return a;
    sc.lamps.slice(0, 4).forEach((z, i) => {
      Lz[i] += ((i < lit ? o.lampLevel : 0) - Lz[i]) * (1 - Math.pow(0.95, DT / 16.7));
      const sx = G.ox + z.x * G.k, sy = stTop + G.oy + (z.y - 60) * G.k, r = o.lampRadius * G.k / H();
      a.set([sx / W(), 1 - sy / H(), Lz[i], 0.693 / (r * r)], i * 4);
    });
    return a;
  }
  function step(pt, pmv, l, sc) {
    gl.bindFramebuffer(gl.FRAMEBUFFER, B.f); gl.viewport(0, 0, N[0], N[1]); gl.useProgram(pa.p);
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, A.t); gl.uniform1i(pa.u('d'), 0);
    gl.uniform2f(pa.u('m'), pt[0], pt[1]); gl.uniform2f(pa.u('mv'), pmv[0], pmv[1]);
    gl.uniform1f(pa.u('t'), tm); gl.uniform1f(pa.u('asp'), W() / H()); gl.uniform1f(pa.u('lamp'), l);
    const lr = sc.lr ?? 10; gl.uniform1f(pa.u('lr'), sc.T ? 10 + (lr - 10) * ia : lr);
    const fr = DT / 16.7; gl.uniform1f(pa.u('dec'), Math.pow(o.decay, fr)); gl.uniform1f(pa.u('fd'), o.fade * fr);
    gl.uniform1f(pa.u('px'), 1.2 / N[0]); gl.uniform4fv(pa.u('L[0]'), lampsU(sc));
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4); [A, B] = [B, A];
  }
  function show(sc) {
    gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.viewport(0, 0, canvas.width, canvas.height); gl.useProgram(ps.p);
    [[A.t, 'd'], [sc.T ? sc.T.base : A.t, 'rel'], [sc.T ? sc.T.top : A.t, 'real']].forEach(([t, n], i) => {
      gl.activeTexture(gl.TEXTURE0 + i); gl.bindTexture(gl.TEXTURE_2D, t); gl.uniform1i(ps.u(n), i); });
    gl.uniform2f(ps.u('res'), W(), H()); gl.uniform2f(ps.u('org'), G.ox, G.oy + stTop); gl.uniform2f(ps.u('isz'), IW * G.k, IH * G.k);
    gl.uniform1f(ps.u('t'), tm); gl.uniform1f(ps.u('asp'), W() / H()); gl.uniform1f(ps.u('mode'), sc.T ? 1 : 0); gl.uniform1f(ps.u('ia'), ia);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }
  function size() { const d = Math.min(devicePixelRatio, o.dprMax); canvas.width = Math.round(W() * d); canvas.height = Math.round(H() * d); placePins(); }

  // 一次只亮离光最近的一张说明牌；照过的留暗点
  function updatePins(sc, lx, ly) {
    let best = null;
    if (sc.pins && curStage) { let bd = H() * o.pinRadius;
      sc.pins.forEach(p => { const d = Math.hypot(p.lx - lx, p.ly + stTop - ly); if (d < bd) { bd = d; best = p; } });
      sc.pins.forEach(p => { const on = p === best; if (!p.el) return; p.el.classList.toggle('on', on);
        if (on) { p.el.classList.add('seen'); seen.add(p); } }); }
    if (o.onFrame) o.onFrame({ scene: cur, stage: curStage, light: [lx, ly], pin: best,
      seen: sc.pins ? sc.pins.filter(p => seen.has(p)).length : 0, lit });
  }

  // 切场景：场景图先化回大理石底，再换图化入；墨迹保留，光不断
  function sync(dt) {
    if (want === cur) { curStage = wantStage; if (scenes[cur].T) ia = rm ? 1 : Math.min(1, ia + dt / o.fadeInMs); return; }
    if (cur === null || !scenes[cur].T || rm) { cur = want; curStage = wantStage; tour = 0; ia = rm && scenes[cur].T ? 1 : 0; return; }
    ia -= dt / o.fadeOutMs; if (ia <= 0) { ia = 0; cur = want; curStage = wantStage; tour = 0; }
  }
  function frameGeo() {
    const sc = scenes[cur];
    if (sc.lamps && narrow()) { const z = sc.lamps[Math.max(0, lit - 1)]; sc.fxNow = (sc.fxNow ?? z.x) + (z.x - (sc.fxNow ?? z.x)) * 0.05; }
    G = geo(sc); stTop = curStage && sc.T ? curStage.getBoundingClientRect().top : 0;
  }
  addEventListener('pointermove', e => { target = [e.clientX / W(), 1 - e.clientY / H()]; idle = 0; });
  addEventListener('pointerdown', e => { target = [e.clientX / W(), 1 - e.clientY / H()]; idle = 0; });

  function loop(now) {
    const dt = Math.min(now - (last || now), 50); DT = dt; last = now; tm += dt / 1000; idle += dt; sync(dt);
    if (cur) { const sc = scenes[cur]; frameGeo(); lamp = Math.min(1, lamp + dt / 900);
      // 空闲后自动巡游：有热点照热点，有吊灯照已亮的区，否则缓慢漂移
      if (idle > o.idleMs) { tour += dt;
        const pts = sc.pins ? sc.pins.map(p => [p.lx, p.ly + stTop])
          : sc.lamps ? sc.lamps.slice(0, Math.max(1, lit)).map(z => [G.ox + z.x * G.k, stTop + G.oy + z.y * G.k]) : null;
        if (pts) { const q = pts[Math.floor(tour / o.tourMs) % pts.length]; target = [q[0] / W(), 1 - q[1] / H()]; }
        else target = [0.5 + 0.3 * Math.sin(tm * 0.13), 0.5 + 0.22 * Math.sin(tm * 0.21 + 1)]; }
      const ef = 1 - Math.pow(o.follow, dt / 16.7), nx = m[0] + (target[0] - m[0]) * ef, ny = m[1] + (target[1] - m[1]) * ef;
      mv = [nx - m[0], ny - m[1]]; m = [nx, ny];
      step(m, mv, lamp * (0.6 + 0.35 * (sc.T ? ia : 0)), sc); show(sc);
      updatePins(sc, m[0] * W(), (1 - m[1]) * H()); }
    requestAnimationFrame(loop);
  }
  // 减少动态：照亮全部热点与吊灯，画一帧
  function still() {
    const sc = scenes[cur]; if (!sc) return; frameGeo(); clearInk();
    for (let r = 0; r < 40; r++) {
      (sc.pins || []).forEach(p => step([p.lx / W(), 1 - (p.ly + stTop) / H()], [0, 0], 0.8, sc));
      if (!sc.pins) step([0.5, 0.5], [0, 0], sc.T ? 0 : 0.5, sc);
    }
    show(sc); (sc.pins || []).forEach(p => p.el && p.el.classList.add('on', 'seen'));
  }

  addEventListener('resize', () => { size(); if (rm) still(); });
  const load = src => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.onerror = () => r(null); i.src = src; });
  const srcs = [...new Set(Object.values(scenes).flatMap(s => s.base ? [s.base, s.top] : []))];
  Promise.all(srcs.map(load)).then(imgs => {
    const T = {}; srcs.forEach((s, i) => { if (imgs[i]) T[s] = tex(0, 0, imgs[i]); });
    Object.values(scenes).forEach(s => { if (s.base && T[s.base] && T[s.top]) s.T = { base: T[s.base], top: T[s.top] }; });
    size();
    if (rm) { lit = 4; let q = 0;
      addEventListener('scroll', () => { if (q) return; q = requestAnimationFrame(() => { q = 0; sync(0); if (cur) still(); }); }, { passive: true });
      sync(0); still(); }
    else requestAnimationFrame(loop);
  });

  return {
    setLit(n) { lit = rm ? 4 : Math.max(0, Math.min(4, n)); }, // 签名：逐盏点亮
    geo, still, reducedMotion: rm
  };
}

root.LayeredReveal = { mount, defaults: DEF };
})(window);
