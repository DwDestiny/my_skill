| 字段 | 内容 |
|---|---|
| id | pinned-3d-scrub |
| 机制 | ScrollTrigger pin 一屏并 scrub，驱动 8 方块物体旋转、分解、相机推进三段，文字叠层按段切换。舞台带 data-pin-screens="2" |
| 依赖 | gsap 与 ScrollTrigger 3.15.0，three 0.186.0（jsDelivr） |
| 文件体积 | 6356 字节 |
| Reduce Motion | 不建 ScrollTrigger，不 pin。3 个按钮切换终态一帧。gsap 加载失败走同一退路 |
| 已验证 | 控制台 0 error。滚动 1100 px 后 1440 截图为第三段。RM 截图为终态。未验证中间段与暗色模式 |
