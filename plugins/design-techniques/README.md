# design-techniques · 设计手法库

> v0.1.1 · 2026-10-27 · 维护：DwDestiny

一个 Claude Code 插件。它只收在真实项目里做出好效果的视觉手法。每个手法带效果图、适用场景、所需工具与依赖，以及一个完整的风格化 skill：规范、SOP、起手代码和踩坑。

没有实践过、没有达标的手法不进来，只记在 [`CANDIDATES.md`](CANDIDATES.md)。

## 手法

### 叠图晕染 · layered-reveal

![叠图晕染效果](skills/layered-reveal/showcase/cover.webp)

几层构图对齐的画面叠在一起。指针、灯或滚动推开一道水墨般的边，揭示下一层。适合宣讲页、品牌页、产品页和前后对比，也就是要讲"表面之下是什么"的内容。

所需工具：生图（成对图）、WebGL2。详见[手法卡](skills/layered-reveal/CARD.md)。

### 手绘风格化 · hand-drawn

![手绘风格化效果](skills/hand-drawn/showcase/cover.webp)

用代码在有颗粒的纸上画钢笔线、彩铅和手写字。首屏是一整幅手绘画，标题写在画里；讲解图与文字用同一种颜色对应。适合讲解页、课程页、方法图和流程图，也就是要让人看懂并记住关系的内容。

所需工具：Canvas2D、开源手写字体（OFL）。详见[手法卡](skills/hand-drawn/CARD.md)。

## 安装

在 Claude Code 2.1.275 或更新版本里，一步安装：

```text
/plugin install design-techniques --marketplace DwDestiny/my_skill
```

更早的版本分两步：

```text
/plugin marketplace add DwDestiny/my_skill
/plugin install design-techniques@maizong-skills
```

## 使用

1. 直接说需求，例如"做一个手绘风的课程讲解页"或"首屏要鼠标一照就显出另一层"。Claude 会选中对应手法。
2. 不确定用哪个手法时，运行 `/design-techniques:catalog`。它列出手法、效果图和适用场景，帮你选。
3. 点名手法时，运行 `/design-techniques:layered-reveal` 或 `/design-techniques:hand-drawn`。

每个手法的起手页面在 `skills/<手法>/templates/starter/`，用浏览器直接打开就能看效果。

## 结构

```text
design-techniques/
├─ .claude-plugin/plugin.json
├─ CANDIDATES.md            候选池：未收录的手法、外部 skill、试过没达标的方向
├─ evals/                   触发与选择评测用例
└─ skills/
   ├─ catalog/              入口索引：选手法，再交给子 skill
   ├─ layered-reveal/       叠图晕染
   └─ hand-drawn/           手绘风格化
```

一个手法目录的内容：

| 文件 | 内容 |
|---|---|
| `SKILL.md` | 完整风格化 skill：何时用、变体空间、风格规范、SOP、起手代码说明、载体与降级、踩坑 |
| `CARD.md` | 手法卡：效果、本质、适合与不适合、已验证与可衍生变体、工具、依赖与许可、实践记录 |
| `showcase/` | 效果图：`cover.webp`（1440×900）、过程帧、`mobile.webp`（390 宽） |
| `templates/starter/` | 能在浏览器直接打开的起手页面，同时是效果演示页 |
| `references/` | 细节文档，SOP 做到对应步骤时读 |

## 收录标准

一个手法同时满足下面四条，才进 `skills/`：

1. 在真实项目里用过。
2. 用户评价效果达标，记下原话与日期。
3. 有效果图。
4. 起手代码能在浏览器直接打开，依赖实测过。

收录步骤见 [`skills/catalog/SKILL.md`](skills/catalog/SKILL.md) 第 4 节。

## 评测

在插件根目录运行：

```bash
claude plugin eval . --trust-plugin --runs 1 --max-cost-usd 5 --no-publish
```

用例检查三件事：自然说法下是否选中正确的手法；问"有哪些手法"时是否列出全部已收录手法；后台表格类需求是否不硬套视觉手法。

## 许可

插件代码与文档使用 MIT 许可，见 [`LICENSE`](LICENSE)。手绘风格化使用的字体是 SIL Open Font License 1.1，许可文件随字体放在该手法的起手目录里。效果图里的画面为 AI 生成的通用场景，文字已换成中性内容。
