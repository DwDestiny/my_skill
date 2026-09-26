# UI 视觉验收工作流

## 目的与边界

以目标版本的真实运行 UI 为对象，给出能复查、能证伪的验收结论。验收人应独立于本轮开发；文件校验、测试绿、概念稿和 mock 都不能单独证明产品视觉通过。

## 最小输入

运行中的应用或可复现启动命令、revision/构建号、目标 routes/screens、state × viewport、设计基线、交互路径以及当前可用的截图/浏览器/桌面检查能力。缺任一项时先标明验证范围。

## 工作步骤

1. 核对被测工作树、进程 cwd、页面 URL 和 revision；版本不一致会使旧截图与当前实现失效，先重拍或标 blocked。
2. 建 qa-matrix.json，覆盖相关 screen × state × viewport，至少含 desktop 与 mobile；对不适用项写出原因。
3. 逐页实际操作并观察层级、对齐、溢出、截断、焦点、组件状态、失败反馈和视觉节奏。使用键盘完成重要路径，检查焦点可见、顺序合理；在约 200% 放大或浏览器缩放下复核长文本与表单。
4. 检查 reduced-motion 偏好下内容和操作是否仍可用；对触控目标与小屏布局按产品/项目所需基线核实。
5. 为每个发现立刻保存邻接证据：报告同一问题段紧邻对应截图/证据链接，写明 route、viewport、state、revision、复现步骤及期望/实测。避免把一组截图堆在报告末尾却没有逐问题映射。
6. 独立比对实现与被认可的设计方向/原型以及行为契约。严重判断须写成可证伪条件，例如“在 390px 宽的 error 状态，重试 CTA 被固定底栏遮挡；重新打开该 route/state 可复现”。
7. 记录每条结果为 pass、fail 或 unable_to_verify；evidence.json 区分 runtime_capture、concept、mock。只有 runtime_capture 能支撑运行态结论。
8. 写 qa-report.md、qa-matrix.json、evidence.json、verdict.json；完整串联时由独立审查人 review stage 08 并生成最终 snapshot。单阶段审查无需造全链快照。

## 产物

qa-report.md 每个问题含位置/症状/复现/证据/判断；qa-matrix.json 记录覆盖项与逐项结论；evidence.json 保存证据上下文；verdict.json 记录结论人、判断依据和未决项。

## 失败与回退

不能控制目标浏览器/应用、登录态或状态不可达、没有可靠 revision 时标为 unable_to_verify/blocked 并写出解除条件。不得用不同分支、不同部署或 mock 环境的截图顶替。截图工具失效时先尝试项目许可的替代取证；仍不行则如实停止。

## 验收

- 验收人未参与本轮实现或能说明独立性；所依据的 revision 与实现报告一致。
- 关键状态、viewport 和真实操作路径可复现；键盘焦点、放大显示和 reduced-motion 有结果或明示未验证。
- 每个 fail 有邻接的截图/证据和可证伪复现条件；未验证项不计 pass。
- verdict 不靠通过率平均掉 blocker；契约脚本通过只代表结构有效，不能授权发布。

## 参考

- [交接契约：证据和最终判断](../../ui-delivery/references/handoff-contract.md#阶段结构字段)
- [来源选型：真实视觉 QA](../../ui-delivery/references/source-selection.md#八阶段选型)：自动化用于覆盖交互和截图，不能取代独立视觉判断；按环境选择可用浏览器工具。
