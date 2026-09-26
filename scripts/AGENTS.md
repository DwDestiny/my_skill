# scripts

该目录包含仓库级辅助脚本。本 L2 增补 UI Delivery 的分发构建入口说明，不替代已有脚本规范。

- `build_ui_delivery_plugin.py` 从仓库 Skills 与 `plugins/ui-delivery/` 配方构建版本化目录、ZIP 和 SHA-256 清单。
- 构建到新目标目录；脚本拒绝覆盖已有输出，并且不会安装插件或写入全局配置。
- 仅在 UI Delivery 包格式变化时同步本说明。
