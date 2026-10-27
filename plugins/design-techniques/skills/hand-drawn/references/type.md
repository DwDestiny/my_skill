# 手写字

> 做到“选字体、子集化、逐字抖动或字体加载出问题”时读。

## 1. 选字

| 用途 | 字体 | 来源 | 许可 |
|---|---|---|---|
| 标题、图内标签 | 霞鹜漫黑 LXGW Marker Gothic v1.004（记号笔） | github.com/lxgw/LxgwMarkerGothic release v1.004 | OFL-1.1 |
| 正文、批注 | 小赖 Xiaolai v3.126（细钢笔） | github.com/lxgw/kose-font release v3.126 | OFL-1.1 |

- Hershey 单线字体没有中文，只能用于拉丁字母。
- OFL 允许发布子集，许可证文本要随字体一起放（`fonts/OFL-*.txt`）。
- 字体族名改成自己的（例如 `HD Marker`），不沿用原名，符合 OFL 对改版字体的要求。

## 2. 子集化

`scripts/fonts.sh` 扫给定 HTML/JS 的**全部字符**（JS 字符串、canvas `fillText` 的字都在源码里），补数字和常用标点，用 fontTools 输出 woff2。改了任何文字就重跑。演示页两款合计约 170 KB。

## 3. 逐字抖动

- `handset(el, seed, amp)` 把文字逐字包成 `.ch`，每字随机基线（±.035em）和倾角（±1.6°），写在行内 transform 里。
- “抖一下”动画用独立的 `translate`、`rotate` 属性 + `steps(1,end)`，才能和行内 transform 叠加；逐字错开 `--i × 30ms`。
- 图内标签用 `label()`：HTML 绝对定位，坐标按图的逻辑单位换算成百分比，字号用 `cqw`，容器设 `container-type:inline-size`。

## 4. 加载

- `document.fonts.ready` 可能在字体开始加载前就返回。用 `fontsReady([["HD Marker","样例字"],["HD Hand","样例字"]])` 显式加载再画。
- `font-display:block`，避免先闪楷体再跳成手写字。
- 换更宽的手写字后，图注箭头会压到图注：先排 HTML 标签，再从标签右端起笔画箭头。
