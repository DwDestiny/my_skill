| 字段 | 内容 |
|---|---|
| id | instanced-field |
| 机制 | InstancedMesh 画 3000 根柱，高度按噪声场变化，鼠标移波心，滚动推相位，按需渲染 |
| 依赖 | three 0.186.0（jsDelivr importmap） |
| 文件体积 | 5560 字节 |
| Reduce Motion | 只渲染一帧静态排列。WebGL 不可用时显示内联 SVG 剪影 |
| 已验证 | 控制台 0 error。1440 与 390 截图已看。RM 截图为终态。未验证 SVG 退路与暗色模式 |
