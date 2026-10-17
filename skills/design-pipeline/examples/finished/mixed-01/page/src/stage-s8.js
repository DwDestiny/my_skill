// stage-s8.js · 开场：A03 图签角特写为底，章先落，再渗印（只画在施工图层）。play() 只执行一次。
import { bleed } from './ink.js';

export function mount(sheet, opts = {}) {
  const reduced = opts.reduced ?? matchMedia('(prefers-reduced-motion: reduce)').matches;
  const base = opts.assets || new URL('../../assets/generated/', import.meta.url).href;
  const host = document.createElement('div');
  host.className = 's8-stage' + (reduced ? ' is-reduced' : '');
  host.innerHTML = `
    <div class="s8-plan">
      <img class="s8-bg" src="${base}A03-s8-seal.jpg" alt="" width="1536" height="1024">
      <svg class="s8-seal" viewBox="0 0 120 120" role="img" aria-label="审定章">
        <rect x="10" y="10" width="100" height="100" rx="9" fill="none" stroke="currentColor" stroke-width="10"/>
        <text x="60" y="76" text-anchor="middle" font-size="42" font-weight="700" fill="currentColor" font-family="var(--font-body)">审定</text>
      </svg>
    </div>
    <div class="s8-tp" aria-hidden="true"></div>`;
  sheet.appendChild(host);
  const plan = host.querySelector('.s8-plan'), seal = host.querySelector('.s8-seal');
  let played = false, destroyed = false;
  return {
    play() {
      if (played) return Promise.resolve();
      played = true;
      host.classList.add('is-stamped');
      const wait = reduced ? 0 : 400;
      return new Promise((r) => setTimeout(r, wait)).then(() => {
        if (destroyed) return;
        return bleed(seal, { size: 320, spread: 0.45, alpha: 0.5, duration: 800, parent: plan, reduced });
      }).then((res) => {
        if (destroyed) return;
        host.classList.add('is-inked');
        sheet.dispatchEvent(new CustomEvent('s8:inked', { bubbles: true }));
        return res;
      });
    },
    destroy() { destroyed = true; host.remove(); },
  };
}
