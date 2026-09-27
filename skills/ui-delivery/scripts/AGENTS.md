# ui-delivery scripts

`delivery.py` 是纯 Python 标准库的 `init` / `snapshot` / `validate` 命令入口。新 `init` 默认创建 schema v2；schema v1 只接受 legacy 结构校验，不能声称通过新保真门。更改字段或约束时先加会失败的合成契约测试，再改实现。不得让 `snapshot` 自动改状态、制造审查记录或把图片存在等同于运行验收。阶段目录内所有受契约管理的本地交付文件均纳入哈希，缓存规则见交接契约。拒绝绝对路径、上级目录和软链逃逸。CLI 错误以非零退出码和可读诊断返回。
