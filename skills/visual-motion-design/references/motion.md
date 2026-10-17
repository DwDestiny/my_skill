# 动效：引擎、编排、炫技

先读 `gears.md` 选预算预设。本文讲怎么做。

## 1. 原则

1. 静态页先完成。动效放大构图，不能挽救构图。
2. 一个动效动词。页面的全部动效都是同一个动词的变体（"像纸落定""像快门打开""像图层叠起"），同一族缓动。
3. 编排，不是装饰。每个动效回答三个问题：发生了什么、什么重要、接下来看哪里。按阅读顺序错开，大物件先动、慢动。
4. 一个时钟。全部按帧的逻辑走引擎的 `onTick` / `onScroll`，不另写 `requestAnimationFrame` 循环或 scroll 监听。
5. 只动 `transform`、`opacity`、`clip-path`、`--p` 这类不触发布局的属性。折叠的 `grid-template-rows` 是唯一例外。
6. 反馈不是配饰。删减时先删装饰，hover / press / focus 反馈只能改样，不能删。
7. 减少动效是设计过的版本，不是坏掉的版本。看它的截图。

## 2. 引擎

文件：`assets/engine/motion-engine.js`、`engine.css`、`head-flag.html`。零依赖，离线可开，是 预设 `clear`的引擎和 GSAP 引擎的回退。来源与许可见 `assets/engine/LICENSE-MIT.txt`。

接入步骤：

1. 把 `head-flag.html` 的 `<script>` 放进 `<head>`，位于样式之后。
2. 引入 `engine.css`（在令牌之后）。
3. 在 `</body>` 前：`import { boot } from './engine/motion-engine.js'; boot({ gear: 'clear' });`
4. 用数据属性标记元素。属性清单见引擎文件头部注释。
5. 需要自定义加载器或驱动模块时，在 `boot({ setup })` 的 `setup` 里注册。

引擎按预算预设自动限制：`gear` 参数取 `clear`、`mixed`、`show`，这是预设标识。`clear` 不拆字、不漂移、不磁吸、无加载器；`mixed` 漂移上限 0.08、加载器 ≤1.2 秒；`show` 全开。改预算先改 `gears.md`，再改 `GEARS` 常量。

### 选引擎

| 预算预设 | 引擎 | 说明 |
|---|---|---|
| clear | `motion-engine.js`（零依赖） | 不用 GSAP。离线可开 |
| mixed | `motion-engine-gsap.js` | GSAP + ScrollTrigger。Lenis 可选（`boot({ lenis: true })`）。固定舞台（`data-pin`）≤1 个 |
| show | `motion-engine-gsap.js` | GSAP + ScrollTrigger + Lenis。允许 WebGL（OGL 或 three.js，按需从 CDN 加载，同样固定版本） |

### GSAP 引擎

文件：`assets/engine/motion-engine-gsap.js`。起点页面：`assets/page-skeleton-gsap.html`。字体片段：`assets/fonts-web.html`。

1. 数据属性、`boot({ gear, setup })`、`html.motion` 门控与减少动效行为与 `motion-engine.js` 相同。新增可选属性 `data-pin`。
2. 库从 jsdelivr CDN 加载，版本精确固定，带 SRI。版本写在文件顶部的 `CDN` 常量里。升级前查 npm 发布日期，须满 14 天。
3. 本 skill 不分发 GSAP 文件。许可见 `sources-and-credits.md`。
4. 减少动效时不请求 CDN。
5. CDN 在 2.2 秒内没加载完时，引擎改用零依赖实现，`<html data-engine="fallback">`。内容照常可见。成功时 `data-engine="gsap"`。
6. 需要 WebGL 时，在 `boot({ setup })` 里按需动态加载 OGL 或 three.js。同样固定版本、限时、失败时显示静态版本。

## 3. 时长与缓动

| 对象 | 时长 | 缓动 |
|---|---|---|
| 按压 | 100 到 160ms | out |
| hover | 150 到 200ms | ease |
| 菜单、弹层 | 150 到 250ms | out |
| 折叠、抽屉 | 240 到 320ms | out |
| 区块入场 | 400 到 1300ms（按预算预设） | out |
| 文字逐行 | 700 到 1300ms，错开 60 到 100ms | out |
| 图片 clip | 900 到 1600ms | out / inOut |
| 幕布、页面转场 | 800 到 1100ms 每向 | inOut |
| 加载器 | 1.1 到 2.6 秒 | 跟随真实进度 |
| 滚动驱动 | 跟随滚动 | none |

离开比进入快约 30%。`ease-in` 不用。弹性缓动只给反馈类小物件。

## 4. 阅读区的动效

阅读区只做三类：

1. 反馈：按钮按压 `scale(0.97)`、链接下划线加粗或变色、卡片 hover 上抬 ≤2px。
2. 状态：折叠展开、目录当前项、阅读进度、复制成功（停留 2.2 秒后 0.35 秒淡出）。
3. 新内容进入：折叠内容展开时淡入 10 到 12px。

hover 规则：写在 `@media (hover: hover)` 内；每个 hover 状态在 `:focus-visible` 下也有；减少动效下保留颜色或下划线变化。

## 5. 舞台区的动效（mixed / show）

### 5.1 签名时刻

一句话写清它表达主题的哪一点。只有它可以"响"。做法从 `gears.md` 第 5 节的菜单选，或从动效动词发明。周围保持安静。

### 5.2 驱动模块

一个变量（滚动进度、章节序号、指针、时间）驱动全部承载概念的视觉。用引擎的 `driver(map, apply)`：`map` 把变量变成离散状态，`apply` 写到 DOM（`<html>` 上的类、CSS 变量、标签文字）。章节换底色、色场随滚动、标签随章节都走这里。文字色由 `<html>` 上一个全局变量跟随，页面每个状态都检查可读。

### 5.3 固定舞台章节

左文右图或上图下文，图用 `position: sticky`，文字滚动，章节进入中线时 `data-stage` 得到 `data-state`。CSS 按状态切换画面。减少动效下状态仍切换，过渡取消。

### 5.4 空闲动效

只有 预设 `show`允许明显的空闲动效，`mixed` 只允许签名物微动。规则：由概念物承担，幅度几像素或几度；离屏暂停；减少动效下为零；显眼的循环（大面积视频、全屏场景）配可见的暂停按钮。不加"漂浮的形状"来凑数。

### 5.5 WebGL 与 3D

WebGL 只用于线画不出的连续场（光、水、雾、材质）。能删掉而解释仍成立的效果，删掉。规则：canvas 在内容之下；文字上加 DOM 遮罩；无 GL 和减少动效时显示设计过的静态版本；手机 60fps。方法来源 juliobsz webgl.md 与 anatomy webgl.md，着色器自写，不复制对方代码。3D 等轴测交互图走 `figures.md`。

### 5.6 加载器

仅在页面有真实加载工作（字体、关键图、GL）时使用。进度跟随真实任务。出场动画与 hero 首帧衔接：加载器最后一帧等于 hero 第一帧。预设 `show` 1.1 到 2.6 秒，预设 `mixed` ≤1.2 秒，预设 `clear`无。

## 6. 减少动效

| 元素 | 减少动效下 |
|---|---|
| 入场、拆字 | 直接显示（`html.motion` 不加） |
| 漂移、磁吸、空闲 | 关闭 |
| 加载器 | 等待真实资源后 0.3 秒淡出 |
| 滚动 scrub | `--p = 1` 终态 |
| 章节舞台 | 状态仍切换，无过渡 |
| 进度条、目录高亮、折叠 | 保留（状态） |
| GL | 关闭，显示静态版本 |
| 平滑滚动 | 原生 |

## 7. 性能

目标：桌面与中端手机滚动 60fps；LCP <2.5 秒；CLS <0.05；JS ≤300KB gzip；总重 <3MB。`will-change` 只在动画中使用。大面积不动 `filter: blur()` 与 `box-shadow`。

## 8. 生成式动效的破绽

每个区块同款淡入上移；hero 里十几个错开入场；每张卡片 hover 放大；弹性缓动用在界面；无意义的脉冲点、漂浮形状、闪烁文字、旋转徽章；入场没触发留下空白带。
