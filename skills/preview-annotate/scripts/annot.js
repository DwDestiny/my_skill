// 预览批注层：悬停高亮组件，点击写批注；批注按路由显示编号标记
// Input: 页面 DOM；/__annot 接口
// Output: Shadow DOM 里的批注按钮、高亮框、编号和列表；POST/DELETE /__annot
// Pos: server.mjs 注入到每个 HTML 页面末尾
(() => {
  const host = document.createElement('div');
  host.id = '__annot-host';
  host.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:2147483647';
  const root = host.attachShadow({ mode: 'open' });
  root.innerHTML = `<style>
    :host{all:initial}
    *{box-sizing:border-box;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
    .hl{position:fixed;border:2px solid #2442ff;background:rgb(36 66 255/8%);border-radius:3px;display:none;pointer-events:none}
    .tag{position:fixed;background:#2442ff;color:#fff;font:600 11px/1 monospace;padding:4px 6px;border-radius:3px;display:none;pointer-events:none;max-width:60vw;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
    .bar{position:fixed;right:16px;bottom:16px;display:flex;gap:8px;pointer-events:auto}
    button{cursor:pointer;border:0;border-radius:999px;padding:10px 16px;font-size:14px;font-weight:600;background:#17140f;color:#fff;box-shadow:0 6px 20px rgb(0 0 0/22%)}
    button.on{background:#2442ff}
    button.ghost{background:#fffcf7;color:#17140f;border:1px solid #d9ccb8;box-shadow:none}
    .pop,.panel{position:fixed;pointer-events:auto;background:#fffcf7;color:#17140f;border:1px solid #d9ccb8;border-radius:14px;box-shadow:0 12px 40px rgb(0 0 0/20%);padding:14px}
    .pop{width:min(340px,calc(100vw - 32px))}
    .pop p{margin:0 0 8px;font:12px/1.4 monospace;color:#6f665a;word-break:break-all}
    textarea{width:100%;min-height:96px;border:1px solid #d9ccb8;border-radius:10px;padding:10px;font-size:14px;resize:vertical;background:#fff;color:#17140f}
    textarea:focus{outline:2px solid #2442ff;border-color:transparent}
    .row{display:flex;justify-content:flex-end;gap:8px;margin-top:10px}
    .row button{padding:8px 14px;box-shadow:none;white-space:nowrap;flex-shrink:0}
    .pin{position:fixed;width:24px;height:24px;margin:-12px 0 0 -12px;border-radius:50%;background:#d4572a;color:#fff;font:700 12px/24px sans-serif;text-align:center;pointer-events:auto;cursor:pointer;box-shadow:0 2px 8px rgb(0 0 0/30%)}
    .panel{right:16px;bottom:72px;width:min(380px,calc(100vw - 32px));max-height:60vh;overflow:auto;display:none}
    .panel h4{margin:0 0 10px;font-size:15px}
    .item{border-top:1px solid #e6dac8;padding:10px 0;font-size:13px;line-height:1.5}
    .item small{display:block;color:#6f665a;font-family:monospace;word-break:break-all}
    .item a{color:#d4572a;cursor:pointer;font-size:12px;margin-left:8px}
    .hint{position:fixed;left:50%;top:12px;transform:translateX(-50%);display:none;background:#17140f;color:#fff;font-size:12px;padding:7px 14px;border-radius:999px;box-shadow:0 6px 20px rgb(0 0 0/22%);white-space:nowrap}
    .toast{position:fixed;right:16px;bottom:72px;display:none;background:#2f4a2a;color:#fff;font-size:13px;padding:9px 14px;border-radius:10px;box-shadow:0 6px 20px rgb(0 0 0/22%)}
    .toast.bad{background:#b3401b}
    .row .keys{margin-right:auto;align-self:center;font-size:12px;color:#6f665a}
    button:disabled{opacity:.6;cursor:default}
    .empty{color:#6f665a;font-size:13px}
  </style>
  <div class="hl"></div><div class="tag"></div><div class="pins"></div>
  <div class="panel"></div>
  <div class="hint">移动鼠标选组件 · 点击选中 · ↑ 选父级 ↓ 回子级 · Esc 取消</div>
  <div class="toast"></div>
  <div class="bar"><button class="ghost list">批注列表 <span class="n">0</span></button><button class="pick">选组件批注</button></div>`;
  document.documentElement.appendChild(host);

  const $ = (s) => root.querySelector(s);
  const hl = $('.hl'), tag = $('.tag'), pins = $('.pins'), panel = $('.panel'), pickBtn = $('.pick'), hint = $('.hint');
  // picking：选择模式；mouse：最后指针位置；depth：↑/↓ 调整到父级的层数；locked：已点选、正在写批注的组件
  let picking = false, pop = null, locked = null, depth = 0, all = [];
  const mouse = { x: 0, y: 0, inside: false };

  const ownEvent = (e) => e.composedPath().includes(host);

  // 生成稳定选择器：优先 id，否则按 class + nth-of-type 逐级向上
  function selectorOf(el) {
    const parts = [];
    while (el && el.nodeType === 1 && el !== document.body) {
      if (el.id && !/^\d/.test(el.id)) { parts.unshift('#' + CSS.escape(el.id)); break; }
      let s = el.tagName.toLowerCase();
      const cls = [...el.classList].filter((c) => !/^(semi-.*-(hover|active|focus)|is-|__)/.test(c)).slice(0, 3);
      if (cls.length) s += '.' + cls.map(CSS.escape).join('.');
      const sib = el.parentElement ? [...el.parentElement.children].filter((c) => c.tagName === el.tagName) : [];
      if (sib.length > 1) s += `:nth-of-type(${sib.indexOf(el) + 1})`;
      parts.unshift(s);
      el = el.parentElement;
    }
    return parts.join(' > ');
  }
  const label = (el) => el.tagName.toLowerCase() + (el.classList.length ? '.' + [...el.classList].slice(0, 2).join('.') : '');

  function box(el) {
    const r = el.getBoundingClientRect();
    // 组件完全滚出视口时不画框
    if (r.bottom < 0 || r.top > innerHeight || r.right < 0 || r.left > innerWidth || (!r.width && !r.height)) return hideBox();
    Object.assign(hl.style, { display: 'block', left: r.left + 'px', top: r.top + 'px', width: r.width + 'px', height: r.height + 'px' });
    tag.textContent = `${label(el)}  ${Math.round(r.width)}×${Math.round(r.height)}`;
    const tagTop = r.top - 24 >= 4 ? r.top - 24 : Math.min(r.bottom + 4, innerHeight - 24);
    Object.assign(tag.style, { display: 'block', left: Math.min(Math.max(4, r.left), innerWidth - tag.offsetWidth - 4) + 'px', top: tagTop + 'px' });
  }
  const hideBox = () => { hl.style.display = tag.style.display = 'none'; };

  // 指针下的组件，按 depth 上溯父级
  function target() {
    let el = document.elementFromPoint(mouse.x, mouse.y);
    if (!el || el === host || el === document.documentElement) return null;
    for (let i = 0; i < depth && el.parentElement && el.parentElement !== document.body; i++) el = el.parentElement;
    return el;
  }

  function placePop() {
    if (!pop || !locked) return;
    const w = pop.offsetWidth, h = pop.offsetHeight;
    let top, left;
    if (locked.isConnected) {
      const r = locked.getBoundingClientRect();
      top = r.bottom + 8;
      if (top + h > innerHeight - 8) top = r.top - h - 8;
      left = r.left;
    } else { top = parseFloat(pop.style.top) || 8; left = parseFloat(pop.style.left) || 8; }
    // 组件滚出视口时，批注框停在视口边缘，保持可输入
    pop.style.top = Math.min(Math.max(8, top), innerHeight - h - 8) + 'px';
    pop.style.left = Math.min(Math.max(8, left), innerWidth - w - 8) + 'px';
  }

  // 每帧按实际布局重画：覆盖滚动、平滑滚动、图片加载与动画引起的位移
  let loop = 0;
  function frame() {
    loop = 0;
    if (pop && locked) { locked.isConnected ? box(locked) : hideBox(); placePop(); }
    else if (picking && mouse.inside) { const el = target(); el ? box(el) : hideBox(); }
    else hideBox();
    if (picking || pop) loop = requestAnimationFrame(frame);
  }
  const kick = () => { if (!loop) loop = requestAnimationFrame(frame); };

  function setPicking(v) {
    picking = v; depth = 0;
    pickBtn.classList.toggle('on', v); pickBtn.textContent = v ? '取消选择（Esc）' : '选组件批注';
    hint.style.display = v ? 'block' : 'none';
    kick();
  }

  let toastTimer = 0;
  function toast(msg, bad = false) {
    const t = $('.toast'); t.textContent = msg; t.classList.toggle('bad', bad); t.style.display = 'block';
    clearTimeout(toastTimer); toastTimer = setTimeout(() => { t.style.display = 'none'; }, 1800);
  }

  function closePop() { pop?.remove(); pop = null; locked = null; kick(); }

  function openPop(el) {
    closePop();
    locked = el;
    const sel = selectorOf(el);
    pop = document.createElement('div'); pop.className = 'pop';
    pop.innerHTML = `<p></p><textarea placeholder="这个组件的问题或修改意见…"></textarea>
      <div class="row"><span class="keys">Enter 保存 · Shift+Enter 换行</span><button class="ghost cancel">取消</button><button class="ok">保存批注</button></div>`;
    pop.querySelector('p').textContent = `${location.pathname} · ${label(el)}`;
    root.appendChild(pop);
    placePop(); kick();
    const ta = pop.querySelector('textarea'); ta.focus({ preventScroll: true });
    pop.querySelector('.cancel').onclick = closePop;
    const ok = pop.querySelector('.ok');
    let saving = false;
    const submit = async () => {
      const comment = ta.value.trim(); if (!comment) return ta.focus();
      if (saving) return;
      saving = true; ok.disabled = true; ok.textContent = '保存中…';
      const r = el.getBoundingClientRect();
      const payload = {
        route: location.pathname + location.search, selector: sel, element: label(el),
        text: (el.innerText || el.getAttribute('aria-label') || el.getAttribute('alt') || '').replace(/\s+/g, ' ').trim().slice(0, 120),
        rect: { x: Math.round(r.left + scrollX), y: Math.round(r.top + scrollY), w: Math.round(r.width), h: Math.round(r.height) },
        viewport: `${innerWidth}×${innerHeight}`, comment,
      };
      let res = null;
      try { res = await fetch('/__annot', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(payload) }); } catch {}
      if (!res?.ok) { saving = false; ok.disabled = false; ok.textContent = '保存批注'; toast('保存失败，请重试', true); return; }
      closePop(); await refresh();
      toast(`已保存 · 本页第 ${here().length} 条`);
    };
    ok.onclick = submit;
    // Enter 保存，Shift+Enter 换行；中文输入法选词时的 Enter 不触发保存
    ta.addEventListener('keydown', (e) => {
      if (e.key !== 'Enter' || e.shiftKey || e.isComposing || e.keyCode === 229) return;
      e.preventDefault(); submit();
    });
  }

  // 选择模式下拦截点击，避免触发跳转；不拦截 touch，手机上仍可滚动
  for (const t of ['pointerdown', 'mousedown', 'mouseup', 'click']) {
    document.addEventListener(t, (e) => {
      if (!picking || ownEvent(e)) return;
      e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation();
      if (t === 'click') {
        Object.assign(mouse, { x: e.clientX, y: e.clientY, inside: true });
        const el = target() || e.target;
        setPicking(false); openPop(el);
      }
    }, { capture: true, passive: false });
  }
  document.addEventListener('pointermove', (e) => {
    if (e.pointerType === 'touch') return;
    Object.assign(mouse, { x: e.clientX, y: e.clientY, inside: !ownEvent(e) });
    if (mouse.inside) depth = depth && e.movementX ** 2 + e.movementY ** 2 > 36 ? 0 : depth;
  }, true);
  // 指针移出窗口时隐藏框
  document.documentElement.addEventListener('pointerleave', () => { mouse.inside = false; });
  addEventListener('blur', () => { mouse.inside = false; });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { if (pop) closePop(); else setPicking(false); return; }
    if (!picking) return;
    if (e.key === 'ArrowUp') { e.preventDefault(); depth++; }
    if (e.key === 'ArrowDown') { e.preventDefault(); depth = Math.max(0, depth - 1); }
  }, true);
  pickBtn.onclick = () => { closePop(); setPicking(!picking); };

  $('.list').onclick = () => { panel.style.display = panel.style.display === 'block' ? 'none' : 'block'; renderPanel(); };

  const here = () => all.filter((a) => a.route.split('?')[0] === location.pathname);

  function renderPanel() {
    $('.n').textContent = all.length;
    if (panel.style.display !== 'block') return;
    const cur = here();
    panel.innerHTML = `<h4>本页批注 ${cur.length} 条 · 全站 ${all.length} 条</h4>`;
    if (!all.length) panel.innerHTML += '<div class="empty">还没有批注。点右下角“选组件批注”开始。</div>';
    const list = [...cur, ...all.filter((a) => !cur.includes(a))];
    list.forEach((a) => {
      const d = document.createElement('div'); d.className = 'item';
      const n = cur.indexOf(a);
      d.innerHTML = `<b></b> <span></span><a class="go"></a><a class="del">删除</a><small></small>`;
      d.querySelector('b').textContent = n >= 0 ? `#${n + 1}` : '';
      d.querySelector('span').textContent = a.comment;
      d.querySelector('small').textContent = `${a.route} · ${a.element}${a.text ? ' · “' + a.text.slice(0, 40) + '”' : ''}`;
      const go = d.querySelector('.go');
      if (n >= 0) { go.textContent = '定位'; go.onclick = () => document.querySelector(a.selector)?.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
      else { go.textContent = '前往'; go.onclick = () => { location.href = a.route; }; }
      d.querySelector('.del').onclick = async () => {
        if (!confirm('删除这条批注？')) return;
        await fetch('/__annot', { method: 'DELETE', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ id: a.id }) });
        refresh();
      };
      panel.appendChild(d);
    });
  }

  function placePins() {
    pins.innerHTML = '';
    here().forEach((a, i) => {
      const el = document.querySelector(a.selector);
      let x, y;
      if (el) { const r = el.getBoundingClientRect(); if (!r.width && !r.height) return; x = r.left + 4; y = r.top + 4; }
      else { x = a.rect.x - scrollX; y = a.rect.y - scrollY; }
      if (y < -20 || y > innerHeight + 20) return;
      const p = document.createElement('div'); p.className = 'pin'; p.textContent = i + 1; p.title = a.comment;
      p.style.left = Math.max(12, x) + 'px'; p.style.top = Math.max(12, y) + 'px';
      p.onclick = () => { panel.style.display = 'block'; renderPanel(); };
      pins.appendChild(p);
    });
  }

  async function refresh() {
    try { all = await (await fetch('/__annot', { cache: 'no-store' })).json(); } catch { all = []; }
    renderPanel(); placePins();
  }

  let raf = 0;
  const schedule = () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(placePins); };
  addEventListener('scroll', schedule, true);
  addEventListener('resize', schedule);
  let lastPath = location.pathname;
  setInterval(() => { if (location.pathname !== lastPath) { lastPath = location.pathname; renderPanel(); } schedule(); }, 800);
  refresh();
})();
