---
# DESIGN.md — 设计系统规范（Google design.md 格式）
# 提取自 logip SaaS dashboard 参考视觉，用于驱动公众号运营看板的视觉实现。
# Tokens 为规范值；正文说明如何应用。

colors:
  # 语义命名：primary/secondary + neutral 表面体系
  primary: "#5B8DEF"          # 主强调蓝：主按钮、active 态、图表本期线、链接
  secondary: "#F5A623"        # 暖橙：图表对比线、头像暖底、次要强调
  success: "#34C759"          # 正向：done 状态、上升 delta
  danger: "#FF4D4F"           # 负向：下降 delta、通知点
  canvas: "#E6E8EC"           # 最外层灰底（卡片浮于其上）
  surface: "#FFFFFF"          # 卡片/主面板白
  surface-subtle: "#F4F5F7"   # 浅灰填充：图标圆容器、pill、Upgrade 卡
  on-surface: "#1A1D1F"       # 主文字（近黑）
  on-surface-muted: "#6F767E" # 次要文字
  on-surface-faint: "#9AA0A6" # 三级文字/占位
  chart-tooltip: "#1C1F2A"    # 深色圆角 tooltip 背景

typography:
  font-family: "Inter, 'Plus Jakarta Sans', Manrope, -apple-system, system-ui, sans-serif"
  display:  { size: "32px", weight: 700, role: "问候/总结论标题" }
  headline: { size: "20px", weight: 600, role: "区块标题" }
  metric:   { size: "28px", weight: 700, role: "KPI 大数字" }
  body:     { size: "15px", weight: 400, role: "正文" }
  label:    { size: "13px", weight: 500, role: "字段标签（muted）" }
  caption:  { size: "12px", weight: 400, role: "辅助说明（faint）" }

spacing:
  scale: "8px 基准（4px 半步）"
  card-padding: "24px"
  section-gap: "24px–32px"
  layout: "三栏 250px / 1fr / 320px"

radius:
  shell: "28px"     # 最外层大卡
  card: "18px"      # 内卡片
  pill: "999px"     # 按钮/胶囊/选择器
  icon: "999px"     # 圆形图标容器
  tooltip: "12px"

shadow:
  card: "0 18px 40px rgba(20, 28, 46, 0.08)"   # 柔和、大范围、低透明度
---

# 公众号运营看板设计系统

## Visual Philosophy

对齐 logip SaaS dashboard 的视觉语言：**干净、克制、宽松留白、柔和大圆角**。大面积白与浅灰构成底色，蓝色作唯一主强调，暖橙/绿/红只在数据语义处点缀。一屏一焦点，图表精致，文字克制——读者一眼抓住重点，不被信息淹没。

这不是"企业报表"，是"现代产品仪表盘"：每个卡片都有呼吸感，每个数字都有层级，每个图表都圆润友好。

## Colors

主强调只用 `primary` 蓝（`#5B8DEF`）——主按钮、active 导航、图表本期线、可点链接。`secondary` 暖橙用于图表对比线和头像暖底。`success`/`danger` 仅用于数据语义（上升/下降、完成/告警），不作装饰。

表面体系三层：`canvas` 最外灰底 → `surface` 白卡片 → `surface-subtle` 浅灰填充（图标圆容器、pill、次要卡）。文字三级：`on-surface` 主、`on-surface-muted` 次、`on-surface-faint` 辅助。

**红线**：页面不出现"置信度/高置信/N%"——置信度通过视觉层级（见 Components 的 emphasis）隐性传达。

## Typography

几何无衬线（Inter / Plus Jakarta Sans / Manrope）。层级分明：`display` 用于问候和总结论（大而重），`metric` 用于 KPI 大数字，`headline` 用于区块标题，`body` 正文，`label`/`caption` 用 muted/faint 色降权。标题字重 600–700，正文 400。

## Spacing & Layout

8px 基准网格（4px 半步微调）。卡片内 padding 24px，区块间距 24–32px，整体宽松。三栏布局 `250px / 1fr / 320px`：左导航 + 中叙事主区 + 右上下文栏。中区 scroll-snap 一屏一结论。

## Components

**KPI / 指标卡**：圆形 `surface-subtle` 图标容器（48px，内置线性图标）+ `label` 标签 + `metric` 大数字 + delta（↑/↓ 箭头 + `success`/`danger` 色 + 变化量）。`rounded: card`，`padding: 24px`。

**折线图**：平滑 `monotone` 双线（`primary` 本期 + `secondary` 对比），浅网格（`#EDF1F5`），无显式坐标轴线，圆点 marker。Tooltip 用 `chart-tooltip` 深色背景 + `radius: tooltip` 圆角 + 白字。

**任务/列表行**：圆形图标容器 + 标题（`body`，weight 500）+ 彩色状态点（`primary`/`secondary`/`success`）+ 文字状态 + 时长。

**结论卡（emphasis 视觉层级）**：置信度内化为三档视觉权重——
- `hero`：`display` 级大字号、占据主视觉位、`primary` 强调色描边/底；
- `primary`：正常 `surface` 卡片、`headline` 标题；
- `secondary`：缩小、`on-surface-muted` 文字、归入次要区，刻意做淡。

**pill 选择器**：`surface-subtle` 底 + 文字 + chevron-down，`radius: pill`。

**头像**：圆形（`radius: icon`）+ 右下角状态点。开源 demo 用矢量 `sample-avatar.svg`。

**避免**：卡片墙、拥挤首屏、灰底为主的沉闷壳、纯文字解释。每屏一个主视觉（图表/矩阵/排行/行动板）。
