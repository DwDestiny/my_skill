---
name: ui-high-fidelity
description: 需要从确定的交互与视觉系统制作详细页面稿、状态稿或可点原型时。
---

# UI 高保真设计

本阶段可由用户直接调用，也可由 [$ui-delivery](../ui-delivery/SKILL.md) 串联。使用本阶段实际输入即可；缺少上游文件时写明假设与限制，不伪造上游已完成。

- **目标**：产出可操作、可检查的页面稿和规格；截图不能替代原型操作路径。
- **最小输入**：目标页面和 screen IDs、交互/状态要求、已授权的视觉方向与令牌，以及需要可点验证的用户路径。
- **输出**：high-fidelity.md、screen-specs.json、实际可查看的页面稿及可点击原型，原型使用 asset_kind=prototype 并给出操作路径。

## 工作要求

产出可操作、可检查的页面稿和规格；截图不能替代原型操作路径。按 [阶段工作流](references/workflow.md) 执行。只有完整套件工作区才登记 stage.json 与 snapshot.json。

## 失败回退

上游关键规则未定则标记依赖；用户要求图像而工具不可用时 blocked，不以文字或截图宣称原型完成。

## 验收标准

screen IDs 对齐；关键状态、屏幕尺寸和交互点击路径可操作并可复现。
