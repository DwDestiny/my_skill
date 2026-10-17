// ink.js · 渗印：印泥沿 A02 纸纤维从章外沿渗开，一次，结束转 <img> 并释放 WebGL 上下文
const FIBRE = new URL('../../assets/generated/A02-tracing-texture-512.jpg', import.meta.url).href;
const DEFAULTS = { size: 256, spread: 0.4, alpha: 0.45, duration: 800, fibre: FIBRE, color: null, rotate: 0, reduced: undefined, parent: null };
const clamp = (v) => Math.max(0, Math.min(1, v));

function sealColor(el) {
  const p = document.createElement('i'); p.style.cssText = 'position:absolute;visibility:hidden;color:var(--seal)';
  (el.parentElement || document.body).appendChild(p);
  const m = getComputedStyle(p).color.match(/[\d.]+/g).map(Number); p.remove();
  return [m[0] / 255, m[1] / 255, m[2] / 255];
}

const VS = 'attribute vec2 p;varying vec2 uv;void main(){uv=p*.5+.5;gl_Position=vec4(p,0.,1.);}';
const FS = `precision mediump float;varying vec2 uv;
uniform sampler2D fib;uniform float t,S,hw,spread,alpha,rot;uniform vec3 ink;
float box(vec2 p,vec2 b){vec2 d=abs(p)-b;return length(max(d,0.))+min(max(d.x,d.y),0.);}
void main(){
  vec2 p=(uv-.5)*S; float c=cos(rot),s=sin(rot); p=mat2(c,-s,s,c)*p;
  float r=hw*.08; float d=box(p,vec2(hw-r))-r;      // 章外沿，d>0 在章外
  float f=texture2D(fib,uv*(S/420.)*.55+.2).r;
  float g=texture2D(fib,uv*(S/420.)*1.7+vec2(.37,.11)).g;
  float fn=clamp(.5+(f-.725)*14.,0.,1.); float gn=clamp(.5+(g-.725)*14.,0.,1.);   // A02 纤维图对比很低，先拉开
  float reach=t*spread*hw*2.*(1.5+.5*gn);   // 沿纤维渗出距离（px）
  float e=d>0.?d:-d*4.;                               // 向章内只渗很浅
  float edge=e+(f-.725)*.6*hw*t*.1;
  float k=clamp(edge/(reach+1.),0.,1.);
  float halo=pow(1.-k,1.15)*mix(1.,.45+.55*fn,smoothstep(0.,.5,k));
  float a2=halo*alpha*1.04*smoothstep(0.,.2,t);
  gl_FragColor=vec4(ink*a2,a2);
}`;

// 目标可以是 HTML 或 SVG 元素：用包围盒除以宿主缩放，得到宿主局部坐标，不受 offsetLeft 与祖先 scale 影响
function geom(target, host) {
  const tr = target.getBoundingClientRect(), hr = host.getBoundingClientRect();
  const k = host.offsetWidth ? hr.width / host.offsetWidth : 1;
  const cs = getComputedStyle(target);
  const W = parseFloat(cs.width) || target.offsetWidth || tr.width / k;
  return { cx: (tr.left + tr.width / 2 - hr.left) / k - host.clientLeft, cy: (tr.top + tr.height / 2 - hr.top) / k - host.clientTop, W };
}
function place(cv, target, parent, g) {
  const host = parent || target.parentElement;
  cv.setAttribute('aria-hidden', 'true'); cv.classList.add('ink-bleed');
  Object.assign(cv.style, { position: 'absolute', left: g.cx + 'px', top: g.cy + 'px', transform: 'translate(-50%,-50%)', pointerEvents: 'none' });
  host.insertBefore(cv, target);   // 在章之下，印泥只压在底图一侧
}

export function bleed(target, o = {}) {
  const opts = { ...DEFAULTS, ...o };
  const g = geom(target, opts.parent || target.parentElement); const W = g.W;
  const S = Math.ceil(Math.max(opts.size, W * (1 + 4 * opts.spread) + 8));
  const rm = opts.reduced ?? matchMedia('(prefers-reduced-motion: reduce)').matches;
  const dpr = Math.min(2, devicePixelRatio || 1, 1024 / S);
  const color = opts.color || sealColor(target);
  const cv = document.createElement('canvas'); cv.width = cv.height = Math.round(S * dpr);
  cv.style.width = cv.style.height = S + 'px';
  const gl = cv.getContext('webgl', { premultipliedAlpha: true, preserveDrawingBuffer: true, antialias: false });
  const info = { size: S, canvas: cv.width };

  const finish = (src, lose) => new Promise((res) => {
    const still = new Image(); still.alt = ''; still.src = src;
    still.style.cssText = cv.style.cssText; still.className = 'ink-bleed'; still.setAttribute('aria-hidden', 'true');
    const done = () => { cv.replaceWith(still); lose && lose(); res({ ...info, img: still }); };
    still.onload = done; still.onerror = done;
  });

  if (!gl) {   // 无 WebGL：2D 软边近似终态
    const c2 = cv.getContext('2d'); c2.scale(dpr, dpr);
    c2.shadowColor = `rgba(${color.map((v) => Math.round(v * 255))},${opts.alpha})`; c2.shadowBlur = opts.spread * W * 0.6;
    c2.fillStyle = '#000'; c2.fillRect(S / 2 - W / 2, S / 2 - W / 2, W, W);
    c2.globalCompositeOperation = 'destination-out'; c2.shadowBlur = 0; c2.fillRect(S / 2 - W / 2, S / 2 - W / 2, W, W);
    place(cv, target, opts.parent, g); return finish(cv.toDataURL());
  }
  const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return s; };
  const pr = gl.createProgram(); gl.attachShader(pr, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(pr);
  if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) return Promise.resolve(info);
  gl.useProgram(pr);
  const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
  const loc = gl.getAttribLocation(pr, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  const U = (n) => gl.getUniformLocation(pr, n);

  return new Promise((resolve) => {
    const img = new Image();
    const go = (hasTex) => {
      if (hasTex) {
        const tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
        gl.generateMipmap(gl.TEXTURE_2D); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.REPEAT);
      }
      gl.uniform3f(U('ink'), color[0], color[1], color[2]);
      gl.uniform1f(U('S'), S); gl.uniform1f(U('hw'), W / 2); gl.uniform1f(U('spread'), opts.spread);
      gl.uniform1f(U('alpha'), opts.alpha); gl.uniform1f(U('rot'), (opts.rotate * Math.PI) / 180);
      gl.viewport(0, 0, cv.width, cv.height); gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
      const ut = U('t');
      const draw = (t) => { gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT); gl.uniform1f(ut, t); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4); };
      place(cv, target, opts.parent, g);
      const end = () => resolve(finish(cv.toDataURL(), () => gl.getExtension('WEBGL_lose_context')?.loseContext()));
      if (rm) { draw(1); end(); return; }
      const t0 = performance.now();
      const frame = (now) => {
        const t = clamp((now - t0) / opts.duration);
        draw(1 - Math.pow(1 - t, 3));
        t < 1 ? requestAnimationFrame(frame) : end();
      };
      requestAnimationFrame(frame);
    };
    img.onload = () => go(true); img.onerror = () => go(false);
    img.src = opts.fibre;
  });
}
