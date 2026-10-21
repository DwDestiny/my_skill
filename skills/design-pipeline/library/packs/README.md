# 设计装置包（packs）规格 v0.1 · 2026-10-21

> 何时读：要往库里加一个获奖站，或要给长期运行的采集 agent 派活时读。做页面的人不读本文件，读 `INDEX.json` 和单个包的 `CARD.md`。
> 目的：让 agent 知道什么是好的、如何做出好的。一包围绕一个**装置**（让人停住并记住的那一个做法），站只是出处。文字、我们自己写的代码、网址入库；对方的截图、图片、视频、源码不入库。

## 1. 目录

```
library/packs/
  INDEX.json                 每包一行，固定字段，10 KB 级，lib.mjs packs 查它
  <pack-id>/
    CARD.md                  3 KB 级，八块，见第 3 节
    recipe.html              10 KB 以内，我们自己写的最小复现，能直接打开
    recipe-shots/            recipe 的 1440 与 390 截图各一张（自己的页，可入库）
patterns/
  <pattern-id>.md            跨包反复出现的装置：一条 pattern，多条变体，附反例
```

帧序列、技术盘点 JSON（`toolbox/record-motion.py` 的产物）留在录制机器的临时目录，`CARD.md` 的证据块只写路径和日期。

## 2. INDEX.json 字段

| 字段 | 取值 | 用途 |
|---|---|---|
| `id` | `<站 slug>-<装置 slug>`，例 `terminal-industries-scan-overlay` | 唯一键 |
| `site`, `url`, `award`, `year`, `tier` | 站名、网址、奖项（SOTY/SOTM/SOTD/FWA/CSSDA）、年份、档（judging.md 第 2 节） | 身份与分量 |
| `page_type` | studio-home / product-launch / brand / team / careers / culture / editorial / ecommerce / personal / tool | 同页型检索 |
| `world` | case-map.md 第 1 节的簇 id（如 `dark-one-light`、`real-site-and-people`、`site-plus-tech-layer`） | 选方向 |
| `scenarios` | 数组：题材与受众标签，例 `["工程服务","B 端","团队介绍"]` | 选方向 |
| `device` | 装置类型：`photo-plus-overlay` / `one-light-in-dark` / `giant-word-on-scene` / `live-counter` / `object-macro` / `print-order` / `flat-character` / `walkable-space` / `scroll-timeline` / 新类型要先在 patterns 里立条 | 查重与 pattern 归类 |
| `motion` | 数组：`entry-reveal` / `scroll-stage` / `scroll-page` / `camera-path` / `image-sequence` / `video-base` / `shader-bg` / `kinetic-type` / `none` | 换题与派工 |
| `pointer` | 数组：`light-reveal` / `follow` / `magnet` / `distort` / `crosshair-cursor` / `drag` / `none` | 换题与派工 |
| `tech` | 数组：`three` / `gsap-scrolltrigger` / `lenis` / `pixi` / `webgl-raw` / `css-only` / `video` / `lottie` / `rive` | 派工 |
| `gpu` | `need` / `nice` / `no` | 机器选择与降级 |
| `difficulty` | 1 到 3（1 = CSS 与 SVG 一天内；2 = 需要 three 或 ScrollTrigger；3 = 自定义着色器或物理） | 派工预算 |
| `mobile` | 装置在 390 宽退成什么：`same` / `static-frame` / `reduced` / `hidden` | 载体判断 |
| `recipe` | `yes` / `partial` / `no` | 能不能复制起手 |
| `evidence` | `recorded` / `recorded-loading-only` / `screens-only` | 可信度 |
| `checked_at` | YYYY-MM-DD | 淘汰与复核 |

查法：`node toolbox/lib.mjs packs --where world=dark-one-light,pointer=light-reveal --fields id,site,device,difficulty`（lib.mjs 增加 `packs` 子命令后生效）。

## 3. CARD.md 八块

每块一个二级标题，顺序固定。每句不超过 60 字，写看得见的事实；形容词必须跟着"在哪一帧、哪个位置"。

| 块 | 写什么 | 谁在哪一步读 |
|---|---|---|
| 1 身份 | INDEX 字段的可读版，加一句"这个站为什么得奖"（评审页或评语里的原话，标来源） | 选方向 |
| 2 帧 | 首屏、中段、页尾各一句：构图、光从哪来、字多大在哪、主物是什么 | 选方向、评审 |
| 3 动 | 入场：什么从哪来、几秒、先后；滚动：固定舞台还是整页滚、什么随进度变（相机、图序列、字、色、章节号）；媒体：视频 / WebGL / 图序列 / CSS 各管哪一块 | 换题、派工 |
| 4 跟手 | 指针、悬停、点按带动什么；触屏退成什么 | 派工 |
| 5 好在哪 | judging.md 五维各一句，每句指着一帧说；最弱的一维也写 | 评审定档 |
| 6 换题 | 结构（不变的）一行；名词（必换的）一行；三处雷同风险一行（照抄会被认出来的地方） | 换题 |
| 7 复现 | 用 `examples/mechanisms/` 哪几个拼、拼法一句、难点一句、GPU 与手机降级一句、recipe 做到了几成 | 派工简报 |
| 8 证据 | 录制日期、机器有无 GPU、帧目录路径（本地）、技术盘点摘要（canvas/WebGL/video/库）、没看到的部分写"帧看不出" | 质检 |

## 4. recipe.html 要求

1. 单文件，10 KB 以内，不含外部图片；库只从 cdnjs / jsDelivr / unpkg 固定版本引入。
2. 只复现装置的骨架：占位色、程序生成的占位图、假数据。颜色全部是 CSS 变量，方便换皮。
3. 必须有：Reduce Motion 分支、触屏分支、无 WebGL 时的静帧回退（照 `examples/mechanisms/capability-tiering`）。
4. 文件头注释写：复现的是哪个包的哪个装置、和原站的三处不同、怎么换皮。
5. 自验：打开、1440 与 390 各截一张放 `recipe-shots/`，控制台无错误。

## 5. 采集 agent 的循环

1. **取队列**：Awwwards 的 SOTY、SOTM、SOTD 列表与 FWA、CSSDA、Godly 的近两年获奖页。只取网址与奖项，遵守各站 robots 与条款，不批量抓图。
2. **录站**：`python3 toolbox/record-motion.py --url <站> --out <临时目录>/<slug>`。有 GPU 的机器优先。WebGL 站只录到加载页时，`evidence` 写 `recorded-loading-only`，画面描述只写能看见的。
3. **立装置**：看三组帧，写出 1 到 2 个装置。先查 `INDEX.json` 的 `device` 与 `patterns/`：已有同装置就并入该 pattern 作变体（CARD 仍写，INDEX 的 `device` 指同一类型），不另立类型。
4. **写 CARD**：按第 3 节。每句对应帧；对应不上的删。
5. **写 recipe**：按第 4 节。做不出的写 `partial` 并写清缺哪一块。
6. **质检**（换一个会话做，只给 CARD、recipe 截图、帧）：五句以上没有帧依据 → 退回；装置和已有包三处以内差异 → 并入变体；recipe 打开报错 → 退回。
7. **提交**：每 20 包一个分支一个 PR，PR 描述列包 id 与质检结果。合并后更新 `case-map.md` 对应簇的条目指向包。
8. **淘汰**：同一 `device` 超过 5 个变体只留档最高、证据最全的 5 个；每季度按真实任务里 `deal.mjs` 使用史被引用的次数复核一次，一年没被引用且不是 SOTY 的降到 `patterns/` 的变体列表里，删包。

节奏参考：一站录制 3 到 5 分钟，CARD 10 分钟，recipe 15 到 40 分钟，质检 5 分钟。一天 30 到 50 包。

## 6. 红线

- 不把对方的截图、图片、视频、字体、源码放进仓库。帧只留本地，定期删。recipe 是自己的实现，不是对方代码的改写。
- 没有证据的句子不写。宁可写"帧看不出"。
- 不为了凑数降档：`tier` 只按 judging.md 的锚点定义，SOTD 不自动算 4。
- 新装置类型先在 `patterns/` 立条再入 INDEX，防止类型爆炸。

## 7. 待办（规格落地前）

- `lib.mjs` 加 `packs` 子命令（读 INDEX.json，支持 `--where` 与 `--fields`）。
- `selftest.py` 加一项：INDEX 每行字段齐全、每个 id 有目录与 CARD。
- 用现有 30 个高分锚点先做 5 个包跑通（Terminal、Immersive Garden、Floema、Igloo、Lusion），再放给采集 agent。
