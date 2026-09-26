# UI 设计系统工作流

## 目的与边界

将已授权的视觉选择或现有项目样式转为可复用的语义令牌和组件 API。可独立盘点现有系统；完整串联时遵循共享阶段契约。本包的 tokens.json 是供本流程使用的简化语义结构，不宣称完整兼容 DTCG 交换格式。

## 最小输入

获授权的视觉方向/参考图，或现有 CSS variables、theme、组件源码；另需至少一个实际页面或组件使用范围。只有截图时可以提出概念映射，但应标注无法验证源码真源。

## 工作步骤

1. 盘点现有令牌、字号、断点、颜色、状态样式、组件/API 及其调用者；区分代码真源、文档和值的视觉推断。
2. 先定语义别名，再定具体值，例如 color.surface.canvas 和 color.text.muted；避免把 token 命名为某个当前页面位置或一次性设计值。
3. 为颜色建立文本/背景配对，核对用户指定的 WCAG 等级或项目已有无障碍基线；记录普通文本、较大文本、控件边界、焦点和禁用态。自动对比度值不替代实际组件检查。
4. 定义字号层级、行高和响应断点。说明窄屏长标题、放大文字或局部模块折行如何处理；不要只把桌面尺寸按比例缩小。
5. 建立状态 token 和组件 API：组件用途、必需/可选属性、状态（default/loading/error/disabled 等）、事件、键盘行为和不应承担的业务职责。
6. 具体示例：按钮可用 action.primary 等语义色，区分 primary/secondary/danger 三种操作层级；disabled 不得只靠变灰，还需说明不可操作语义和辅助技术表现。
7. 将令牌和组件登记至 tokens.json、component-inventory.json，并在 design-system.md 写使用规则、来源、待定值和变更约束。
8. 完整串联时 stage 04 经 review 后 snapshot；独立整理现有系统无需规范快照。

## 产物

design-system.md 讲语义规则；tokens.json 放简化、稳定的 token value；component-inventory.json 记录组件 ID 和适用 screen ID。保持可消费而不过度抽象，不为尚不存在的场景发明 token 体系。

## 失败与回退

视觉授权不足时保留中性语义名称并将值标为 proposed；不得擅自定品牌色。图像无法验证 token 数值时把它标推测。若导入/导出要求完整 DTCG，先说明本包 schema 不兼容完整格式，再按用户授权单独做格式转换和映射表。

## 验收

- 每个关键颜色和字号有语义名、用途和状态规则；关键前景/背景配对有对比度记录。
- 断点处理覆盖长文本和大字号；状态设计覆盖 disabled/focus/error/loading 等适用状态。
- 组件 API 能映射到真实页面和 screen ID，没有假定已有但仓库中不存在的组件。
- 简化 JSON 可读且可解析；不把它标为 DTCG 完整实现或标准认证。

## 参考

- [交接契约：阶段结构字段](../../ui-delivery/references/handoff-contract.md#阶段结构字段)
- [来源选型：设计系统与 tokens](../../ui-delivery/references/source-selection.md#八阶段选型)：如需交换格式参考稳定的 DTCG 2025.10；不使用实验性 draft 作为稳定契约。
