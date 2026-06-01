# 视觉型 PPT 生产规程

## 1. 先定故事

不要从页面设计开始。先让用户确认：

- deck 主题。
- 目标受众。
- 使用场景。
- 结论或行动目标。
- 页数范围。
- 是否有模板、品牌、参考图或禁用风格。

大纲未确认前，不进入风格样张。风格未确认前，不进入整套页面生成。

## 2. 风格候选

有高质量 `.pptx` 模板时，模板优先。先拆模板的：

- 标题层级。
- 字体气质。
- 色板。
- 留白。
- 图表语言。
- 图片策略。
- 常见页面类型。

没有模板时，默认做多套风格候选。候选不能只是“换背景和配色”，至少要在这些维度上不同：

- `title_anchor`：标题锚点。
- `body_pattern`：正文承载方式。
- `proof_object`：用什么对象证明观点。
- `metric_pattern`：指标呈现语法。
- `role_signature`：标题、正文、指标、图表在页面上的组合关系。

每套候选先写 `design_director_brief`，再生成页面。

## 3. 效果图母稿

效果图母稿可以包含示例标题、正文、指标和图表。它只用于判断：

- 视觉质感是否成立。
- 页面节奏是否成立。
- 信息密度是否舒服。
- 图表语言是否贴合主题。
- 是否有明确阅读安全区。

母稿不能直接作为最终 PPT 背景。

## 4. Clean Background

clean background 必须和母稿保持同一风格，但移除：

- 标题。
- 正文。
- 数字。
- 图表。
- 坐标轴。
- 标签。
- logo-like 伪文字。
- UI 文本。

prompt 必须明确：

- `text-safe zone`：低纹理、低噪声、适合正文。
- `chart-safe zone`：适合图表主线、柱体、标签。
- `low-detail transition area`：让内容层自然融入背景。
- `protected_empty_zone`：避免主体和装饰占用。

如果 clean background 破坏安全区，重做背景，不要靠加框补救。

## 5. 坐标蓝图

16:9 标准页用 `13.333 x 7.5` inches。坐标蓝图至少包含：

```json
{
  "title_zone": {"x": 0.7, "y": 0.5, "w": 5.8, "h": 0.8},
  "text_zone": {"x": 0.8, "y": 1.6, "w": 4.6, "h": 3.5},
  "chart_zone": {"x": 6.4, "y": 1.5, "w": 5.6, "h": 4.2},
  "metrics_zone": {"x": 0.8, "y": 5.5, "w": 5.2, "h": 0.8},
  "visual_focus_zone": {"x": 6.2, "y": 0.8, "w": 5.8, "h": 5.7},
  "protected_empty_zone": {"x": 0.7, "y": 0.4, "w": 11.9, "h": 6.5}
}
```

坐标蓝图是后续 PPTX 落版依据，不是装饰说明。

## 6. 可编辑层重建

正式 PPTX 中：

- 标题、正文、页脚、来源是文本对象。
- 指标是文本对象和形状组合。
- 柱状图、线图、时间线优先用 PPT 形状重建。
- 透明人物、物体、图标和装饰素材可以作为 PNG 图片层。
- 背景只承载视觉氛围，不承载关键信息。

需要透明素材时调用 `$transparent-visual-assets`。不要让主 PPT skill 自己临场发明抠图流程。

## 7. Deck Spec

每套正式 deck 应保留一个 `deck_spec.json`。它至少表达：

- deck 标题和主题。
- theme。
- slides。
- 每页 layout。
- 非标题页的 claim。
- 图表数据和 source。
- 图片和背景路径。
- 坐标蓝图。
- overlay 样式。

详细字段见 `deck-spec-schema.md`。

## 8. QA 门禁

交付前至少跑：

```bash
node scripts/validate_deck_quality.js --spec /absolute/path/deck_spec.json --report /absolute/path/qa_report.json
node scripts/build_deck_preview.js --spec /absolute/path/deck_spec.json --output-dir /absolute/path/preview
```

风格候选还要跑：

```bash
node scripts/design_director_qa.js --sample-dir /absolute/path/style-candidates --report /absolute/path/design-director-qa.json
```

验收失败时，修原因，不降级绕过。

## 9. 常见失败

- 把整页母稿直接当背景，导致 PPT 看着好但不可编辑。
- clean background 仍残留伪文字、数字或图表。
- 背景太花，正文和标签只能靠白框才能看清。
- 多套候选只是同一版式换颜色。
- 数据没有来源，却被包装成真实结论。
- 预览图能看，PPTX 里关键文字却不是可编辑对象。
