---
title: 设计流水线发布页
one_line: 一句委托从左端进入，一张做过设计的页面从右端出来。
version: 0.1
date: 2026-10-19
delivery: local-html
language: zh-CN
audience:
  who: 不懂设计的委托人
  use_mode: [速读]
  device: [desktop, mobile]
reader_mode: 看
style_quotes: ["给不懂设计的委托人看的，让他一眼知道这东西能把需求做成什么样的页面、怎么做、为什么不会做成模板"]
outcomes: [O1, O2, O3]
sources_file: blueprint.md#附录-证据索引
glossary_file: blueprint.md#附录-术语表
credibility_legend: "高=插件文件原文；中=插件文件转述历史记录；未验证=当前插件内无原文"
notes: 样例。7 章，舞台章 4（s0 s1 s2 s4），占 4/7，高于默认 1/4。事实只取自插件自身文件。
---

# 设计流水线发布页

## 顶部摘要
- 流水线分四个阶段，形成四部分设计产物：blueprint.md 加同一个 design.md 的三节。 [C001] 事实 · 高
- 案例库有 148 条，机制示例有 21 个。 [C002] [C003] 事实 · 高
- 防模板靠 8 条机制，不靠检查脚本。 [C004] 事实 · 高

## 产品层（样例，未经客户确认）

### P1 根本目标
| 谁 | 目标 | 依据 |
|---|---|---|
| 客户（发起这页的人） | 让委托人一眼看懂流水线能产出什么 | 原话 |
| 读者 | 判断要不要把自己的需求交给这条流水线 | 原话 |

### P2 工作故事
| 编号 | 当（情境） | 我想（动机） | 以便（结果） | 失败代价 | 结果 |
|---|---|---|---|---|---|
| J1 | 当我第一次看到这页 | 我想看到产出物 | 以便知道值不值得往下读 | 读者离开 | O1 |
| J2 | 当我想知道怎么做 | 我想看到每个阶段留下什么 | 以便知道自己要给什么 | 读者给错材料 | O2 |
| J3 | 当我担心做成模板 | 我想看到防模板的做法与边界 | 以便决定是否信任 | 读者不信任 | O3 |

### P3 页面职责卡
| 页面 / 章 | 工作故事 | 访客到此状态 | 离开时必须做到 | 唯一主任务 | 必需内容 | 展示形式 | 视觉重量 | 禁止出现 |
|---|---|---|---|---|---|---|---|---|
| s0 首屏 | J1 | 刚打开 | 说出"需求进、页面出" | 看到机器 | s0-1 s0-2 | 3D 舞台 | 主角 | 内部编号 |
| s1 成品 | J1 | 想看产出 | 看到成品截图 | 看成品 | s1-1 s1-2 s1-3 | 舞台加读数 | 主角 | 生成图冒充截图 |
| s2 八步 | J2 | 想知道怎么做 | 说出每个阶段留下什么 | 沿机身看四个阶段 | s2-1 s2-2 | pin 加 scrub | 主角 | 步骤编号占视觉中心 |
| s3 点头 | J2 | 想知道何时确认 | 知道委托人要点头 | 读确认规则 | s3-1 s3-2 | 阅读 | 配角 | 无 |
| s4 防模板 | J3 | 担心像模板 | 说出 8 条机制 | 看发牌 | s4-1 s4-2 s4-3 | 舞台加列表 | 主角 | 无 |
| s5 边界 | J3 | 想知道不做什么 | 说出 4 条禁区 | 读边界 | s5-1 | 阅读 | 配角 | 无 |
| s6 缺口 | J3 | 想知道没验证什么 | 看到未测项 | 读缺口 | s6-1 | 阅读 | 配角 | 无 |

## 章节

### s0 · 一句委托进去，一张设计过的页面出来
- id: s0
- outcome_ids: [O1]
- pattern: 答案先行
- intro: 流水线把一句委托做成一张页面。
- claims: [C001]
- new_terms: []
- blocks:
  - block: s0-1
    shape: 标题与一句话
    form: text
    title: 一句委托进去，一张设计过的页面出来
    claims: [C001]
    budget: 25 字
    mobile: 同桌面
    twin: 无
  - block: s0-2
    shape: 四阶段提示
    form: text
    title: 四个阶段，四部分产物
    claims: [C001]
    budget: 25 字
    mobile: 同桌面
    twin: 无
- fold: []
- screens: 1
- checkpoint: 读完这节你能说出页面的用途。
- stage: yes
- image_needs:
  - id: A01
    purpose: 首屏主视觉，让读者看到需求进、页面出
    subject: 八层叠片落下的叠片机
    kind: mechanism
    size: 全宽 16:9

### s1 · 上一个成品长这样
- id: s1
- outcome_ids: [O1]
- pattern: 先给结果
- intro: 流水线已有 3 个成品范例。
- claims: [C006, C008]
- new_terms: []
- blocks:
  - block: s1-1
    shape: 评审读数
    form: text
    title: 评审从 3 分到 4 分
    claims: [C008]
    budget: 60 字
    mobile: 同桌面
    twin: 无
  - block: s1-2
    shape: 成品截图展开
    form: text
    title: 5 张成品截图
    claims: [C006]
    budget: 60 字
    mobile: 竖排
    twin: A02
  - block: s1-3
    shape: 判断句
    form: text
    title: 三句判断
    claims: [C006, C008]
    budget: 90 字
    mobile: 同桌面
    twin: 无
- fold: []
- screens: 2
- checkpoint: 读完这节你能说出成品的评价结论。
- stage: yes
- image_needs:
  - id: A02
    purpose: 给出 5 个真实成品画面作证据
    subject: 5 张首屏截图：show-01 的 d-fold 与 m-fold，mixed-01 的 d-fold 与 m-fold，clear-01 的 m-fold（浅色，首屏）
    kind: data
    size: 1440×900 与 390×844
  - id: A03
    purpose: 评审读数的刻度尺
    subject: 评审 3 分到 4 分
    kind: mechanism
    size: 800×120

### s2 · 四个阶段，每个阶段留下一部分产物
- id: s2
- outcome_ids: [O2]
- pattern: 顺序展开
- intro: 每个阶段交出一部分产物，交给下一阶段：阶段 1 是 blueprint.md，阶段 2 到 4 是 design.md 的三节。本页按四阶段讲流水线；叠片机的八个工位沿用评测页的历史划分（S0 到 S6 加 S3.5），与四阶段不一一对应，页面不展示这个对应。
- claims: [C001, C007, C013]
- new_terms: [站, 层]
- blocks:
  - block: s2-1
    shape: 阶段产物表
    form: table
    title: 每个阶段留下什么
    claims: [C001]
    budget: 4 行 × 2 列
    items:
      - 列：阶段 | 产物
      - 1 内容蓝图 | `01-内容规划/blueprint.md`，并在 `design.md` 第 0 节登记路径
      - 2 视觉氛围 | `design.md` 第 1 节
      - 3 组件创意 | `design.md` 第 2 节
      - 4 design.md | `design.md` 第 3 节
    mobile: 竖排 4 行
    twin: 无
  - block: s2-2
    shape: 八工位机身示意
    form: text
    title: 八工位静帧
    claims: [C007]
    budget: 30 字
    mobile: 静图
    twin: A04
- fold: []
- screens: 3
- checkpoint: 读完这节你能说出每个阶段的产物。
- stage: yes
- image_needs:
  - id: A04
    purpose: 八工位静帧，只作机身示意，工位上只写站名 S0 到 S6、S3.5，不写产出说明
    subject: 八个工位的静帧
    kind: mechanism
    size: 8 张各 320×200

### s3 · 委托人点头，文件才锁定
- id: s3
- outcome_ids: [O2]
- pattern: 规则加例子
- intro: 确认是一个动作，发生在两个位置。
- claims: [C012]
- new_terms: [夹具]
- blocks:
  - block: s3-1
    shape: 规则句
    form: text
    title: 确认后文件不可改
    claims: [C012]
    budget: 80 字
    mobile: 同桌面
    twin: 无
  - block: s3-2
    shape: 控制台近景
    form: text
    title: 夹具合上
    claims: [C012]
    budget: 30 字
    mobile: 静图
    twin: A05
- fold: []
- screens: 1
- checkpoint: 读完这节你能说出何时点头。
- stage: no
- image_needs:
  - id: A05
    purpose: 夹具合上的近景
    subject: S3 工位的夹具
    kind: mechanism
    size: 16:9

### s4 · 每次开工都重新发牌，用过的不再发
- id: s4
- outcome_ids: [O3]
- pattern: 机制加证据
- intro: 防模板靠 8 条机制。
- claims: [C002, C003, C004, C009, C010, C014]
- new_terms: [发牌, 使用史]
- blocks:
  - block: s4-1
    shape: 发牌说明
    form: text
    title: 一次发 3 张，选 1 张
    claims: [C010]
    budget: 80 字
    mobile: 同桌面
    twin: A06
  - block: s4-2
    shape: 机制列表
    form: text
    title: 8 条机制
    claims: [C004, C014]
    budget: 8 句各 ≤40 字
    items:
      - M1 点子先于库：发牌前先写点子。把身份换成相邻身份（一个普通的 CI 流水线介绍页），点子应当不成立；仍成立则重做。
      - M2 发牌不检索：一次发 3 张候选，从中选 1 张。
      - M3 使用史跨项目：发牌前写出最近 5 次用了什么，撞车则重新发牌。
      - M4 禁用清单每项目重写：每项目写 5 条，有使用史时至少 2 条引用上一项目。
      - M5 库里存决定不存形容词：每个决定写选项名、数值或色值、参照。
      - M6 默认值检查：按清单逐项查，命中 2 项回阶段 2 重做。
      - M7 可区分性盲评（建议）：与上一项目并排，另一会话说出 3 处不同。
      - M8 机制示例不带皮肤：接入后页面色值与字体全部来自方向单变量。
    mobile: 同桌面
    twin: 无
  - block: s4-3
    shape: 折叠条
    form: table
    title: 21 个机制示例
    claims: [C002, C003, C009]
    budget: 21 行 × 3 列
    items:
      - 列：目录名 | 路径 | 一句话
      - blender-headless-glb | `examples/mechanisms/blender-headless-glb` | `blender -b --python make-model.py` 在 Blender 里程序化建模（6 块倒角薄板螺旋叠放加中柱，Principled BSDF），导出 `model.glb` 49 KB，three.js GLTFLoader 加载。管线见 `references/blender-pipeline.md`
      - capability-tiering | `examples/mechanisms/capability-tiering` | 探测 6 项信号，判 full / lite / static，写入 `window.__tier`，三档舞台
      - cross-doc-view-transition | `examples/mechanisms/cross-doc-view-transition` | 两个文档都写 `@view-transition { navigation: auto }`，共享元素同名 `view-transition-name`，转场由浏览器完成
      - css-scroll-timeline | `examples/mechanisms/css-scroll-timeline` | 零 JS，`animation-timeline: view()` 与 `scroll()` 做入场与进度条，`@supports` 包住
      - depth-parallax-image | `examples/mechanisms/depth-parallax-image` | 程序生成彩色图与深度图，着色器按深度位移，指针加滚动驱动
      - fluid-ink-pointer | `examples/mechanisms/fluid-ink-pointer` | WebGL2 染料双缓冲，curl noise 加指针速度回溯采样，文字在实色面板上
      - fluid-noise | `examples/mechanisms/fluid-noise` | 全屏片元着色器 fbm 噪声，三个 CSS 变量传入 uniform
      - glass | `examples/mechanisms/glass` | backdrop-filter 玻璃浮层，只用于浮层
      - gltf-model-stage | `examples/mechanisms/gltf-model-stage` | GLTFLoader 加载本地 model.glb，`make-model.mjs` 手写 glTF 二进制写入器生成 25 KB 环面
      - grain | `examples/mechanisms/grain` | SVG feTurbulence 静态颗粒，可选 steps() 动态颗粒，页内算正文对比度
      - image-sequence | `examples/mechanisms/image-sequence` | canvas 按滚动进度绘 24 帧程序化序列，预加载、进度映射、低端机降帧
      - instanced-field | `examples/mechanisms/instanced-field` | InstancedMesh 画 3000 根柱，高度按噪声场变化，鼠标移波心，滚动推相位，按需渲染
      - lenis-webgl-sync | `examples/mechanisms/lenis-webgl-sync` | Lenis 平滑滚动，gsap.ticker 单循环同时驱动 ScrollTrigger.update 与 three 着色器 uniform，静止时不渲染
      - mesh-gradient | `examples/mechanisms/mesh-gradient` | WebGL 1 片元着色器融合 5 个来自 CSS 变量的控制色，慢速漂移，读回像素实测正文区对比度
      - pinned-3d-scrub | `examples/mechanisms/pinned-3d-scrub` | ScrollTrigger pin 一屏并 scrub，驱动 8 方块旋转、分解、相机推进三段，文字叠层按段切换。舞台 `data-pin-screens="2"`
      - raymarch-backdrop | `examples/mechanisms/raymarch-backdrop` | 全屏片元着色器 SDF 光线步进（球体与盒体平滑并集），只作 `show` 档背景，文字在实色面板上
      - scroll-camera-path | `examples/mechanisms/scroll-camera-path` | three.js 四个站点，相机沿 CatmullRomCurve3 随滚动穿行，HTML 叠层文字
      - scroll-story | `examples/mechanisms/scroll-story` | GSAP ScrollTrigger 固定舞台，三章，SVG 状态切换，`--p` 由 scrub 驱动
      - splittext-kinetic | `examples/mechanisms/splittext-kinetic` | SplitText 按字入场（位移加旋转）加 SVG textPath 的 startOffset 随滚动 scrub
      - variable-font-axis | `examples/mechanisms/variable-font-axis` | 原生 `font-variation-settings`，滚动进度驱动 wght、slnt、CASL，rAF 合并写入
      - webgl-scene | `examples/mechanisms/webgl-scene` | three.js 程序化分层板片与节点连线，鼠标视差，滚动推镜头
    mobile: 折叠
    twin: 无
- fold: [s4-3]
- screens: 2
- checkpoint: 读完这节你能说出防模板的做法。
- stage: yes
- image_needs:
  - id: A06
    purpose: 发牌口吐出 3 张方向卡
    subject: 发牌口与方向卡
    kind: mechanism
    size: 16:9

### s5 · 四条禁区
- id: s5
- outcome_ids: [O3]
- pattern: 边界清单
- intro: 流水线明确不做四类事。
- claims: [C005, C015]
- new_terms: [禁区]
- blocks:
  - block: s5-1
    shape: 护栏图
    form: text
    title: 四条禁区
    claims: [C015]
    budget: 4 句各 ≤40 字
    items:
      - 禁 1 没有概念承载：手法不能用一句话说出它表达主题的哪一点。
      - 禁 2 挡住阅读：动效层、3D、视频与正文重叠，或正文对比低于 4.5:1。
      - 禁 3 同一手法重复超过默认次数：同一表现形式 id 出现 3 次以上。
      - 禁 4 出现在阅读区：阅读区只允许反馈与状态动效。
    mobile: 静图
    twin: A07
- fold: []
- screens: 2
- checkpoint: 读完这节你能说出四条禁区。
- stage: no
- image_needs:
  - id: A07
    purpose: 护栏翻开露出禁区
    subject: 4 块护栏与禁区标签
    kind: mechanism
    size: 1200×400

### s6 · 没验证的部分
- id: s6
- outcome_ids: [O3]
- pattern: 状态清单
- intro: 本页有 5 项没有验证或没有原文。
- claims: [C011, C012, C013]
- new_terms: []
- blocks:
  - block: s6-1
    shape: 铭牌
    form: table
    title: 五项未验证内容
    claims: [C011, C012, C013]
    budget: 5 行 × 4 列
    mobile: 竖排
    twin: 无
    items:
      - 列：项目 | 状态 | 一句说明 | 来源文件
      - 检查点与浮夸度维度的清单 | 缺口 | 插件内无原文，本页不展示 | 见 C011
      - 委托人点头两次 | 缺口 | 插件内无原文 | 见 C012
      - 八站与四阶段的对应 | 缺口 | 插件内无对应表 | 见 C013
      - 四项底线 | 缺口 | 原样例有此说法，restraint.md 只有四条禁区，已删 | `references/restraint.md` 第 2 节
      - 实现后的页面 | 未测 | 样例只到 design.md，未做截图与盲评 | 无
- fold: []
- screens: 1
- checkpoint: 读完这节你能说出哪些内容没有验证。
- stage: no
- image_needs: []

## 信息缺口
- id: gaps
- claims: [C011, C012, C013]
- C011：检查点与浮夸度维度的清单在插件内无原文，本页不展示。
- C012：当前插件内无原文，来自历史页面。
- C013：`SKILL.md` 与 `README.md` 没有八站到四阶段的对应表。
- 四项底线：插件内无原文，蓝图与 design.md 已删。

## 信息架构
- 导航：顶栏 7 个章名锚点，显示当前位置
- 折叠清单：s4-3
- 附录：证据索引、术语表
- 可信度图例位置：顶部摘要之后
- 速读通道检查：s0 的 s0-1 单独读即可知道页面用途

## 章节到结果对照
| 章节 | 结果 |
|---|---|
| s0 | O1 |
| s1 | O1 |
| s2 | O2 |
| s3 | O2 |
| s4 | O3 |
| s5 | O3 |
| s6 | O3 |

## 删除清单
| 断言 | 原因 |
|---|---|
| 盲评从 2 分到 4 分 | 当前插件内无原文，改用 `show-01/README.md` 的 Fable 3 分到 4 分 |

## 附录 证据索引
| 断言 ID | 断言 | 来源（路径与小节） | 可信度 |
|---|---|---|---|
| C001 | 流水线分 4 个阶段，每阶段一部分产物（blueprint.md 与 design.md 三节） | `SKILL.md` 第 1.1 节 | 高 |
| C002 | 案例库有 148 条 | `README.md` 状态行 | 高 |
| C003 | 机制示例有 21 个 | `README.md` 第 1 节"examples/mechanisms/" | 高 |
| C004 | 反同质化有 8 条机制 M1 到 M8 | `references/anti-sameness.md` 第 1 节 | 高 |
| C005 | 收放原则有 4 条禁区 | `references/restraint.md` 第 2 节 | 高 |
| C006 | 成品范例有 3 个，show-01 与 clear-01 是待改案例 | `README.md` 第 1 节"examples/finished/" | 高 |
| C007 | 历史页面讲的是旧八步 SOP，每步留一个文件 | `examples/finished/show-01/README.md` 来源行 | 中 |
| C008 | Fable 评审 S3.5 第 1 轮 3 分，第 2 轮 4 分 | `examples/finished/show-01/README.md` 表中"Fable"行 | 中 |
| C009 | 禁用清单每项目写 5 条 | `references/anti-sameness.md` 第 1 节 M4 | 高 |
| C010 | 发牌一次 3 张，选 1 张 | `references/anti-sameness.md` 第 1 节 M2 | 高 |
| C011 | 检查点 7 个，浮夸度 9 个维度 | 当前插件内无原文，来自历史页面 | 未采用 |
| C012 | 委托人点头两次，确认后文件不可改 | 当前插件内无原文，来自历史页面 | 未验证 |
| C013 | 历史页面按 S0 到 S6 八站运行，插件内无八站到四阶段的对应表 | `examples/finished/show-01/README.md` 来源行 | 中 |
| C014 | 8 条机制 M1 到 M8 的名称与作用 | `references/anti-sameness.md` 第 1 节表 | 高 |
| C015 | 4 条禁区的名称与判定 | `references/restraint.md` 第 2 节 | 高 |

## 附录 术语表
| 首选词 | 定义 | 不用的词 |
|---|---|---|
| 站 | 页面机身上的一个工位，只作视觉造型，不对应阶段 | 阶段（阶段指 `SKILL.md` 的 4 个阶段） |
| 层 | 悬在机身上的一片叠片，只作视觉造型，不代表文件 | 片、板 |
| 夹具 | 检查点的物理形状，合上表示通过 | 锁、闸 |
| 发牌 | `toolbox/deal.mjs` 按槽与目的发 3 条候选 | 抽签、检索 |
| 使用史 | `history/history.json` 里已用过的组合记录 | 历史 |
| 禁区 | `references/restraint.md` 的 4 类不做的事 | 红线 |
| 舞台章 | 以固定舞台承载视觉主体的章 | 展示章 |
