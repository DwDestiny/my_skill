# Deck Spec Schema

`scripts/build_visual_pptx.js` 读取一个 JSON spec，并输出可编辑 `.pptx`。

## 顶层字段

```json
{
  "title": "Deck title",
  "subtitle": "Optional subtitle",
  "author": "Codex",
  "theme": {
    "background": "F7F4EF",
    "foreground": "17202A",
    "accent": "1F8A70",
    "accent_2": "E76F51",
    "muted": "6B7280",
    "panel": "FFFFFF",
    "font_face": "Aptos"
  },
  "slides": []
}
```

颜色用 6 位十六进制，不带 `#` 也可以。

## 支持的 layout

通用约束：

- 标题页的左侧标题区域会控制在右侧视觉面板之外；长中文标题应允许自动换行，不应压到右侧面板。
- 正文、图表标签和页码都是可编辑文本对象。
- 图片只作为插图或透明素材层，不应把整页正文烤成图片。
- 商用 deck 的非标题/章节/收尾页必须写 `claim`，即这一页要证明的一句话。
- 涉及判断、图表、路线、风险、指标时必须写 `source` 或 `chart.source`；没有来源的数据只能标为假设或示例模型。

### title

```json
{
  "layout": "title",
  "title": "主标题",
  "subtitle": "副标题",
  "kicker": "视觉化交付系统"
}
```

### content

```json
{
  "layout": "content",
  "title": "页面标题",
  "claim": "这一页的核心判断",
  "body": "一段说明",
  "bullets": ["要点一", "要点二"],
  "source": "资料来源或口径说明"
}
```

### image_text

```json
{
  "layout": "image_text",
  "title": "页面标题",
  "claim": "这一页的核心判断",
  "body": "一段说明",
  "bullets": ["要点一", "要点二"],
  "image": "/absolute/path/transparent_asset.png",
  "source": "资料来源或口径说明"
}
```

`image` 支持绝对路径，也支持相对 spec 文件的相对路径。

### bar_chart

```json
{
  "layout": "bar_chart",
  "title": "页面标题",
  "claim": "这一页的核心判断",
  "body": "图表口径说明",
  "chart": {
    "labels": ["网站", "PPT", "App"],
    "values": [42, 68, 55],
    "unit": "%",
    "source": "图表数据来源或示例口径"
  }
}
```

当前 helper 用 PPT 形状绘制条形图，便于用户继续编辑。

### reference_visual_trend

用于“完整效果图母稿通过后，按 clean background + 坐标蓝图重建”的视觉趋势页。这个 layout 的目标不是通用模板，而是验证参考图反拆路径：先有整页 PPT 效果图母稿，再派生无文字、无图表的 raster 底板；标题、正文、指标、柱状图、趋势线、坐标标签全部是 PPT 可编辑对象。

`reference_anime_trend` 是旧别名，仍然兼容；新 spec 优先使用 `reference_visual_trend`。

```json
{
  "layout": "reference_visual_trend",
  "layout_variant": "future_launch_stage",
  "design_director_brief": {
    "expression_system": "tech_launch_stage",
    "style_intent": "科技发布会感，用中央舞台柱图、光轨和右侧遥测数据制造发布节奏。",
    "title_anchor": "左上发布会标题",
    "body_pattern": "底部横向遥测 ticker",
    "proof_object": "中央发射台柱状证明对象",
    "metric_pattern": "右侧遥测数据栈",
    "typography_system": "大标题 + 高亮数字 + 短句 ticker",
    "color_strategy": "深蓝底、青蓝主色、紫色辅助，保证科技感与可读性。",
    "chart_language": "中央发光柱图、顶部数值、弱化坐标",
    "layout_rhythm": "上方定题，中部证明，右侧指标，底部进度流"
  },
  "visual_draft_image": "assets/anime-full-page-draft.png",
  "background_image": "assets/anime-clean-background.png",
  "coordinate_blueprint": {
    "title_zone": {"x": 1.0, "y": 1.08, "w": 5.1, "h": 0.62},
    "text_zone": {"x": 1.02, "y": 2.46, "w": 4.95, "h": 2.02},
    "subtitle_zone": {"x": 1.02, "y": 1.78, "w": 4.6, "h": 0.42},
    "bullet_zone": {"x": 1.02, "y": 2.46, "w": 4.95, "h": 2.02},
    "metrics_zone": {"x": 2.05, "y": 5.12, "w": 3.95, "h": 1.08},
    "chart_title_zone": {"x": 6.82, "y": 1.7, "w": 3.2, "h": 0.38},
    "chart_zone": {"x": 6.7, "y": 2.38, "w": 5.08, "h": 3.7},
    "visual_focus_zone": {"x": 6.2, "y": 0.8, "w": 5.8, "h": 5.7},
    "protected_empty_zone": {"x": 0.7, "y": 0.4, "w": 11.9, "h": 6.5}
  },
  "overlay_style": {
    "subtitle_color": "CFE5FF",
    "bullet_title_color": "F5F9FF",
    "bullet_body_color": "B8C8DE",
    "bullet_icon_texts": ["01", "02", "03"],
    "title_font_size": 29,
    "subtitle_font_size": 12.5,
    "bullet_title_font_size": 12,
    "bullet_body_font_size": 8.5,
    "metric_value_font_size": 19,
    "metric_label_font_size": 7.2,
    "metrics_divider_color": "456B9D",
    "metrics_divider_transparency": 45,
    "metric_label_color": "D8E6F8",
    "chart_title_color": "F5F9FF",
    "chart_title_font_size": 11.8,
    "chart_grid_color": "456B9D",
    "chart_grid_transparency": 58,
    "chart_zero_grid_transparency": 18,
    "chart_tick_color": "A9BEDA",
    "chart_tick_font_size": 6.8,
    "chart_label_color": "CFE5FF",
    "chart_label_font_size": 7,
    "chart_value_color": "F5F9FF",
    "chart_value_font_size": 8.2,
    "chart_source_color": "8EA6C8",
    "chart_source_font_size": 5.4,
    "chart_bar_colors": ["2BD3FF", "4E8DFF", "8D6BFF", "16E0B3"],
    "chart_bar_transparency": 14
  },
  "title": "2026 AI 应用趋势调研",
  "subtitle": "从智能助手到业务协同",
  "bullets": [
    {"title": "学习成本降低", "body": "AI 工具更易上手，知识获取与技能成长更高效。"}
  ],
  "metrics": [
    {"value": "73%", "label": "企业试点"}
  ],
  "chart": {
    "title": "AI 应用综合趋势指数",
    "labels": ["2023\n探索期", "2024\n成长期"],
    "values": [58, 72],
    "source": "示例数据，仅用于视觉样张"
  }
}
```

硬约束：

- `visual_draft_image` 必须是先生成并通过审美确认的整页 PPT 效果图母稿，允许带示例标题、正文、指标和图表。
- `background_image` 必须是 clean background，不能使用带文字和图表的效果图母稿。
- `visual_draft_image` 和 `background_image` 必须是两个不同文件，不能互相顶替。
- `coordinate_blueprint` 必须来自母稿反拆，至少包含 `title_zone`、`text_zone` 或 `bullet_zone`、`chart_zone`、`metrics_zone`、`visual_focus_zone`、`protected_empty_zone`。
- `layout_variant` 控制页面骨架，不是装饰名。当前支持：
  - `minimal_left_report`：左侧报告式正文 + 右侧图表。
  - `future_dashboard_focus`：深色科技仪表盘式。
  - `oriental_vertical_scroll`：东方竖向卷轴式。
  - `editorial_feature_story`：杂志特写叙事式。
  - `boardroom_summary_matrix`：董事会报告 + 右侧象限矩阵。
  - `future_launch_stage`：科技发布会舞台 + 中央柱图 + 右侧遥测栈。
  - `oriental_scroll_narrative`：东方横排题签 + 左侧卷轴分栏 + 底部路径线。
  - `editorial_feature_spread`：编辑杂志专题 + 右侧横向条形叙事。
- 不同风格候选不能全部复用同一个变体。高质量候选还要写清表达系统：`title_anchor`、`body_pattern`、`proof_object`、`metric_pattern` 和 `role_signature`，避免变成“同一版式换背景”。
- `design_director_brief` 是主动设计约束，不是可有可无的说明文字。正式候选至少写清 `expression_system`、`style_intent`、`typography_system`、`color_strategy`、`chart_language` 和 `layout_rhythm`；`design_director_qa.js` 会用这些字段检查一致性、协调性和多样性。
- 文字、指标、图表标签必须由 PPT 文本对象承载。
- 柱状图、趋势线、节点和网格线必须由 PPT 形状承载。
- 不允许用大白框、大色块框或图表容器遮住背景；如果看不清，重做背景安全区或调整坐标。
- 深色、浅色、国潮、动漫等不同背景必须通过 `overlay_style` 调整字色、字号、图表色、图表透明度、网格线透明度和指标色，不允许一套文字/图表样式硬套所有风格。

### comparison

```json
{
  "layout": "comparison",
  "title": "方案对比",
  "claim": "这一页的核心判断",
  "items": [
    {"title": "方案 A", "body": "说明"},
    {"title": "方案 B", "body": "说明"}
  ],
  "source": "对比口径说明"
}
```

### executive_summary

```json
{
  "layout": "executive_summary",
  "title": "一页结论",
  "claim": "整套 deck 的主判断",
  "points": [
    {"label": "01", "title": "结论一", "body": "说明"},
    {"label": "02", "title": "结论二", "body": "说明"},
    {"label": "03", "title": "结论三", "body": "说明"}
  ],
  "source": "资料来源或口径说明"
}
```

### architecture

```json
{
  "layout": "architecture",
  "title": "系统架构",
  "claim": "这一页的核心判断",
  "layers": [
    {"title": "入口层", "body": "说明"},
    {"title": "能力层", "body": "说明"},
    {"title": "治理层", "body": "说明"}
  ],
  "source": "架构假设或资料来源"
}
```

### metrics

```json
{
  "layout": "metrics",
  "title": "价值测算",
  "claim": "这一页的核心判断",
  "metrics": [
    {"value": "20-35%", "label": "周期下降", "body": "口径说明"}
  ],
  "chart": {
    "labels": ["开发", "测试", "文档"],
    "values": [28, 22, 34],
    "unit": "%",
    "source": "示例测算模型，非外部事实"
  },
  "source": "资料来源或测算口径"
}
```

### roadmap

```json
{
  "layout": "roadmap",
  "title": "90 天落地路线",
  "claim": "这一页的核心判断",
  "phases": [
    {"period": "第 1-2 周", "title": "选场景", "body": "说明"},
    {"period": "第 3-4 周", "title": "跑闭环", "body": "说明"},
    {"period": "第 5-8 周", "title": "建治理", "body": "说明"}
  ],
  "source": "计划假设或资料来源"
}
```

### risk_next_steps

```json
{
  "layout": "risk_next_steps",
  "title": "风险与下一步",
  "claim": "这一页的核心判断",
  "risks": ["风险一", "风险二"],
  "actions": ["动作一", "动作二"],
  "source": "治理清单或资料来源"
}
```

### timeline

```json
{
  "layout": "timeline",
  "title": "执行节奏",
  "claim": "这一页的核心判断",
  "steps": [
    {"label": "1", "body": "确认主题"},
    {"label": "2", "body": "确认风格"}
  ],
  "source": "计划口径说明"
}
```

### closing

```json
{
  "layout": "closing",
  "title": "下一步",
  "body": "交付 PPTX"
}
```
