# scripts/cli — 命令行入口层(L2)

## 模块边界
`wxops` CLI 的入口与子命令。负责参数解析、环境自检、workspace/多账号管理与用户交互文案;真正的抓取逻辑在 `../fetch/`,分析逻辑在 `../analyze/`。

## 文件清单
| 文件 | 职责 |
|---|---|
| `main.py` | 可执行入口主分发:init / login / analyze / accounts / migrate / desk / kit；账号解析与锁在此层包一层 |
| `init_cmd.py` | 环境自检 + 依赖自动装 + workspace 初始化 + 配置写入 |
| `login_cmd.py` | 扫码登录持久化浏览器 profile;登录态判定依赖 URL token(已知缺口:即时读取会误报未登录,见 issue #24 关联诊断) |
| `analyze_cmd.py` | 抓取(或 demo)→ build 报告 → dashboard 预览/构建 |
| `env.py` | SKILL_DIR 自定位、`WXOPS_HOME`/workspace 解析、账号目录树、config 读写、依赖探测、中文打印工具 |
| `accounts_store.py` | 多账号注册表核心:accounts.json 薄指针 + account.json/pipeline.json 单一真源(纯逻辑,零交互) |
| `accounts_cmd.py` | accounts add/list/use/remove 的中文向导式输出 |
| `migrate_cmd.py` | 旧单账号工作区 → accounts/<slug>/ 的 copy-first 迁移 |
| `lock.py` | 同号 browser-profile 并发锁(fcntl flock;Windows no-op 降级) |
| `desk_cmd.py` | 编辑部总控台:只读展示各账号流水线状态、在途内容与下一步建议 |
| `kit_cmd.py` | 写作三件套只读门禁:persona + 结构契约(+ 选题卡/证据包);缺一 exit 1 |
| `health.py` | 登录态健康探测：headless 打开 browser-profile 查 token，写回前由调用方持锁 |
| `batch_cmd.py` | analyze --all 批量编排：前置体检 + 顺序拉数 + 防风控间隔 + 失败隔离 + 批次报告 |

## 本地规则
- 所有路径解析走 `env.py`,不得在子命令内自拼 workspace 路径。
- 用户可见文案一律中文,用 `env.py` 的 print_* 工具保持样式一致。
- 子命令只编排、不实现:网络逻辑进 `fetch/`,计算逻辑进 `analyze/`。
- 真实 `~/.wxops` 禁触;测试与冒烟一律 `WXOPS_HOME` 指向临时目录。
