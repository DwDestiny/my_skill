---
name: ui-visual-qa
description: 需要验收真实运行界面的视觉、布局、响应式或页面状态时。
---

# UI 视觉验收

本阶段可由用户直接调用，也可由 [$ui-delivery](../ui-delivery/SKILL.md) 串联。使用本阶段实际输入即可；缺少上游文件时写明假设与限制，不伪造上游已完成。

- **目标**：把固定版本的真实运行界面与实现前冻结的设计基线逐页逐元素核对，并验证旅程与公共组件一致性。
- **最小输入**：可运行的目标应用、route/screen IDs、viewport/state、预期行为、实现前冻结的设计基线及运行版本/revision；缺基线时明确缩小可判断范围。
- **输出**：qa-report.md、qa-matrix.json、evidence.json、verdict.json。

## 工作要求

在实际运行界面做逐页面和状态核验，给出证据支持的通过/不通过/无法验证。按 [阶段工作流](references/workflow.md) 执行。完整套件工作区才登记 stage/snapshot；独立验收直接交付报告与证据。
整套交付须阅读 [视觉一致性交接](../ui-delivery/references/visual-consistency.md)：基线与运行图并排或叠加比较，逐元素核查，修复后重拍；公共组件变更复验所有使用页。不得用当前实现截图改写设计基线。

## 失败回退

真实页面不可达、状态不可达或取证失败时标记 blocked/无法验证；概念图与 mock 不算运行通过。

## 验收标准

每个结论可回溯到冻结基线、route、viewport、state、revision、字体/渲染环境和证据；未验证不计通过，像素分数或同一实现者的自述不能单独放行。
