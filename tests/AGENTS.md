# tests

该目录包含仓库级测试。本 L2 增补 UI Delivery、preview-annotate 与 feishu-claude-bot 测试入口的范围说明，不概括其他测试模块。

- `test_ui_delivery.py` 覆盖共享交接与阶段契约工具。
- `test_ui_delivery_package.py` 覆盖便携插件包结构、插件目录本体和打包内容。
- `test_preview_annotate.py` 覆盖 preview-annotate 的文档、本地服务（越界、畸形路径、并发保存）与 `preview.sh` 启停；不开隧道、不访问外网。
- `test_feishu_claude_bot.py` 覆盖 feishu-claude-bot 的文档、生成器输出和两个钩子（身份策略、私密路径、知识库搜索改写）；不连飞书、不调 Claude。
- 这些检查用于结构和分发回归，不构成 UI 实际视觉质量或产品验收证据。
