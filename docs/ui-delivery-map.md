# UI Delivery 套件索引

本页是 UI Delivery 九个 Skill、阶段交接、来源说明和插件分发包的唯一仓库入口。套件版本为 **0.2.0**。v2 交接契约为新建交付的默认格式；v1 只保留旧结构的 legacy 校验，不代表通过 v2 的完整性门槛。

## 从哪里开始

- 要完整规划、设计、实现并验收 UI：从 [ui-delivery 总调度](../skills/ui-delivery/SKILL.md) 开始。
- 只做一个阶段时，可直接用对应阶段 Skill；阶段 Skill 接受该阶段实际输入，不要求补齐所有上游文件。
- 交付文件、旅程覆盖、stage 状态、review 与快照规则见 [handoff-contract.md](../skills/ui-delivery/references/handoff-contract.md)。
- 整套页面、公共组件和图到代码的一致性规则见[视觉一致性交接](../skills/ui-delivery/references/visual-consistency.md)；本轮脱敏问题类型、证据等级与修订范围见[保真问题复核](ui-delivery-fidelity-review.md)。
- 上游规范的选择、许可边界与引用链接见 [source-selection.md](../skills/ui-delivery/references/source-selection.md)。
- 套件的测试、最终包验收与未做事项见 [验证记录](ui-delivery-validation.md)；受限请求的实际回应见 [前向行为评估](ui-delivery-forward-eval.md)。
- 想查看旧版阶段文件结构，可从[合成产品规划样例（v1 legacy）](examples/ui-delivery-product-planning/README.md)开始；它只展示旧结构，不是 v2 模板，也不代表真实业务产品证据。

## 九个 Skill

| 顺序 | Skill | 阶段产物 / 用途 |
|---|---|---|
| 调度 | [ui-delivery](../skills/ui-delivery/SKILL.md) | 选择独立阶段或完整串联，追踪交接、状态和验收 |
| 01 | [ui-product-planning](../skills/ui-product-planning/SKILL.md) | `product-brief.md`、`page-inventory.json`；把用户任务整理为有序旅程并覆盖所有范围内页面 |
| 02 | [ui-ux-architecture](../skills/ui-ux-architecture/SKILL.md) | `ux-map.md`、`state-matrix.json`、`wireframes.md`；把旅程逐步映射到页面、screen、state 与关键元素 |
| 03 | [ui-visual-direction](../skills/ui-visual-direction/SKILL.md) | `direction-options.md`、`style-decision.json` 和需要时的实际图片候选 |
| 04 | [ui-design-system](../skills/ui-design-system/SKILL.md) | `design-system.md`、`tokens.json`、`component-inventory.json` |
| 05 | [ui-high-fidelity](../skills/ui-high-fidelity/SKILL.md) | 每页/视口的完整视觉基线与逐屏状态规格；可点击原型是独立可选产物 |
| 06 | [ui-motion-design](../skills/ui-motion-design/SKILL.md) | `motion-spec.md`、`motion-map.json` |
| 07 | [ui-frontend-implementation](../skills/ui-frontend-implementation/SKILL.md) | 实现报告、页面路由、screen 状态和必需元素到代码的映射 |
| 08 | [ui-visual-qa](../skills/ui-visual-qa/SKILL.md) | 真实运行页面的逐旅程点击结果、逐状态/视口视觉比较、证据和独立 verdict |

用户旅程是完整范围的主线：每个范围内页面要被旅程覆盖，旅程步骤要能追溯到 page、screen 和 state，关键元素在规划、结构设计、高保真、实现和 QA 中保持可对照。流程次序为交互早于视觉、动效在主要界面之后。静态高保真基线与可点击原型分开记录；原型可选，最终 QA 必须在真实运行页面逐步点击实际旅程。视觉 QA 要核对真实页面、代码工作树、截图基线、状态和视口；HTTP 200、打开 tab 或结构校验通过，都不代表页面渲染或交互通过。问题截图应放在报告对应问题旁。

## 插件包

- 源码配方：[plugins/ui-delivery/](../plugins/ui-delivery/)，维护 manifests 和可移植包 README；Skill 真源仍在 `skills/`。所有白板、设计或原型工具均按项目选择，不是公共 Skill 的强依赖。
- 构建：[scripts/build_ui_delivery_plugin.py](../scripts/build_ui_delivery_plugin.py)。
- 在仓库根执行：`python3 scripts/build_ui_delivery_plugin.py --output dist/ui-delivery-0.2.0`。目标目录必须不存在。产物是插件目录、zip 和 SHA-256 清单；构建不会安装插件或修改全局设置。
- 发布、全机安装和 Codex 全局设置不属于当前包的自动化动作；安装命令应在目标主机按当前 CLI 能力另行验证。

## 来源和许可

只保留原创摘要和一手来源链接，不复制上游 Skill 正文、第三方软件或 Pro 专有资产。详细选型、版本和许可边界见来源说明；使用前应按其中记录重新核对漂移的外部来源。
