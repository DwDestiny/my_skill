| 字段 | 内容 |
|---|---|
| id | mesh-gradient |
| 机制 | WebGL 1 片元着色器融合 5 个来自 CSS 变量的控制色，慢速漂移，并读回像素实测正文区对比度 |
| 依赖 | 无（原生 WebGL 1） |
| 文件体积 | 6459 字节 |
| Reduce Motion | 渲染一帧静帧，不启动 rAF。无 WebGL 时用 CSS 多层 radial-gradient |
| 已验证 | 控制台 0 error。1440 与 390 截图已看。RM 截图为终态。实测对比度 11.5:1（浅色模式）。未验证暗色模式截图 |
