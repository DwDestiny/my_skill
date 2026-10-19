# 设计资产生成

S3 写资产生成清单，S5 按清单生成。用户 2026-10-16 已授权直接用已有的生图 skill 生成设计资产，不逐次问。从网站取图仍先问用户。

## 1. 资产生成清单格式

写在 `02-方向单/direction.md` 与方向单 HTML 的"资产生成清单"区块。每个资产一行。

| 列 | 写什么 |
|---|---|
| 编号 | `A01`、`A02`。页面规划与 `ASSETS.md` 用同一编号 |
| 用途与位置 | 哪一屏、哪个区块、承载什么意思 |
| 类型 | hero 主视觉 / 章节插画 / 纹理 / 图标剪影 / 信息示意图 / 视频 / 3D 件 |
| 尺寸 | `1536x1024`、`1024x1536`、`1024x1024`，或 CSS 尺寸 |
| 风格约束 | 引用方向单的四维决定原词与配色类，写主色色值 |
| 生成方式 | `image-gen` / 生视频 skill（待提供）/ `anatomy` / CSS 或着色器 |
| 提示词要点 | 英文关键词，3 到 6 个 |
| 备选 | 生成失败或不合格时用什么 |

## 2. `image-gen` 用法摘要

详细用法读 `~/.claude/skills/image-gen/SKILL.md`。

1. 命令：`python3 ~/.claude/skills/image-gen/scripts/imggen.py gen --prompt "<英文提示词>" --out <临时目录>/<编号>.png --size 1536x1024`。
2. 尺寸只有三种：`1536x1024`、`1024x1536`、`1024x1024`。透明底加 `--transparent`。
3. 用同一角色或风格重画：`edit --ref <参考图> --prompt ...`。
4. 提示词用英文。写主体、构图、光、色调、留白位置，结尾写 "no text, no logos, no watermark"。
5. 每张约 20 秒。先生成 1 张试风格，再批量。
6. 生成后用 Read 工具逐张看图。检查乱字、logo、多余肢体、风格偏离。不合格重生成，最多 3 次，再用备选。
7. 压缩。生成的 PNG 未压缩，每张约 3 MB。目标：hero 不超过 300 KB，章节图不超过 200 KB，平铺纹理缩到 512 像素且不超过 50 KB。做法：
   1. 示例环境没有 Pillow 时，先建临时环境：`python3 -m venv <临时目录>/imgenv && <临时目录>/imgenv/bin/pip install -q pillow`。
   2. 照片类转 JPG：`Image.open(src).convert("RGB").save(dst, "JPEG", quality=82, optimize=True, progressive=True)`。需要透明底的图保留 PNG，用 `quantize(256)` 后保存。
   3. 平铺纹理先 `resize((512, 512), Image.LANCZOS)` 再保存。
   4. 删除原始 PNG。后续 `edit --ref` 用压缩后的文件作参考图。
8. 合格后放到项目 `assets/generated/`，写 `ASSETS.md`，记录压缩前后体积。

> **警告**：不把项目源码、用户隐私、客户名称、示例环境路径写进提示词。不打印、不记录、不提交密钥。

> **注意**：`HTTP 5xx` 或超时时，等几秒重试一次。仍失败就用备选，并报告原因。不换用别的站点或模型厂商。

## 3. 按资产类型的提示词模式

### 3.1 hero 主视觉

```text
<主体> in <场景>, <镜头：35mm / macro / top-down>, <光：single soft side light from left>,
palette of <主色英文描述> and <灰阶描述>, large calm empty area on the <left/right> for text overlay,
<材质词：paper grain / frosted glass>. No text, no logos, no watermark.
```

### 3.2 章节插画

```text
Editorial illustration of <章节意象>, <风格：flat gouache / line and wash / cut paper>,
limited palette: <3 个色值的英文描述>, consistent stroke weight, plain <底色> background,
same style as a series of <N> chapter openers. No text, no logos.
```

同一套插画先出 1 张，再用 `edit --ref` 以它为风格参考出其余各张。

### 3.3 纹理与材质贴图

```text
Seamless tileable texture of <材质：handmade paper / fine film grain / brushed aluminium>,
even lighting, no visible seams, low contrast, neutral <色调>. No text, no objects.
```

生成后在页面里平铺两次检查接缝。纹理能用 CSS 或 SVG 噪声做时，优先用代码。

### 3.4 图标剪影

```text
A set of <N> monochrome flat silhouette icons of <主体>, one row, plain white background,
solid shapes, no gradients, readable at 24 pixels. No text.
```

生成后缩到真实尺寸检查可读性。需要精确矢量时，再描摹为 SVG。

### 3.5 信息示意图

```text
Clean explanatory diagram of <机制>, <版式：left to right flow / layered cutaway>,
soft <配色> palette, generous spacing. Labels in Simplified Chinese exactly as quoted: "<标签1>", "<标签2>".
No other text, no logos, no numbers except those quoted.
```

> **注意**：图里的数字是画出来的，不是计算出来的。真实数据用 `dataviz` 画。生成的示意图标"示意"，小于 12px 的字逐字核对。

## 4. 生视频 skill（预留）

待用户提供，到位后补充用法。

现在的替代：视频背景用 CSS 动画或着色器动画（`examples/mechanisms/fluid-noise/`）。需要实物运动时，用图片序列（`examples/mechanisms/image-sequence/`），帧用 `image-gen` 的 `edit` 条带法生成。

## 5. 3D 生成 skill（预留）

待用户提供，到位后补充用法。

现在的替代：

1. 等轴测示意用 `anatomy` skill 的 SVG。
2. 需要真 3D 时用 three.js 程序化几何（`examples/mechanisms/webgl-scene/`）。用基础几何体组合，不加载外部模型文件。

## 6. 许可记录 `ASSETS.md`

放在项目 `assets/generated/ASSETS.md`。每个资产一行。

| 列 | 写什么 |
|---|---|
| 编号 | 与资产清单一致 |
| 文件 | 相对路径 |
| 用途 | 哪一屏、哪个区块 |
| 生成方式 | `image-gen` 加模型名，或代码、`anatomy` |
| 提示词要点 | 英文关键词，不写完整提示词中的敏感内容 |
| 日期 | YYYY-MM-DD |
| 尝试次数 | 生成几次后采用 |
| 许可说明 | "生成图，版权归属在法律上不确定，不并入代码许可证" |

素材进入项目前，在报告里告诉用户生成了几张、用在哪里。
