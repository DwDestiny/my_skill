# 资产清单（样例）

无外部文件。本页全部资产在页面里现场生成，生成方式见各行。

| 编号 | 用在 | 种类 | 生成方式 | 文件 |
|---|---|---|---|---|
| A01 | s0 首屏 | mechanism | three.js 程序化几何，`buildMachine` 工厂产出叠片机 | 无 |
| A02 | s1 成品 | data | 自有页面截图，运行页面后用浏览器截取，不得生成冒充 | 无（实现时截取） |
| A03 | s1 读数 | mechanism | HTML 与 SVG 自绘刻度尺 | 无 |
| A04 | s2 八步 | mechanism | three.js 程序化几何，`?export` 参数导出站点小图 | 无（导出时生成 `assets/*.jpg`） |
| A05 | s3 点头 | mechanism | three.js 程序化几何，S3 近景静帧 | 无 |
| A06 | s4 防模板 | mechanism | three.js 程序化几何，发牌口与方向卡 | 无 |
| A07 | s5 边界 | mechanism | SVG 自绘护栏与禁区标签 | 无 |

`image-gen` 不上页面，只用于方向单里的目标板。
