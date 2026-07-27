# scripts/cli — 命令行入口层(L2)

## 模块边界
`wxops` CLI 的入口与三个子命令。负责参数解析、环境自检、workspace 管理与用户交互文案;真正的抓取逻辑在 `../fetch/`,分析逻辑在 `../analyze/`。

## 文件清单
| 文件 | 职责 |
|---|---|
| `main.py` | 可执行入口主分发:init / login / analyze |
| `init_cmd.py` | 环境自检 + 依赖自动装 + workspace 初始化 + 配置写入 |
| `login_cmd.py` | 扫码登录持久化浏览器 profile;登录态判定依赖 URL token(已知缺口:即时读取会误报未登录,见 issue #24 关联诊断) |
| `analyze_cmd.py` | 抓取(或 demo)→ build 报告 → dashboard 预览/构建 |
| `env.py` | SKILL_DIR 自定位、workspace 解析(默认 `~/.wxops`)、config 读写、依赖探测、中文打印工具 |

## 本地规则
- 所有路径解析走 `env.py`,不得在子命令内自拼 workspace 路径。
- 用户可见文案一律中文,用 `env.py` 的 print_* 工具保持样式一致。
- 子命令只编排、不实现:网络逻辑进 `fetch/`,计算逻辑进 `analyze/`。
