---
name: ui-delivery
description: Coordinate end-to-end UI product planning, interaction, visual design, implementation, and visual QA, or route a request to one independent UI stage.
---

# UI 交付总调度

根据用户目标组织本套 UI 阶段。用户可以要求完整串联，也可以只调用某一阶段；单阶段 Skill 必须允许依据用户提供的实际输入独立工作，不把完整前序流程当成硬依赖。

## 使用流程

1. 盘点目标、项目/页面和用户已有产物，区分用户已决定、明确授权代决、建议和待确认事项。
2. 需要完整交付时按顺序选择阶段：产品规划 → UX 架构 → 视觉方向 → 设计系统 → 高保真页面/可选原型 → 动效 → 前端实现 → 视觉验收。交互逻辑早于视觉，微动画后置。
   设计系统阶段必须从获选方向图或已有系统提取并确认可执行规格，再进入逐屏高保真与实现；图片推断值不能冒充精确测量。高保真静态图与可点原型分别记录，交互可在实现阶段的浏览器中验证。
3. 用户已有有效产物或授权风格时复用并记来源；不为满足流程而重复生产。
4. 完整串联时在规范工作区登记 draft、ready、blocked 或 skipped；跳过必须说明原因，并记录产物路径、上游和产物哈希。单阶段独立调用不强制创建 stage.json、snapshot.json 或规范工作区。
5. 按需读取 references/handoff-contract.md、references/source-selection.md 和相应阶段 workflow，并通过目标包的 delivery.py 操作交接。
6. 完整串联时，开工先列出预期页面 × 关键状态 × 视口的清单、总数和用户旅程；按批交付时持续处理已授权的剩余项，未完成项标 pending 或真实 blocked，不把代表页、Hero 或一批图片当作整套完成。

## 关键约束

- 用户要求探索多个图片视觉版本时，必须实际交付可查看的图片候选；生成或查看能力不可用时标记 blocked，不能用文字冒充图片。识别当前环境实际提供的视觉工具，不硬编码模型或供应商；用户指定工具/模型且不可用时如实说明，不声称使用过。
- 默认可建议 2–3 个差异方向，但数量不强制；用户已有风格授权时可复用。
- style-decision.json 按契约记录 selection.by（user 或 authorized_agent）、selection.evidence 与 selection.authorization；推荐不等于授权。
- 可点原型必须包含可执行操作路径；静态页面截图不能替代点击验收。
- evidence 区分 runtime_capture、concept、mock，记录 route、viewport、state、revision。mock 与概念稿不能证明真实运行 UI 通过。
- CLI 契约校验只证明交付文件满足结构约定，不代表视觉或产品验收通过。
- 用户指定生成式逐屏图片时，必须实际生成并查看，不得用 HTML/Figma 渲染图冒充。公共导航等可复用交互区域优先由同一代码或设计组件维护，逐屏图须标明来源；代码渲染的设计预览也不是运行态验收截图。

## 交接参考

完整串联时阅读 [交接协议](references/handoff-contract.md) 了解工作区、阶段产物、状态和命令；阶段需要外部规范或参考时阅读 [来源选择说明](references/source-selection.md)。
涉及整套页面图片、公共组件、设计基线或图到代码一致性时，阅读 [视觉一致性交接](references/visual-consistency.md)。
