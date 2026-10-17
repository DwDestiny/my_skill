# show-01 · 设计流水线发布页（叠片机）

来源：评测任务 E2（`evals/E2/`），2026-10-16 到 2026-10-17 走完 S0 到 S6。页面讲的是本插件自己的八步 SOP，内容来自仓库文件，不代表任何客户项目。

| 项 | 值 |
|---|---|
| 氛围 | 钢与纸：冷灰铝底、工程蓝、硬门黄只给当前站。动效气质"驱动"（滚动推轨），首屏一次签名时刻。此页在 2026-10-17 重定向前按旧"show 档"做，README 保留旧评审口径 |
| 载体 | `desktop-web`，桌面为主，手机 390 能看（首屏 4:5 近景裁切，s2 用 780×976 近景静图） |
| 页面形态 | `P03` 固定舞台换内容。7 章：s0 首屏、s1 成品、s2 八步（pin 300vh）、s3 点头、s4 防模板（pin 150vh）、s5 边界、s6 缺口 |
| 点子 | 叠片机：需求从左端进，八个工位各留一个文件，八层压实成一张成品页从右端出 |
| 签名时刻 | 首屏八层自下而上落下压实（错开 80 ms，每片 380 ms），成品页滑出并亮起，S3 夹具合上变黄。总长 1.4 s，一次。Reduce Motion 直接显示终态 |
| 技术 | three.js 0.160（CDN importmap）程序化几何，`RoundedBoxGeometry` 倒角，单 `WebGLRenderer` 用 `setScissor` 分三区画三台机器。Lenis 1.3.11 可选，`?nolenis` 关闭。静止 400 ms 后停 rAF |
| 盲评 | S6 第 1 轮 4 与 3 取低 3。修改轮（B1 到 B4）后第 2 轮 4 与 3 取低 3。两轮 3 分都来自术语与内部编号，不来自形态。改字 M1、M2 后未再盲评 |
| Fable | S3.5 第 1 轮 3 分，第 2 轮 4 分。S6 第 1 轮 3 分（B1 到 B4），第 2 轮 4 分可交付（`evals/E2/runs/20261016/05-评审/S6-ROUND-2.md`） |
| 依赖 | three.js 与 Lenis 走 jsDelivr CDN。无 WebGL 时首屏退到 `assets/hero-still.jpg` |
| 本机未验 | 真实 GPU 帧率、Safari 与 Firefox、768 到 1279 宽、4G 首屏时刻、Fable G5 真机核验 8 项 |
| 截图 | `shots/`：`1440-hero.jpg`、`1440-s2.jpg`、`1440-s4.jpg`、`390-hero.jpg`，每张 ≤110 KB。盲评与可区分性并排用 |

## 打开

```bash
python3 -m http.server 8130 --directory examples/finished/show-01/page
```

浏览器开 `http://127.0.0.1:8130/`，视口 1440×900。`?still` 直接出首屏终态。`?export` 产出各站静帧到 `window.__exp`。

## 不可照抄的部分

1. 叠片机是"八步各留一个文件"这一内容结构的解。步骤不留文件、或步骤数不固定的流程，不能沿用叠片与工位。
2. 硬门黄只表示硬门与当前站，一色一义。别的页面若黄色没有"门"的含义，不能把黄夹具当装饰搬走。
3. 单渲染器三区 scissor 与"静止 400 ms 停循环"是 2 核无 GPU 机器上的工程解。有 GPU 的项目可以改回多画布或持续循环，但要重测首屏时刻。

## 可借的部分

| 位置 | 可借 |
|---|---|
| 机器工厂 | `buildMachine({ stations, clampGap, stackHeight, pageYaw, pagePos, clampMode, labels })`，一份几何三处用 |
| 首屏 | `poseA(ms)` 时间驱动的签名时刻，`__heroReady` 就绪标志，`?still` 终态，`hero-still.jpg` 退路 |
| pin 章 | 左栏面板 `max-height` 随内容，右侧舞台 300vh 推轨，黄牌等于当前站，落片 120 ms 一层 |
| 阅读章 | s3 控制台（SVG 夹具合上），s5 护栏板（四个红框禁区，≤480 px 只留数字），s6 铭牌表（方块、圆圈、三角三种状态） |
| 导出 | `?export` 一次产出 `st-0` 到 `st-7`、`s2-final`、`s4-final`、`s2-390` 静帧 |
| 工具箱检查 | floor-check 0 FAIL 1 WARN，flash-check 0 FAIL，defaults-check 与 mixed-01 相似度 14%。检查是参考，不是门 |

## 已知残余问题

1. s1 成品托盘没做"叠放展开"，四张缩略是静态排列。
2. 390 首屏是 1440 构图的 4:5 近景裁切，不是独立构图。
3. O1 未做：s5 护栏板没有 3D 近景帧，只有平面图。
4. O5 未做：s4 纸卡上的英文 id 在 1440 下可辨认。
5. s3 两帧交叉淡入只核了终态帧，时序未录屏。
6. 真机未验：Fable G5 清单 (a) 到 (n)，含真实 GPU 帧率、Safari 与 Firefox、768 到 1279 宽、4G 首屏时刻。

## 案例库

此页贡献的案例：hero-08 悬层压实首屏、steps-05 相机推轨逐站拆层、page-06 单渲染器三区裁切、panel-05 夹具合上确认、nav-05 当前站牌、cards-01 滚动摊开托盘，以及 S6 第 2 轮补库演练的 5 条（见 `library/cases.md`）。
