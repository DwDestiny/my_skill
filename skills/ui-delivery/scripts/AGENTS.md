# ui-delivery scripts

`delivery.py` 是纯 Python 标准库的 `init` / `snapshot` / `validate` 命令入口。更改字段或约束时先加会失败的合成契约测试，再改实现。不得让 `snapshot` 自动改状态、制造审查记录或把图片存在等同于运行验收。阶段目录内所有本地交付文件（包括原型的 CSS/JS/图片依赖）均纳入哈希；`stage.json` 单独哈希，`snapshot.json` 和明确的缓存产物除外。拒绝绝对路径、上级目录和软链逃逸。CLI 错误以非零退出码和可读诊断返回。
