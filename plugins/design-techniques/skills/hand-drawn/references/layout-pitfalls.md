# 布局与渲染的细坑

> 做到“截图错位、混合失效、阴影不对、换行孤字”时读。

| 现象 | 原因 | 改法 |
|---|---|---|
| 390 宽截图错位 | 无头 Chrome 布局宽度最小 500 px | 用 iframe 包一层（`m.html?w=390&h=844&q=`），桌面截图也走 iframe |
| 下划线压到字上 | 截图时视口高度变（布局 813、截图 900），整屏居中的内容移动，按整屏坐标画的装饰留在原地 | 装饰画布挂在文字所在容器里；ResizeObserver 同时观察标题和整屏 section |
| 浅色卡纸画不亮 | `multiply` 永远不会变亮 | 卡纸用普通混合：纸纹 pattern 缩放 1/DPR，再盖 `rgba(255,252,244,.42)` |
| multiply 压不到纸纹 | 父元素有 z-index、opacity<1、mask 或 clip-path，成了隔离组 | 容器保持 `z-index:auto`；卡纸 `z-index:-1` 垫后面；要淡入的组把 multiply 设在组上 |
| 影子大小随屏变 | canvas 的 shadowBlur / shadowOffset 按设备像素算，不受变换影响 | 手乘 DPR·k |
| 颗粒在画布边上断开 | 每块画布从 (0,0) 取纸纹 | `paperPattern` 用 (rect + scroll)·DPR 平移 |
| 高亮比字宽 | 按网格单元量宽度 | 用 Range 量文字本身 |
| 胶带拉满整行 | 手机上第一组 `display:block` | 加 `width:fit-content` |
| 断出“哪 / 一步” | `text-wrap:balance` 只看长度 | 词组用 `.nw` 的 nowrap span 包住 |
| 手机标题剩孤字 | 字号与行宽不配 | `.nw` 分组 + 调字号（演示页手机 38px） |
| 悬停被挡 | 旋转画布的外接框盖住别的元素 | 画布 `pointer-events:none`，另放旋转的透明热区，`.hit:hover + .card`；注意选择器优先级 |
| 图内标签跑到别处、字号不对 | 首屏标签用了通用类名（`.plate`），和另一屏同名类的定位规则叠在一起 | 每屏的类名带前缀（`.sc-t.sign`），或选择器写在屏内（`.s01 .sign`）；加新类前先 `grep` 全页 |
| 标题像镂空模板字 | 墨缺口遮罩太强 | 大字遮罩最多去掉 30%，只在 h < .22 的深坑处（`paper.md` 第 1 节） |
| 隐藏的屏报错 | `display:none` 的屏宽为 0 | 画之前检查 `offsetParent` |
| 本机没 unzip | — | `python3 -I -c "import zipfile..."` 解压 |
| 手机页面横向溢出几十像素 | 卡纸和彩铅画布画在元素框外（外扩约 0.8 到 2 倍字号），竖排后伸出屏宽 | 页容器 `overflow-x:clip`（不用 `hidden`：它让纵向也变成滚动容器，会裁掉上下伸出的卡纸）；桌面多列卡片的列间距至少留两倍外扩 |
