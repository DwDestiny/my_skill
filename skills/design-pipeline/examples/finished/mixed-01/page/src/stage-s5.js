// stage-s5.js · 五个校审格。set(k) 把前 k 格置为落定。
// 成熟度符号（必改 3）：已有产品 = 实线画满的格，研究或试点 = 铅笔排线，无公开案例 = 虚线空格。印泥章只表示可信度"高"，本图幅不用章。
export const STAGES = [
  { id: 'survey',  name: '勘察',          level: 'pencil', source: 'C112', case: '模板替换生成岩土层描述', note: '' },
  { id: 'scheme',  name: '方案与效果图',  level: 'pencil', source: 'C113', case: 'ComfyUI 加 ControlNet（教学）', note: '' },
  { id: 'drawing', name: '初设与施工图',  level: 'solid',  source: 'C114', case: 'PKPM Agent 2.0', note: '结构建模' },
  { id: 'qty',     name: '算量造价',      level: 'solid',  source: 'C115', case: '广联达 AecGPT', note: '' },
  { id: 'review',  name: '审查与校审',    level: 'split',  source: 'C116', case: '上海 BIM 智能辅助审查', note: '规则加 BIM',
    halves: [{ name: '施工图审查（规则加 BIM）', level: 'pencil' }, { name: '智能校审', level: 'empty' }] },
];
const LABEL = { solid: '已有产品', pencil: '研究或试点', empty: '无公开案例', split: '' };
const HLABEL = { pencil: '规模应用', empty: '无公开案例' };

function mark(level) {
  if (level === 'solid') {
    let h = ''; for (let y = 20; y <= 100; y += 10) h += `<path pathLength="1" d="M12 ${y} H108"/>`;
    return `<svg class="s5-solid" viewBox="0 0 120 120" aria-hidden="true"><rect x="6" y="6" width="108" height="108" fill="none" stroke="currentColor" stroke-width="5"/><g stroke="currentColor" stroke-width="4">${h}</g></svg>`;
  }
  if (level === 'pencil') return `<svg class="s5-pencil" viewBox="0 0 120 120" aria-hidden="true"><rect x="6" y="6" width="108" height="108" fill="none" stroke="currentColor" stroke-width="1.6" stroke-dasharray="3 2" opacity=".7"/><g fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round"><path pathLength="1" d="M14 52 L52 14"/><path pathLength="1" d="M15 78 L79 15"/><path pathLength="1" d="M17 103 L104 17"/><path pathLength="1" d="M41 106 L106 42"/><path pathLength="1" d="M68 105 L105 69"/></g></svg>`;
  return `<svg class="s5-empty" viewBox="0 0 120 120" aria-hidden="true"><rect x="8" y="8" width="104" height="104" fill="none" stroke="currentColor" stroke-width="3" stroke-dasharray="9 8"/></svg>`;
}

export function mount(sheet, opts = {}) {
  const reduced = opts.reduced ?? matchMedia('(prefers-reduced-motion: reduce)').matches;
  const host = document.createElement('div');
  host.className = 's5-stage' + (reduced ? ' is-reduced' : '');
  host.setAttribute('role', 'group'); host.setAttribute('aria-label', '设计全流程五个环节的成熟度');
  host.innerHTML = STAGES.map((s, i) => `
    <button type="button" class="s5-cell" data-level="${s.level}" aria-pressed="false">
      <span class="s5-src"><b>来源</b> <span class="s5-num">${s.source}</span>${s.note ? ' · ' + s.note : ''}</span>
      <span class="s5-tp" aria-hidden="true"></span>
      <span class="s5-no s5-num">${String(i + 1).padStart(2, '0')}</span>
      <span class="s5-name">${s.name}</span>
      <span class="s5-case">${s.case}</span>
      ${s.halves ? `<span class="s5-mark s5-split">${s.halves.map((h) => `<span class="s5-half" data-level="${h.level}"><span class="s5-hn">${h.name}</span>${mark(h.level)}<span class="s5-lv">${HLABEL[h.level]}</span></span>`).join('')}</span>` : `<span class="s5-mark">${mark(s.level)}</span>
      <span class="s5-lv">${LABEL[s.level]}</span>`}
    </button>`).join('');
  sheet.appendChild(host);
  const cells = [...host.querySelectorAll('.s5-cell')];
  const onClick = (e) => { const b = e.currentTarget; const on = b.getAttribute('aria-pressed') !== 'true'; b.setAttribute('aria-pressed', on); b.classList.toggle('is-open', on); };
  cells.forEach((c) => c.addEventListener('click', onClick));
  let cur = 0;
  return {
    set(k) {
      k = Math.max(0, Math.min(STAGES.length, Math.round(k)));
      cells.forEach((c, i) => {
        const was = c.classList.contains('is-done'), now = i < k;
        if (was === now) return;
        c.classList.toggle('is-done', now);
        if (now && !reduced) { c.classList.remove('is-land'); void c.offsetWidth; c.classList.add('is-land'); }
      });
      cur = k;
    },
    get k() { return cur; },
    destroy() { cells.forEach((c) => c.removeEventListener('click', onClick)); host.remove(); },
  };
}
