# 生成资产 · E1 · 2026-10-16

生成工具：`image-gen`（用户 2026-10-16 授权）。提示词为英文，不含项目名、人名、路径。未从网站取图。

| 编号 | 文件 | 尺寸 | 用途 | 提示词要点 | 看图结论 | 采用 |
|---|---|---|---|---|---|---|
| A01 | `A01-hero.jpg`（269 KB） | 1536x1024 | 首屏主视觉：硫酸纸覆施工图 | top-down macro, tracing paper over construction drawing, title block lower right, side light upper left, empty left third, no text | 左侧留白干净，构图与光向符合方向单。图签内红章有极小的伪字形，页面上被自绘图签遮住，可接受 | 是 |
| A02 | `A02-tracing-texture-512.jpg`（34 KB） | 512x512，由 1024 缩小 | 舞台区纸纹、硫酸纸层 | seamless tracing paper vellum, fine fibres, low contrast, no text | 纹理好，但整体偏深（约 L 0.78）。只能 multiply 叠加，透明度不超过 0.35 | 是（限用法） |
| A03 | `A03-s8-seal.jpg`（215 KB） | 1536x1024 | s8 章首：图签角与出图章 | macro title block corner, square vermilion seal, empty inner area, no characters | 无伪字，光向一致，左半留白可压标题 | 是 |

共生成 3 张，采用 3 张。A04（s2 四层图纸）留到 S5 用 `edit --ref A01` 生成。

## v0.2 编辑（2026-10-16，S3 第 2 轮）

| 编号 | 文件 | 尺寸 | 改动 | 提示词要点 | 看图结论 | 采用 |
|---|---|---|---|---|---|---|
| A01 v2 | `A01-hero.jpg`（231 KB，覆盖 v1） | 1536x1024 | `image-gen edit --ref A01-hero.jpg`：去掉照片右下角自带的图签表格与红章，用同质硫酸纸与轴网线补齐 | remove the title block table and the small red seal in the lower right, fill with the same translucent tracing paper and faint grid continuation, keep everything else identical, no text | 图签与红章已去掉，补齐区域纹理与光向一致，平面草图、铅笔、直尺、左侧留白不变。首屏只剩页面自绘的 SVG 图签（评审必改项 4） | 是 |

v0.3 核对（2026-10-16，S3 第 2 轮必改 3）：第 2 轮评审在 390 首屏看到的"淡矩形加~"不是 A01 v2 的擦除残留。它是页面自己的硫酸纸层 `.tracing`（SVG 里有一条 ~ 形铅笔线），390 下落在照片左上。A01 v2 不重做，文件不变。方向单 v0.3 把硫酸纸层挂到图签上，390 下揭开后淡出到 0。390 截图 `05-评审/shots/s3-v0.3/390-hero.jpg` 已核对，照片上无矩形。

v1 的 A01 不再保留。原因：v1 自带图签与页面 SVG 图签形成双图签。编辑原始 PNG 已删除。

压缩记录（2026-10-16）：原始 PNG 每张约 3 MB，已用 Pillow 12.3（临时 venv）转为 JPG，质量 82，渐进式。A02 缩为 512 平铺。原始 PNG 已删除，不入库。后续如需 `edit --ref`，用 JPG 作参考图。

## A04 系列（2026-10-16，S5 前由协调者生成）

| 编号 | 文件 | 尺寸 | 用途 | 提示词要点 | 看图结论 | 采用 |
|---|---|---|---|---|---|---|
| A04-1 | `A04-1.png` | 1024x1024，透明底，PNG-8 | s2 舞台第 1 层：概念草图 | `edit --ref A04-2.png`：same floor plan as loose graphite concept sketch, main walls and column circles only, transparent background, no text | 第 1 版用 A01 作参考，朝向与其余三张不一致，已删。第 2 版以 A04-2 为参考，轮廓同一栋楼，线条松、略歪，符合"草图"。与 2 到 4 不逐像素对齐，B 按包围盒对齐 | 是 |
| A04-2 | `A04-2.png` | 同上 | 第 2 层：方案设计 | `edit --ref A01-hero.jpg`：preliminary design drawing, clean thin ink lines, walls and openings, no dimensions, transparent | 干净单线，带家具，无文字 | 是 |
| A04-3 | `A04-3.png` | 同上 | 第 3 层：施工图 | construction drawing, double-line walls, door swings, dimension lines, axis grid bubbles | 双线墙、轴号圈、尺寸线齐全，与 A04-2 同一平面，略大一圈 | 是 |
| A04-4 | `A04-4.png` | 同上 | 第 4 层：竣工图 | as-built, hatched wall fills, a few red revision clouds | 墙体填充，3 处红色云线，无文字 | 是 |

压缩：1254 缩到 1024，`quantize(256)` 无抖动，原始 PNG 已删。
