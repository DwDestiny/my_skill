#!/usr/bin/env python3
"""record-motion.py 录一个站"怎么动、怎么跟手"的证据。Python 3.12 标准库，调用 agent-browser 子进程。

为什么有它（2026-10-21）：锚点库 30 个高分站里 23 条的 motion 写着"截图看不出"，案例地图因此只记了静态构图，
做出来的页面和参考站只剩"也是暗的、也有线"。获奖站的好，一半在它怎么动、怎么跟手。入库和借案例前先跑这个。

用法：
  python3 toolbox/record-motion.py --url <站点> --out <目录> [--screens 4] [--session rec]
  python3 toolbox/record-motion.py --anchor <锚点id> --out <目录>      读 library/anchors.json 的 url

产物（都在 --out 下，临时目录，看完删，不入库）：
  00-load.png      打开后 1.5 秒（入场进行中）
  01-settled.png   打开后 6 秒（入场结束）
  10-scroll-1.png … 每滚一个视口高度截一张，最后一张是页底
  20-pointer-a/b/c.png  指针停在左上、中心、右下各 1 秒后
  30-top-again.png 回到顶部后（看有没有回放或状态保留）
  inventory.json   技术盘点：canvas/video 数、WebGL、three/gsap/ScrollTrigger/Lenis/PIXI/lottie、
                   动画数、sticky/fixed 元素数、滚动驱动属性、页面高度
  MOTION.md        上面的清单加一张待填表（入场/滚动/跟手/媒体/证据），由看图的人填

怎么读证据：
  入场 = 00 和 01 的差别；滚动 = 10-* 相邻两张的差别；跟手 = 20-* 三张和 01 的差别。
  WebGL 重站在无 GPU 机器上可能只出加载页，这时 inventory.json 仍然可信（它看的是 DOM 和脚本），画面去 awwwards 作品页看分段截图。
  agent-browser 第一次 open 可能失败，脚本自动重开一次。同时只开一个会话。
"""
import argparse, json, os, subprocess, sys, time, pathlib

INVENTORY_JS = r"""
(() => {
  const canv=[...document.querySelectorAll('canvas')];
  let webgl=0; for(const c of canv){ try{ if(c.getContext('webgl2')||c.getContext('webgl')) webgl++; }catch(e){} }
  const vids=[...document.querySelectorAll('video')].map(v=>({autoplay:v.autoplay,loop:v.loop,w:v.videoWidth,h:v.videoHeight,src:(v.currentSrc||v.src||'').slice(0,120)}));
  const srcs=[...document.scripts].map(s=>s.src).filter(Boolean);
  const kw=['three','gsap','scrolltrigger','lenis','pixi','lottie','splitting','locomotive','barba','swiper','webgl','shader','rive','spline','matter','ogl','curtains','babylon','framer','motion'];
  const libs={}; for(const k of kw){ libs[k]=srcs.filter(s=>s.toLowerCase().includes(k)).length; }
  const g={THREE:!!window.THREE,gsap:!!window.gsap,ScrollTrigger:!!(window.ScrollTrigger||(window.gsap&&window.gsap.core&&window.gsap.core.globals&&window.gsap.core.globals().ScrollTrigger)),Lenis:!!window.Lenis,PIXI:!!window.PIXI,lottie:!!window.lottie,locomotive:!!window.LocomotiveScroll};
  let anims=0; try{ anims=document.getAnimations().length; }catch(e){}
  const all=[...document.querySelectorAll('body *')];
  let sticky=0,fixed=0; for(const el of all){ const p=getComputedStyle(el).position; if(p==='sticky')sticky++; else if(p==='fixed')fixed++; }
  const dataScroll=all.filter(el=>[...el.attributes].some(a=>/^data-(scroll|speed|parallax|aos|animate|reveal|split)/.test(a.name))).length;
  const inline=[...document.scripts].filter(s=>!s.src).map(s=>s.textContent).join('\n');
  const shader=/gl_FragColor|gl_Position|precision (high|medium)p float|uniform /.test(inline);
  return JSON.stringify({url:location.href,title:document.title.slice(0,80),pageHeight:document.documentElement.scrollHeight,viewport:[innerWidth,innerHeight],canvas:canv.length,webgl,video:vids,libsByScriptSrc:libs,globals:g,animationsRunning:anims,sticky,fixed,dataScrollAttrs:dataScroll,inlineShader:shader,scripts:srcs.length,fonts:[...new Set(all.slice(0,400).map(e=>getComputedStyle(e).fontFamily.split(',')[0].replace(/["']/g,'')))].slice(0,6)});
})()
"""

def ab(*args, timeout=60):
    r = subprocess.run(['agent-browser', *args], capture_output=True, text=True, timeout=timeout)
    return (r.stdout or '') + (r.stderr or '')

def shot(path):
    ab('screenshot', str(path))
    return path.exists()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--url'); ap.add_argument('--anchor'); ap.add_argument('--out', required=True)
    ap.add_argument('--screens', type=int, default=4); ap.add_argument('--session', default='rec')
    ap.add_argument('--width', type=int, default=1440); ap.add_argument('--height', type=int, default=900)
    a = ap.parse_args()
    url = a.url
    if a.anchor:
        lib = pathlib.Path(__file__).resolve().parent.parent / 'library' / 'anchors.json'
        d = json.load(open(lib))
        hit = [x for g in ('high', 'low') for x in d.get(g, []) if x.get('id') == a.anchor]
        if not hit: sys.exit(f'锚点 {a.anchor} 不在 anchors.json')
        url = hit[0].get('url'); print('url', url)
    if not url: sys.exit('需要 --url 或 --anchor')
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    os.environ['AGENT_BROWSER_SESSION'] = a.session
    ab('set', 'viewport', str(a.width), str(a.height))
    ok = 'error' not in ab('open', url, timeout=90).lower()
    if not ok:
        time.sleep(2); ab('open', url, timeout=90)
    time.sleep(1.5); shot(out / '00-load.png')
    time.sleep(4.5); shot(out / '01-settled.png')
    inv_raw = ab('eval', INVENTORY_JS, timeout=60).strip()
    inv = None
    try:
        s = inv_raw[inv_raw.index('{'):inv_raw.rindex('}') + 1]
        inv = json.loads(json.loads('"' + s.replace('"', '\\"') + '"')) if s.startswith('{\\') else json.loads(s)
    except Exception:
        try: inv = json.loads(json.loads(inv_raw))
        except Exception: inv = {'raw': inv_raw[:800]}
    # 门：有些站首屏是一道门（弹球、点击进入、Scroll to explore），滚轮推不动。推一次探路，推不动就点中心、按空格，再等 3 秒。
    def scroll_y():
        try: return float(ab('eval', 'window.scrollY||document.scrollingElement.scrollTop||0').strip().strip('"') or 0)
        except Exception: return 0.0
    def dom_sig():
        return ab('eval', "(()=>{const b=document.body;return b?b.innerText.length+':'+b.querySelectorAll('*').length+':'+(window.scrollY|0):''})()").strip()
    ab('mouse', 'move', str(a.width // 2), str(a.height // 2))
    sig0 = dom_sig(); ab('mouse', 'wheel', str(a.height)); time.sleep(1.6)
    gated = False
    if dom_sig() == sig0:
        gated = True
        ab('mouse', 'down'); ab('mouse', 'up'); time.sleep(1.0)
        ab('press', 'Space'); time.sleep(3.0)
        ab('mouse', 'wheel', str(a.height)); time.sleep(1.6)
        if dom_sig() != sig0: shot(out / '02-after-gate.png')
    for _ in range(3): ab('mouse', 'wheel', str(-a.height * 2)); time.sleep(0.2)
    ab('eval', 'window.scrollTo(0,0)'); time.sleep(1.0)
    scroll_log = []
    frames = []
    for i in range(1, a.screens + 1):
        ab('mouse', 'move', str(a.width // 2), str(a.height // 2)); ab('mouse', 'wheel', str(a.height)); time.sleep(1.6)  # 滚轮事件：Lenis 等虚拟滚动站也能动
        p = out / f'10-scroll-{i}.png'; shot(p); frames.append(p.name); scroll_log.append(scroll_y())
    for _ in range(6): ab('mouse', 'wheel', str(a.height * 2)); time.sleep(0.4)
    time.sleep(1.6)
    shot(out / f'10-scroll-{a.screens + 1}-end.png')
    for _ in range(12): ab('mouse', 'wheel', str(-a.height * 3)); time.sleep(0.2)
    ab('eval', 'window.scrollTo(0,0)'); time.sleep(1.5)
    for name, (x, y) in {'a': (a.width * 0.15, a.height * 0.2), 'b': (a.width * 0.5, a.height * 0.5), 'c': (a.width * 0.85, a.height * 0.8)}.items():
        ab('mouse', 'move', str(int(x)), str(int(y))); time.sleep(1.0)
        shot(out / f'20-pointer-{name}.png')
    shot(out / '30-top-again.png')
    ab('close')
    if isinstance(inv, dict):
        inv['gated'] = gated; inv['scrollYPerFrame'] = scroll_log
        inv['note'] = '每帧 scrollY 全为 0 且 pageHeight 不大：虚拟滚动或门没过，画面变化只能看帧；仍为 0 且帧全同：这站在无头浏览器里没动起来，去 awwwards 作品页看。'
    (out / 'inventory.json').write_text(json.dumps(inv, ensure_ascii=False, indent=1))
    md = [f'# 动效证据：{url}', '', '帧：00-load（1.5 秒）、01-settled（6 秒）、10-scroll-1…（每屏）、10-scroll-N-end（页底）、20-pointer-a/b/c（指针左上、中心、右下）、30-top-again（回顶）。', '',
          '## 技术盘点', '```json', json.dumps(inv, ensure_ascii=False, indent=1)[:3000], '```', '',
          '## 待填（看图的人填，写进 anchors.json 的 moves 字段）', '',
          '| 项 | 写什么 |', '|---|---|',
          '| entry | 00 到 01 之间发生了什么：什么东西从哪来、多久、谁先谁后 |',
          '| scroll | 10-* 相邻两张的差别：固定舞台还是整页滚；什么随进度变（相机、图序列、字、颜色） |',
          '| pointer | 20-* 和 01 的差别：指针带动了什么（照亮、跟随、变形、磁吸）；没有就写"未观察到" |',
          '| media | 画面由什么做出来：video / canvas-webgl / canvas-2d / svg / css；对应 inventory |',
          '| evidence | 现场录（本脚本）/ 作品页截图 / 看不出 |']
    (out / 'MOTION.md').write_text('\n'.join(md))
    print('录完', out, '帧', len(list(out.glob('*.png'))), '盘点', 'raw' not in (inv or {}))

if __name__ == '__main__':
    main()
