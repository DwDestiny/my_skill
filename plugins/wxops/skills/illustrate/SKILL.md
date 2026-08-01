---
name: illustrate
description: Use when 配图、做封面、生成文章插图、公众号封面尺寸, or producing cover and body images for a drafted article with pluggable image sources (AI generation or human-supplied).
---

# illustrate — 配图工位

## 核心原则

- **封面必须有**：公众号无封面不能发；首图 = 第二标题——核心数字/身份/结果打在图上，手机缩略图可读
- **通路可插拔**：图从哪来（AI 生成/人工供图）可换，**尺寸规范与落盘约定不变**——下游 publish 站只认约定
- **账号视觉一致性**：配色/字体感觉/构图习惯读 persona.md「视觉 tokens」段，一个号一张脸

## 尺寸规范（写死，平台硬约束）

| 图 | 尺寸 | 比例 | 用途 |
|---|---|---|---|
| 封面大图 `cover.jpg` | 900×383 | 2.35:1 | 头条封面、分享卡 |
| 封面方图 `cover-square.jpg` | 200×200 | 1:1 | 次条小图（建议同素材裁切） |
| 正文图 `fig-01.jpg` … | 宽 ≥ 1080 | 不限 | 正文插图，按序号命名 |

落盘：`~/.wxops/accounts/<slug>/images/<topic-slug>/`，文件名按上表约定。

## 工作流

1. **列图单**：读定稿 `drafts/<topic-slug>/draft.md`，列出需要的图——封面（必须）+ 正文图（哪些段落需要配图、各自表达什么）。图单呈给用户确认，不多配：一张不服务内容的图就是一处加载负担。
2. **读视觉 tokens**：persona.md「视觉 tokens」段——封面风格、首图大字规则、正文图习惯。首图大字用 title-smith 环节的首图建议（≤ 12 字）。
3. **选通路出图**：
   - **通路 A · AI 生成（钦定 Codex 生图）**：按图单逐张出 prompt（内容 + 视觉 tokens + 目标尺寸），走本机 codex 生图通路（示例：`codex exec "<生图任务>"`，以本机 codex 配置为准）。生成后按命名约定落盘。
   - **通路 B · 人工供图**：把图单（含每张的尺寸与内容要求）交给用户，用户备好后放进 `images/<topic-slug>/` 对应文件名。
   - 两通路可混用（封面 AI、正文截图人工是常态——教程文的真实截图不可替代）。
4. **尺寸校验**（脚本说话）：

   ```bash
   sips -g pixelWidth -g pixelHeight ~/.wxops/accounts/<slug>/images/<topic-slug>/cover.jpg
   ```

   封面必须精确 900×383；不合尺寸先裁切（`sips -c 383 900` 中心裁切）再复验。
5. **终检呈图**：全部图与所在段落对应关系呈给用户过目，人点头即本站完成。

## 红线

- 封面缺失或尺寸不符不算完成——publish 站（P5）会再拦一次，别把问题传下去
- 生成图不冒充实拍/截图：教程步骤图必须是真实截图，AI 生成只用于封面与概念配图
- 图内文字（首图大字）过一遍 persona 人设禁忌——标题党红线同样适用于图
- 素材版权：人工供图确认可商用；他人图表引用在正文标注来源
