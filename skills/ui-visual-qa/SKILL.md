---
name: ui-visual-qa
description: 需要验收真实运行界面的视觉、布局、响应式或页面状态时。
---

# UI 视觉验收

本阶段可由用户直接调用，也可由 [$ui-delivery](../ui-delivery/SKILL.md) 串联。使用本阶段实际输入即可；缺少上游文件时写明假设与限制，不伪造上游已完成。

- **目标**：在实际运行界面做逐页面和状态核验，给出证据支持的通过/不通过/无法验证。
- **最小输入**：可运行的目标应用、route/screen IDs、viewport/state、预期行为或设计基线、运行版本/revision。
- **输出**：qa-report.md、qa-matrix.json、evidence.json、verdict.json。

## 工作要求

在实际运行界面做逐页面和状态核验，给出证据支持的通过/不通过/无法验证。按 [阶段工作流](references/workflow.md) 执行。完整套件工作区才登记 stage/snapshot；独立验收直接交付报告与证据。

## 失败回退

真实页面不可达、状态不可达或取证失败时标记 blocked/无法验证；概念图与 mock 不算运行通过。

## 验收标准

每个结论可回溯到 route、viewport、state、revision 和证据；未验证不计通过。
