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

效果图母稿是正式视觉系统的起点，不是可选装饰。对强视觉页面，不要先找一张 clean background 再往上贴文字；必须先生成整页 PPT 效果图，让背景、内容、图表和装饰元素在同一张图里自然配套。

效果图母稿可以包含示例标题、正文、指标和图表。它用于判断：

- 视觉质感是否成立。
- 页面节奏是否成立。
- 信息密度是否舒服。
- 图表语言是否贴合主题。
- 是否有明确阅读安全区。
- 文案层、图表层和背景层是否像同一个设计系统。

母稿不能直接作为最终 PPT 背景。它必须保存为 `visual_draft_image`，并在 `deck_spec.json` 中留下路径，作为后续拆解和验收依据。

母稿失败的典型表现：

- 背景像科技海报，图表像普通办公模板。
- 正文和指标只是浮在背景上，不像从画面结构里长出来。
- 一页看着能用，但换到下一页时完全没有延展语法。
- 只能靠加大白框、大色块框才能读清内容。

出现这些情况时，不进入 clean background，直接重做母稿。

## 4. Clean Background

clean background 必须从已认可的母稿派生，保持同一光影、材质、构图、留白和视觉元素关系，但移除：

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

禁止事项：

- 禁止跳过整页母稿，直接从随机背景图开始。
- 禁止一张背景铺完整套 PPT，除非每一页都有对应母稿证明这套视觉系统能延展。
- 禁止把带文字、数字或图表的母稿当作 `background_image`。

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
- 每个强视觉页的 `visual_draft_image`。
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
python3 scripts/inspect_pptx_editability.py --pptx /absolute/path/final_deck.pptx --spec /absolute/path/deck_spec.json --report /absolute/path/editability_report.json
```

`build_deck_preview.js` 生成的是结构快检 SVG，不足以判断真实 PPT 渲染质感。强视觉 deck 必须再用 Keynote、PowerPoint 或 LibreOffice 从 `.pptx` 导出 PNG/PDF 预览，确认最终渲染没有文字挤压、元素割裂或背景不搭。

风格候选还要跑：

```bash
node scripts/design_director_qa.js --sample-dir /absolute/path/style-candidates --report /absolute/path/design-director-qa.json
```

验收失败时，修原因，不降级绕过。

## 9. 常见失败

- 把整页母稿直接当背景，导致 PPT 看着好但不可编辑。
- 跳过整页母稿，导致背景、正文、图表和装饰元素各说各话。
- clean background 仍残留伪文字、数字或图表。
- 背景太花，正文和标签只能靠白框才能看清。
- 多套候选只是同一版式换颜色。
- 数据没有来源，却被包装成真实结论。
- 预览图能看，PPTX 里关键文字却不是可编辑对象。
