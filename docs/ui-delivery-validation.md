# UI Delivery 0.1.0 验证记录

日期：2026-09-26。范围是九个 Skill 的交接契约、便携包和文档一致性；本页的合成样例与静态检查均不代表真实业务产品的 UI 验收。套件入口见 [UI Delivery 索引](ui-delivery-map.md)，受限请求的前向行为评估见 [前向评估](ui-delivery-forward-eval.md)。

## 独立审查与修复复验

独立审查先在隔离临时目录复现三处问题，随后对修复版本重新验证：

| 原发现 | 修复后的独立复验结果 |
|---|---|
| `motion-design` 标为 `skipped` 后，修改已有 `motion-spec.md` 仍可全链通过 | 关闭。将该阶段设为 `skipped`、`motions=[]` 并重做后续快照，基线 `validate` 退出码为 0；再改 `motion-spec.md`，退出码为 1，提示该阶段快照过期。 |
| ZIP 内 README 的 `../../skills/...` 链接指向包外 | 关闭。实际生成的 ZIP 中，README 的 10 条本地链接均能解析到包内文件，缺失 0 条。 |
| 配方目录软链可把仓库外 README 打入 ZIP | 关闭。把隔离样例中的 `plugins/ui-delivery` 设为指向外部目录的软链后，构建器抛出 `ValueError`，拒绝构建。 |

另对嵌套原型依赖做回归：在高保真阶段加入并快照 `prototype/nested/prototype.css` 后，全链基线退出码为 0；修改该 CSS 后退出码为 1，提示高保真阶段快照过期。这验证阶段目录内的嵌套文件变更会使旧快照失效。相关实现见 [交接脚本](../skills/ui-delivery/scripts/delivery.py)、[交接契约](../skills/ui-delivery/references/handoff-contract.md)和[打包脚本](../scripts/build_ui_delivery_plugin.py)。

运行 `python3 -m unittest discover -s tests -p 'test_ui_delivery*.py' -v`：**29 项通过**，其中[交接契约测试](../tests/test_ui_delivery.py) 20 项、[打包测试](../tests/test_ui_delivery_package.py) 9 项。测试数据是合成契约样例；运行截图的文件签名检查不能证明截图来自真实产品。

## 主控最终包验收

主控对最终包 [ui-delivery-0.1.0.zip](../dist/ui-delivery-0.1.0/ui-delivery-0.1.0.zip) 拆包验收：大小 **62,144 字节**，含 **9 个 Skill、46 个文件**（含 `package-lock.json`）；SHA-256 为 `8c1294703dbf1311a4ec8f920ae2ca7d47ea8bd38e322fe959cbdc9617a40131`。本轮独立复核了该 ZIP 的文件大小与 SHA-256，均与主控报告一致。

主控验收报告记录：ZIP `testzip`、安全路径检查、解包后全部 45 项文件哈希及无额外文件检查、`SHA256SUMS`、便携 `plugin.json` 的 [Agent Plugins 1.0.0 schema](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json) 校验、官方随附的 `validate_plugin.py` 均通过。解包后的 CLI `init` 成功生成 8 个 `draft` 阶段，`validate` 正确拒绝这些草稿；从当前源码在新临时目录重建的 ZIP 与最终 ZIP 字节完全一致。以上拆包与重建结果来自[主控验收快照](ui-delivery-package-verification.json)，不是本轮独立重复执行的检查。该 JSON 是本机主控验收记录；其中的 `verification_workspace` 只指向当时使用的临时复核位置，不是长期交付路径。

主控还报告：原仓 GEB 测试 14 项通过；全仓 GEB audit 仍有 3 个历史缺口，分别是 `effect-tests/kids-winter-safety-v1/build_kids_winter_safety_pptx.js` 的 L3，以及 `plugins/wxops/scripts`、`skills/geb-project-doc-system/scripts` 的 L2。新增 UI Delivery 范围无 GEB 缺口。这些是仓库文档检查结果，不是产品交付放行。

## 验证边界

全局安装、公开发布、真实业务产品从规划到运行界面的完整八阶段交付尚未执行。当前结论覆盖合成交接门禁与最终包的结构、哈希和重建验收；真实页面的视觉、交互、权限与运行证据仍须在具体产品中逐项验收。
