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
- 流水线分四个阶段，每个阶段留下一份文件。 [C001] 事实 · 高
- 案例库有 148 条，机制示例有 21 个。 [C002] [C003] 事实 · 高
- 防模板靠 8 条机制，不靠检查脚本。 [C004] 事实 · 高
- 检查点个数与浮夸度维度数，当前插件内无原文。 [C011] 缺口

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
| s2 八步 | J2 | 想知道怎么做 | 说出每站留下什么 | 沿机身看站 | s2-1 s2-2 s2-3 | pin 加 scrub | 主角 | 步骤编号占视觉中心 |
| s3 点头 | J2 | 想知道何时确认 | 知道委托人要点头 | 读确认规则 | s3-1 s3-2 | 阅读 | 配角 | 无 |
| s4 防模板 | J3 | 担心像模板 | 说出 8 条机制 | 看发牌 | s4-1 s4-2 s4-3 | 舞台加列表 | 主角 | 无 |
| s5 边界 | J3 | 想知道不做什么 | 说出 4 条禁区 | 读边界 | s5-1 s5-2 s5-3 | 阅读 | 配角 | 无 |
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
    title: 四个阶段，四份文件
    claims: [C001]
    budget: 25 字
    mobile: 同桌面
    twin: 无
- fold: []
- screens: 1
- checkpoint: 读完这节你能说出页面的用途。
- stage: yes
- image_needs: [A01]

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
    form: image
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
- image_needs: [A02, A03]

### s2 · 四个阶段，每一站留下一个文件
- id: s2
- outcome_ids: [O2]
- pattern: 顺序展开
- intro: 每个阶段交出一份文件，交给下一阶段。
- claims: [C001, C007]
- new_terms: [站, 层]
- blocks:
  - block: s2-1
    shape: 站点说明
    form: text
    title: 每一站留下什么
    claims: [C001]
    budget: 90 字
    mobile: 竖排 8 行
    twin: A04
  - block: s2-2
    shape: 站点小图
    form: image
    title: 站点小图
    claims: [C007]
    budget: 30 字
    mobile: 静图
    twin: A04
  - block: s2-3
    shape: 折叠条
    form: table
    title: 检查点清单
    claims: [C011]
    budget: 折叠
    mobile: 折叠
    twin: 无
- fold: [s2-3]
- screens: 3
- checkpoint: 读完这节你能说出每个阶段的产物。
- stage: yes
- image_needs: [A04]

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
    form: image
    title: 夹具合上
    claims: [C012]
    budget: 30 字
    mobile: 静图
    twin: A05
- fold: []
- screens: 1
- checkpoint: 读完这节你能说出何时点头。
- stage: no
- image_needs: [A05]

### s4 · 每次开工都重新发牌，用过的不再发
- id: s4
- outcome_ids: [O3]
- pattern: 机制加证据
- intro: 防模板靠 8 条机制。
- claims: [C002, C003, C004, C009, C010]
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
    claims: [C004]
    budget: 8 句各 ≤40 字
    mobile: 同桌面
    twin: 无
  - block: s4-3
    shape: 折叠条
    form: table
    title: 21 个机制示例
    claims: [C002, C003, C009]
    budget: 折叠
    mobile: 折叠
    twin: 无
- fold: [s4-3]
- screens: 2
- checkpoint: 读完这节你能说出防模板的做法。
- stage: yes
- image_needs: [A06]

### s5 · 四条禁区与四项底线
- id: s5
- outcome_ids: [O3]
- pattern: 边界清单
- intro: 流水线明确不做四类事。
- claims: [C005, C011]
- new_terms: [禁区]
- blocks:
  - block: s5-1
    shape: 护栏图
    form: image
    title: 四块禁区
    claims: [C005]
    budget: 120 字
    mobile: 静图
    twin: A07
  - block: s5-2
    shape: 折叠条
    form: table
    title: 浮夸度维度
    claims: [C011]
    budget: 折叠
    mobile: 折叠
    twin: 无
  - block: s5-3
    shape: 底线列表
    form: text
    title: 四项底线
    claims: [C005]
    budget: 140 字
    mobile: 同桌面
    twin: A07
- fold: [s5-2]
- screens: 2
- checkpoint: 读完这节你能说出四条禁区。
- stage: no
- image_needs: [A07]

## 信息缺口
- id: gaps
- claims: [C011, C012]
- s6-1: 铭牌 5 行。已测、未测、缺口三种状态，每行含项目、状态、一句说明、来源文件。
- 章 s6 · 没验证的部分：block s6-1，stage: no，screens: 1。

## 信息架构
- 导航：顶栏 7 个章名锚点，显示当前位置
- 折叠清单：s2-3、s4-3、s5-2
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
| C001 | 流水线分 4 个阶段，每阶段一份产物 | `SKILL.md` 第 1 节 | 高 |
| C002 | 案例库有 148 条 | `README.md` 状态行 | 高 |
| C003 | 机制示例有 21 个 | `README.md` 第 1 节"examples/mechanisms/" | 高 |
| C004 | 反同质化有 8 条机制 M1 到 M8 | `references/anti-sameness.md` 第 1 节 | 高 |
| C005 | 收放原则有 4 条禁区 | `references/restraint.md` 第 2 节 | 高 |
| C006 | 成品范例有 3 个，show-01 与 clear-01 是待改案例 | `README.md` 第 1 节"examples/finished/" | 高 |
| C007 | 历史页面讲的是旧八步 SOP，每步留一个文件 | `examples/finished/show-01/README.md` 来源行 | 中 |
| C008 | Fable 评审 S3.5 第 1 轮 3 分，第 2 轮 4 分 | `examples/finished/show-01/README.md` 表中"Fable"行 | 中 |
| C009 | 禁用清单每项目写 5 条 | `references/anti-sameness.md` 第 1 节 M4 | 高 |
| C010 | 发牌一次 3 张，选 1 张 | `references/anti-sameness.md` 第 1 节 M2 | 高 |
| C011 | 检查点 7 个，浮夸度 9 个维度 | 当前插件内无原文，来自历史页面 | 未验证 |
| C012 | 委托人点头两次，确认后文件不可改 | 当前插件内无原文，来自历史页面 | 未验证 |

## 附录 术语表
| 首选词 | 定义 | 不用的词 |
|---|---|---|
| 站 | 流水线的一个步骤，在页面里画成一个工位 | 阶段（阶段指 `SKILL.md` 的 4 个阶段） |
| 层 | 一站留下的一个文件，在页面里画成一片叠片 | 片、板 |
| 夹具 | 检查点的物理形状，合上表示通过 | 锁、闸 |
| 发牌 | `toolbox/deal.mjs` 按槽与目的发 3 条候选 | 抽签、检索 |
| 使用史 | `history/history.json` 里已用过的组合记录 | 历史 |
| 禁区 | `references/restraint.md` 的 4 类不做的事 | 红线 |
| 舞台章 | 以固定舞台承载视觉主体的章 | 展示章 |
