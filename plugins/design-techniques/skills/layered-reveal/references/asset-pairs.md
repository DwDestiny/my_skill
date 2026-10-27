# 成对图生产 SOP

> v0.1 · 2026-10-27 · 来源：一次行业宣讲网页（2026-10-23）的三对图

SKILL.md 第 4 节 SOP 第 3 步读本文件。

## 1. 原则

1. 两层是同一构图、同一机位、同一物件位置。差别只在你要揭示的那一维（材质、时间、里外、状态）。
2. 先生成细节最多的一层，再以它为参考图生成简化层。细节多的一层通常是照片、成衣、白天、建成后、内部结构。
3. 反过来做会失败：以简化层为参考生成照片时，模型会自己补细节（台灯、笔筒、衣领、发型），两层对不上，揭示时出现重影。
4. 画面元素少、尺度大、留白多。每个主要物件就是一个热点。

## 2. 步骤

1. 用生图工具（本机为 `image-gen` skill，gpt-image 模型）生成第一层，尺寸 1536×1024。
2. 检查第一层：人脸与手有无畸形，屏幕上的字只作纹理，不承载信息，画面里没有真实品牌标识。
3. 以第一层为参考图，用第 3 节的提示词生成简化层，一次 2 到 3 张。
4. 对每张候选做差值叠图（第 4 节），截图比较。
5. 选人物、物件边缘几乎抵消的一张。
6. 转 webp，每张不超过 300 KB：`magick in.png -resize 1536x -quality 80 out.webp`。
7. 页脚写"场景图为生成示意"。

## 3. 提示词模板

第一层（细节层）：

```
A [主体与动作] in [空间], [机位：eye-level side view / wide frontal view], sparse composition,
only [列出 3–6 个物件], large empty dark background, single warm [光源] from [方向],
cinematic, realistic photo, 3:2, no text, no logos.
```

第二层（简化层，以第一层为参考图）：

```
Redraw the reference image as [简化层材质：a white marble bas-relief / a muslin toile on a
dress form / a night scene / an X-ray]. Keep it pixel aligned with the reference:
trace every contour, keep every object at the same position and size,
do not move, add or remove any object. Same camera, same framing, same aspect.
[材质细节：soft raking light from the left, fine marble grain], dark background.
```

换层关系时只改第二层的"材质"一句。例如：

| 层关系 | 第二层材质句 |
|---|---|
| 浮雕 → 照片（已验证） | `a sparse white marble bas-relief carved into a dark wall` |
| 白坯 → 成衣 | `the same garment as an unbleached muslin toile with chalk lines` |
| 昼 → 夜 | `the same scene at night, lights off, moonlight only` |
| 外壳 → 内部 | 先生成爆炸内部图，再以它为参考生成 `the closed aluminium shell` |
| 旧 → 新 | 先生成今天的街口，再以它为参考生成 `the same street in the 1980s, film photo` |

## 4. 差值叠图挑图

把两层叠在一起，用 `mix-blend-mode:difference` 截图。对齐好的一张，人物与物件边缘几乎变黑。

```html
<div style="position:relative;width:1536px;height:1024px">
  <img src="top.webp" style="position:absolute;inset:0">
  <img src="base-candidate-1.webp" style="position:absolute;inset:0;mix-blend-mode:difference">
</div>
```

也可以用 ImageMagick 直接出差值图：

```
magick top.webp base-candidate-1.webp -compose difference -composite diff-1.png
```

判断：

| 差值图 | 结论 |
|---|---|
| 只剩材质纹理，轮廓线几乎看不见 | 用这张 |
| 人物或物件有一圈亮边 | 偏移了几像素，换一张 |
| 出现整块亮区 | 物件被移动或增删，重新生成 |

如果三张都偏差超过光圈半径的 5%，改用"同一张照片 + 着色器算出的简化层"（例如边缘检测出线稿）。

## 5. 三层以上

光越强揭得越深时，按细节从多到少生成：内部数据层 → 照片层 → 浮雕层。每一层都以上一层为参考图。着色器改法见 `ink-shader.md` 第 5 节。
