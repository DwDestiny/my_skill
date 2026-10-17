# 机制示例

机制示例只给技术，皮肤来自方向单。配色、字体、版式、文案都不可照抄。

每个示例是一个单文件 HTML。文件头注释写明机制、适合与不适合、依赖版本、许可、Reduce Motion 退路、性能预算、不可照抄的部分和三步接入方法。

## 已交 21 个（P1 六个，第二轮六个，P2 九个）

| id | 机制 | 依赖（固定版本） | 文件体积 | Reduce Motion 行为 | 已验证项 |
|---|---|---|---|---|---|
| `webgl-scene` | three.js 程序化分层板片与节点连线，鼠标视差，滚动推镜头 | three 0.186.0（jsDelivr） | 5.8 KB | 停自转与漂移，只在滚动和缩放时重画一帧 | 控制台 0 错误。两种模式截图完整。窄屏拉远镜头 |
| `fluid-noise` | 全屏片元着色器 fbm 噪声，三个 CSS 变量传入 uniform | 无（原生 WebGL2） | 4.9 KB | 冻结时间，只画一帧 | 控制台 0 错误。两种模式截图完整 |
| `grain` | SVG feTurbulence 静态颗粒，可选 steps() 动态颗粒，页内算正文对比度 | 无 | 5.4 KB | 动态颗粒关闭，保留静态层 | 控制台 0 错误。对比度读数 11.66:1，最坏 8.13:1 |
| `glass` | backdrop-filter 玻璃浮层，只用于浮层 | 无 | 3.9 KB | 悬停位移关闭。少透明与高对比改实色 | 控制台 0 错误。两种模式截图完整。少透明与高对比分支未在浏览器中触发 |
| `scroll-story` | GSAP ScrollTrigger 固定舞台，三章，SVG 状态切换，`--p` 由 scrub 驱动 | gsap 3.15.0、ScrollTrigger 3.15.0（jsDelivr） | 5.5 KB | 不建 ScrollTrigger，三章顺序静态显示，`--p` 为 1 | 控制台 0 错误。pin 与章节切换截图确认。库加载失败时走静态版（未单独测） |
| `image-sequence` | canvas 按滚动进度绘 24 帧程序化序列，预加载、进度映射、低端机降帧 | 无 | 5.3 KB | 显示最后一帧 | 控制台 0 错误。两种模式截图完整。低端机降帧路径已触发（12 帧） |
| `scroll-camera-path` | three.js 四个站点，相机沿 CatmullRomCurve3 随滚动穿行，HTML 叠层文字 | three 0.186.0（jsDelivr） | 6.0 KB | 不绑滚动，站点导航按钮切换 4 个静态视图 | 控制台 0 错误。起点、中段、页脚截图确认能滚到页脚。pin 滚动距离 3 屏 |
| `css-scroll-timeline` | 零 JS，`animation-timeline: view()` 与 `scroll()` 做入场与进度条，`@supports` 包住 | 无 | 3.8 KB | `animation: none`，显示终态 | 控制台 0 错误。两种模式截图完整。不支持的浏览器路径未测 |
| `fluid-ink-pointer` | WebGL2 染料双缓冲，curl noise 加指针速度回溯采样，文字在实色面板上 | 无 | 6.7 KB | 预置染料，推进 30 步后画一帧并停止 | 控制台 0 错误。指针拖出墨迹截图确认。简化版，无压力求解 |
| `capability-tiering` | 探测 6 项信号，判 full / lite / static，写入 `window.__tier`，三档舞台 | 无 | 6.1 KB | 直接判 static | 控制台 0 错误。本机判 lite，`?tier=full` 截图确认。static 档与少透明分支未截图 |
| `depth-parallax-image` | 程序生成彩色图与深度图，着色器按深度位移，指针加滚动驱动 | 无 | 6.0 KB | 位移置 0，渲染一帧 | 控制台 0 错误。两种模式截图完整。采样位移上限 3% |
| `gltf-model-stage` | GLTFLoader 加载本地 model.glb，`make-model.mjs` 手写 glTF 二进制写入器生成 25 KB 环面 | three 0.186.0 与 GLTFLoader（jsDelivr） | 4.4 KB | 不自转，渲染一帧 | 控制台 0 错误。两种模式截图完整。需经 http 访问 |
| `mesh-gradient` | WebGL 1 片元着色器融合 5 个来自 CSS 变量的控制色，慢速漂移，读回像素实测正文区对比度 | 无（原生 WebGL 1） | 6.3 KB | 渲染一帧静帧，不启动 rAF。无 WebGL 时用 CSS 多层 radial-gradient | 控制台 0 错误。1440 与 390 截图已看。实测对比度 11.5:1（浅色）。暗色模式未截图 |
| `instanced-field` | InstancedMesh 画 3000 根柱，高度按噪声场变化，鼠标移波心，滚动推相位，按需渲染 | three 0.186.0（jsDelivr） | 5.4 KB | 只渲染一帧静态排列。WebGL 不可用时显示内联 SVG 剪影 | 控制台 0 错误。390 截图与 RM 1440 截图已看。普通模式 1440 截图、SVG 退路、暗色模式未验证 |
| `pinned-3d-scrub` | ScrollTrigger pin 一屏并 scrub，驱动 8 方块旋转、分解、相机推进三段，文字叠层按段切换。舞台 `data-pin-screens="2"` | gsap 与 ScrollTrigger 3.15.0，three 0.186.0（jsDelivr） | 6.2 KB | 不建 ScrollTrigger，不 pin。3 个按钮切换终态一帧。gsap 加载失败走同一退路 | 控制台 0 错误。滚动 1100 px 后 1440 截图为第三段。中间段与暗色模式未验证 |
| `raymarch-backdrop` | 全屏片元着色器 SDF 光线步进（球体与盒体平滑并集），只作 `show` 档背景，文字在实色面板上 | 无（原生 WebGL 1，640×360，最多 40 步） | 5.4 KB | time 固定，渲染一帧后停止。动画只在指针或滚动后运行 2.5 秒 | 控制台 0 错误。1440 与 390 截图已看。暗色模式与真机帧率未验证 |
| `lenis-webgl-sync` | Lenis 平滑滚动，gsap.ticker 单循环同时驱动 ScrollTrigger.update 与 three 着色器 uniform，静止时不渲染 | gsap 与 ScrollTrigger 3.15.0，lenis 1.3.11，three 0.186.0（jsDelivr） | 4.9 KB | 不创建 Lenis，原生 scroll 事件写 uniform，终态由滚动位置决定 | 控制台 0 错误。1440 与 390 截图已看。软件渲染下未测惯性手感 |
| `variable-font-axis` | 原生 `font-variation-settings`，滚动进度驱动 wght、slnt、CASL，rAF 合并写入 | Google Fonts Recursive，无 JS 库 | 3.3 KB | 不监听滚动，`--t` 固定 0.7 | 控制台 0 错误。1440 与 390 截图已看。中文走系统字体，无轴变化 |
| `splittext-kinetic` | SplitText 按字入场（位移加旋转）加 SVG textPath 的 startOffset 随滚动 scrub | gsap、ScrollTrigger、SplitText 均 3.15.0（jsDelivr） | 3.5 KB | 不分割，不创建动画，直接显示终态 | 控制台 0 错误。1440 截图已看。390 未单独截 |
| `blender-headless-glb` | `blender -b --python make-model.py` 在 Blender 里程序化建模（6 块倒角薄板螺旋叠放加中柱，Principled BSDF），导出 `model.glb` 49 KB，three.js GLTFLoader 加载。管线见 `references/blender-pipeline.md` | Blender 4.0.2 加 python3-numpy（仅构建时），three 0.186.0（jsDelivr） | 4.5 KB 加 model.glb 49 KB | 不自转，只渲染一帧 | 控制台 0 错误。1440、390 与 RM 截图已看。官方 glTF 导出器已走通。缺 numpy 时脚本自动退到内置写入器（只支持网格与单材质） |
| `cross-doc-view-transition` | 两个文档都写 `@view-transition { navigation: auto }`，共享元素同名 `view-transition-name`，转场由浏览器完成 | 无库。Chromium 126 以上与 Safari 18.2 以上 | 2.5 KB 加 `page-2.html` 1.5 KB | reduce 时 `::view-transition-*` 的 animation-duration 设 0 | 控制台 0 错误。两页截图已看。转场中间帧与点击后终态未验证 |

## 体积说明

文件体积含文件头注释，不含 CDN 库。每个 `index.html` 都不超过 10 KB。

## 使用规则

1. 先在方向单里选表现形式，再选对应示例。
2. 只复制机制代码。颜色全部改用方向单的令牌。
3. 保留 Reduce Motion 分支，不要删除。
4. 同屏 WebGL 画布不超过 1 个，`backdrop-filter` 元素不超过 3 个。
5. 示例的 `http` 链接只有固定版本的 jsDelivr 地址和 SVG 命名空间。
