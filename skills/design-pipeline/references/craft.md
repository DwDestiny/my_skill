# 工艺附录

> 何时读：设计已写进 `design.md`，开始写代码与看图时。
> 读完做什么：从成品复制工艺层，接入动效，导出静帧，截图看图。
> 本文件只管"怎么做出来"。创意在阶段 2 与阶段 3。
> 来自：旧 `prompts/S5-build.md`、`prompts/S6-accept.md`、`references/sop.md` 第 9 节。

## 1. 起手复制

从 `examples/finished/` 选一个成品复制，再改。不从空白起手。上一个项目用过的成品不选。先读成品文件头"不可照抄的部分"。

复制的是工艺层。形态、版式、配色、文案不复制。形态不同不是跳过复制的理由。

| 复制 | 内容 |
|---|---|
| 令牌结构 | 颜色与字体全部走 CSS 变量。值取 `design.md` |
| 动效引擎 | 入场、反馈、驱动三类的实现，加 Reduce Motion 分支 |
| 滚动同步 | Lenis 或原生滚动，与 `animation-timeline` 的退路 |
| 导出口 | 第 3 节的 `?export` |
| 截图钩子 | 第 4 节的 `window.__idle`、`window.__heroReady` |

接入案例的机制时（`examples/mechanisms/<id>/index.html`），只借机制。示例里的色值不留。接入后搜一遍示例的色值，页面里不应有残留。

## 2. 可选钩子

> 只在用 `toolbox/` 脚本时需要。不用脚本可以不加。

| 钩子 | 放在哪 |
|---|---|
| `data-chapter` 与 `data-layout="<版式家族>"` | 每章 `<section>` |
| `data-hero-visual` | 首屏视觉主体，内含 `svg`、`img`、`canvas` 或 `picture` |
| `data-reveal` | 入场元素 |
| `data-counter` | 数字滚动元素 |

缺钩子时，脚本会漏查或报错。

## 3. 静帧导出口

Reduce Motion 与 390 窄屏需要静态图。用页面里的同一工厂渲染，不另做一套图。做法如下，取自 `evals/E2/runs/20261016/04-页面/index.html`。

1. 页面读 URL 参数 `?export`。有参数时，不进入正常循环。
2. 定义 `snap(w, h, fn, q)`：设渲染器尺寸为 w 乘 h，调 `fn(w, h)` 摆好终态，返回 `canvas.toDataURL('image/jpeg', q)`。
3. 把每帧存入 `window.__exp`，键是帧名。
4. 用 `agent-browser eval` 读 `window.__exp` 的 dataURL，解码后存成 `assets/*.jpg`。
5. 每帧 ≤120 KB。超过就降 `q` 或缩尺寸。
6. 页面在 Reduce Motion 或窄屏下用这些 jpg，代替实时画布。

3D 的静帧导出属于案例级技术，写进对应案例的 `impl`。

## 4. 冷加载与截图

three.js 冷加载超过 2 s 时，首屏动效 deferred：先显示静帧和标题，到首次滚动或指针事件再启动。标题 3 秒内必须可读。

示例环境是软件渲染，慢，只能证明状态，不代表真机帧率。

| 要拍的 | 做法 |
|---|---|
| 滚动后的屏 | `scrollTo` 之后派发 `scroll` 事件，轮询 `window.__idle === true` 再拍 |
| 首屏 | 派发 `scroll` 与 `wheel`，等 `window.__heroReady === true` 再拍 |
| 停止本地服务 | 用 `fuser -k <端口>/tcp`。不要用 `pkill -f`，它会杀掉自己的 shell |

> **注意**：每处修补都在停靠视口的截图上验证。修补落在视口外等于没改。教训：说明栏加在停靠视口下方，读者看不到。

## 5. 实现时的几条

1. 动效引擎要有 Reduce Motion 分支。退路是静（`references/restraint.md` 的气质表）。不要为了通过检查而删动效。先改位置、幅度、频率。删除要写进报告。
2. 舞台格的实质内容不全藏在悬停层下。每格不悬停时至少露出一行实质内容。
3. 小程序与 App：按 `01-载体.md` 的视口尺寸、导航高度与胶囊预留实现。不画设备外框。
4. 蓝图每章的 claims 全部渲染。缺的写"未知"。

## 6. 生成资产

只经 `image-gen` skill 生成。读 `references/asset-generation.md`。

1. 按 `design.md` 的资产清单逐张生成。放 `assets/generated/`。
2. 每张用 Read 看图。乱字、logo、错误数字、风格偏离，重生成，最多 3 次，再用备选。
3. 压缩：hero ≤300 KB，章节图 ≤200 KB，平铺纹理 512 像素以内、≤50 KB。
4. 写 `assets/generated/ASSETS.md`，每张一行：编号、用途、提示词要点、尝试次数。
5. 提示词不写客户名、隐私、示例环境路径。
6. 不从网站取图，除非用户先批准。不复制 Anthropic 品牌。

## 7. 开源库建议

用成熟库实现，不自己写底层。版本一律写"固定版本"，在 `design.md` 第 3 节写出确切号。

| 库 | 用途 | 版本 |
|---|---|---|
| three | 3D 与 WebGL 舞台 | 0.160 以上，固定版本 |
| lenis | 平滑滚动，与舞台同步 | 固定版本 |
| gsap | 时间线与滚动触发 | 固定版本 |

脚本从 `cdnjs.cloudflare.com`、`cdn.jsdelivr.net/npm/` 或 `unpkg.com` 加载时，写完整版本号，不用 `latest`。

## 8. 可选工具箱

下表命令都是可选。它们帮你发现问题，不替你判断设计好不好。参数见各脚本头部注释。

| 命令 | 用途 |
|---|---|
| `python3 toolbox/shots.py --url <url> --out <目录>` | 拍首屏、分屏、页尾、768、390、深色、减少动效、键盘焦点、悬停前后、各停靠点 |
| `python3 toolbox/defaults-check.py <index.html> [--compare <另一页>]` | 查 X1 到 X17 里能 grep 的默认值，可与上一页比对 |
| `python3 toolbox/flash-check.py <index.html>` | 查 `references/restraint.md` 里能用脚本查的项 |
| `python3 ../visual-motion-design/assets/floor-check.py <index.html> --carrier <id>` | 对比度、最小字号、命中区、钩子等基本检查 |
| `node toolbox/deal.mjs ...` | 发牌与写使用史，见 `stages/3-components.md` |

## 9. 看图

脚本通过不证明设计好。逐张真实截图对照看图清单，清单见 `visual-motion-design/references/review.md`。修完再请 Fable 做视觉评审（用户 2026-10-12 全局规则）。评审问法：哪里不像 `design.md`，哪里太素，先改哪三处。

两个独立会话盲评是建议，不是必须。给它们只看截图目录，不给方案与代码。
