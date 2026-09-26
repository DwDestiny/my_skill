# UI Delivery 产品规划示例：社区图书馆借阅入口

本目录是社区图书馆公开借阅入口的合成案例，用于展示 UI Delivery 产品规划阶段的文件形态。它不是实际图书馆需求、系统能力证明、用户研究结果或产品验收记录。

示例只包含根目录 `delivery.json` 和 `01-product-planning/` 内的规划阶段四个文件：`product-brief.md`、`page-inventory.json`、`stage.json`、`snapshot.json`。没有复制 UX 架构到视觉验收的 02–08 阶段，也不表示那些阶段已完成。

从仓库根目录使用以下命令复核快照和产品规划阶段契约：

```sh
python3 skills/ui-delivery/scripts/delivery.py snapshot docs/examples/ui-delivery-product-planning --stage product-planning
python3 skills/ui-delivery/scripts/delivery.py validate docs/examples/ui-delivery-product-planning --through product-planning
```

初始 D1 样例通过了结构与契约校验，但内容尚未完整满足当时可见的规划工作流要求：缺少模块到用户任务映射和 CTA 优先级矩阵。D2 在产品简报中补入这两项，并明确它们均为规划建议；不虚构系统字段或资格、登录政策，也不把预约提交回执写成馆员审核通过。D2 复核仍只覆盖产品规划产物，不构成真实产品验收。
