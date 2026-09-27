# ui-delivery 模块说明

本模块是八阶段 UI 交付的总调度 Skill。`SKILL.md` 是入口；`references/handoff-contract.md` 是交付目录和门禁的唯一详细契约；`scripts/delivery.py` 提供不依赖第三方库的结构与哈希校验。新 `init` 默认创建 schema v2；schema v1 只作为 legacy 结构校验，不得报告为通过 v2 保真门。实际项目交付目录由 `init` 建在用户指定位置，不放进本 Skill 源码目录。

L2 子目录：`scripts/` 放确定性命令；`references/` 放按需读取的长规范。修改契约字段、文件名或命令时，必须同步脚本、测试、交接文档和八阶段 Skill 的输入输出说明。v2 将旅程、页面/状态/必需元素、设计基线、组件、实现映射和运行验收证据串联；具体字段只以交接契约为准。结构与哈希校验只能证明被登记的交付文件、自述和版本链符合相应 schema，不能证明实际设计质量、真实浏览器截图来源、真实服务进程身份或用户授权真实性。

验证：`python3 -m unittest discover -s tests -p 'test_ui_delivery.py' -v`。新增脚本保留 GEB-L3 Input/Output/Pos 头。部署、账号、生产写入不在本模块范围。
