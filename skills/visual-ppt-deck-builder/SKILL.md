---
name: visual-ppt-deck-builder
description: Build polished, editable PowerPoint/PPTX decks from a topic, confirmed outline, visual style samples, AI-generated full-page visual drafts, clean backgrounds, transparent assets, charts, and editable text layers. Use when the user asks to create or rebuild a PPT/PPTX, pitch deck, course deck, report deck, proposal, product launch deck, strategy presentation, or visually rich slides that must be both beautiful and editable.
---

# Visual PPT Deck Builder

## 核心判断

这个 skill 不是“Markdown 转 PPT”，也不是“整页截图塞进 PPT”。它的目标是把主题变成可交付、可修改、视觉质量高的 `.pptx`。

最稳的路线是：

1. 用整页效果图母稿确定审美、构图和风格。
2. 再生成无文字、无图表、无数字的 clean background。
3. 最后用 PPT 原生文本、形状、图表和透明素材重建可编辑层。

这样既避免纯图片 PPT 不能改，也避免网页模板式 PPT 过于死板。

## 强制确认顺序

按下面顺序推进，不要跳步：

1. **确认主题**：主题、受众、场景、语气、页数范围、是否有品牌或参考资料。
2. **确认大纲**：先给章节和叙事顺序，不直接做页面。
3. **确认风格**：有用户模板时优先仿模板；无模板时做多套风格样章。
4. **确认 slide plan**：逐页写清标题、核心观点、证明对象、图表/素材需求。
5. **生成视觉母稿**：允许母稿里出现示例文字和图表，用来判断审美。
6. **生成 clean background**：背景必须去掉文字、数字、图表、标签和 UI 文本。
7. **重建可编辑层**：标题、正文、指标、图表、标签必须是 PPT 可编辑对象。
8. **运行验收**：质量检查、预览检查、可编辑层检查通过后再交付。

## 输入契约

开始正式制作前至少拿到这些信息：

- `topic`：deck 主题。
- `audience`：给谁看。
- `purpose`：希望对方看完做什么。
- `outline`：已确认的大纲。
- `visual_style`：已确认风格，或用户给的模板/参考图。
- `slide_plan`：每页标题、claim、内容、图表和素材需求。

如果用户只给一句主题，先产出大纲和风格方向让用户确认，不要直接生成完整 PPT。

## 视觉母稿到可编辑层

效果图母稿的职责是“审美判断”，不是最终交付物。正式 PPT 只能把它当参考。

对每个需要强视觉的页面：

1. 生成或取得一张完整效果图母稿。
2. 从母稿反拆页面坐标蓝图，至少包含 `title_zone`、`text_zone`、`chart_zone`、`metrics_zone`、`visual_focus_zone`、`protected_empty_zone`。
3. 生成 clean background，prompt 必须明确这些区域是低纹理、低噪声、可读安全区。
4. 用 `deck_spec.json` 描述页面内容、坐标、图表数据和 overlay 样式。
5. 用脚本生成 `.pptx`，再导出预览检查。

硬规则：

- 不要把带正文、数字、图表标签的整页图当背景。
- 不要用大白框、大色块框遮住背景来救可读性。
- 如果看不清，重做背景安全区或调整坐标。
- 没有来源的数据要标为示例或假设，不能伪装成事实。

详细生产规程见 `references/production-workflow.md`。

## 脚本契约

运行脚本需要 Node.js 和 `pptxgenjs`。Codex 桌面环境通常可以走 bundled runtime；如果本地直接运行时报缺依赖，先在执行环境安装 `pptxgenjs`，不要改脚本把依赖静默降级成截图方案。

### 生成 PPTX

```bash
node scripts/build_visual_pptx.js \
  --spec /absolute/path/deck_spec.json \
  --output /absolute/path/final_deck.pptx
```

输入：符合 `references/deck-spec-schema.md` 的 JSON spec。
输出：可编辑 `.pptx`。
完成证据：文件存在，页数与 spec 一致，关键文本出现在 PPT slide XML 中。

### 质量检查

```bash
node scripts/validate_deck_quality.js \
  --spec /absolute/path/deck_spec.json \
  --report /absolute/path/qa_report.json
```

完成证据：`qa_report.json.ok` 为 `true`。失败时先修 spec、来源、claim 或素材路径，不要跳过。

### 生成预览

```bash
node scripts/build_deck_preview.js \
  --spec /absolute/path/deck_spec.json \
  --output-dir /absolute/path/preview
```

完成证据：`preview/contact-sheet.svg` 和逐页 `slide-*.svg` 存在，并能看出页面没有空白、重叠、模板词或明显不可读区域。

### 生成风格候选

```bash
node scripts/build_style_candidates.js \
  --output-dir /absolute/path/style-candidates \
  --topic "<deck topic>" \
  --background-source-dir /absolute/path/generated-backgrounds
```

正式候选必须提供真实 raster 背景目录。只有测试可以使用 `--allow-placeholder-backgrounds`。

完成证据：每套候选都有 PPTX 样板、PNG 预览、prompt、QA 报告和设计总监检查结果。

## 验收标准

交付前逐项确认：

- 用户已确认主题、大纲、风格和 slide plan。
- 最终输出是 `.pptx`，不是一组图片。
- 标题、正文、指标、图表标签可编辑。
- 图表优先由 PPT 原生形状或图表承载。
- 背景是 clean background，不含烤进去的文字和图表。
- 透明素材边缘干净，叠在深浅背景上都能读清。
- 质量检查、预览检查和无模板词检查通过。

## 报告口径

只允许用这些状态：

- `completed`：PPTX、预览、QA 报告都存在且通过。
- `needs_manual_check`：自动检查通过，但视觉审美或模板仿制需要用户看样张确认。
- `blocked`：缺主题、大纲、模板、素材、图像生成能力、脚本依赖或文件权限，导致无法继续。

报告时说明：已生成什么、哪些可编辑、哪些需要用户确认、测试是否通过。

## 需要时读取

- `references/production-workflow.md`：整页母稿、clean background、坐标蓝图和可编辑层重建的详细规程。
- `references/deck-spec-schema.md`：`deck_spec.json` 支持字段和 layout。
- `references/research-notes.md`：PPT 生成路线调研和取舍。
