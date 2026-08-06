# scripts/cli — 命令行入口层(L2)

## 模块边界
`wxops` CLI 的入口与子命令。负责参数解析、环境自检、workspace/多账号管理与用户交互文案;真正的抓取逻辑在 `../fetch/`,分析逻辑在 `../analyze/`。

## 文件清单
| 文件 | 职责 |
|---|---|
| `main.py` | 可执行入口主分发:init / login / analyze / accounts / migrate / desk / kit / publish / review / lint / dedup；账号解析与锁在此层包一层 |
| `init_cmd.py` | 环境自检 + 依赖自动装 + workspace 初始化 + 配置写入 |
| `login_cmd.py` | 扫码登录持久化浏览器 profile;按回车后 `_confirm_token` 就地判定(快路径读 URL + 最多 3 轮主动 goto 探 token,与 health._probe 同原理;禁调 check_login 以免锁重入) |
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
| `publish_cmd.py` | 发布主链编排：预检七项 → 渲染 → （`--go`）上传素材 + 建草稿 → 发布台账；引擎在 `../publish/` |
| `review_cmd.py` | 复盘：台账 + 选题卡预期 + analyze 数据 → `reports/review-<topic>.md`；全程只读，唯一写动作是落报告 |
| `compliance_lib.py` | 稿件合规闸纯引擎：compliance.json schema 校验 + terms/regex/cooccur 匹配；文件级三层回落 |
| `lint_cmd.py` | 稿件合规闸 CLI：按账号 niche 加载规则扫 draft/--text；exit 0=无 BLOCK，1=有 BLOCK，2=用法/缺规则 |
| `dedup_cmd.py` | 选题去重闸：读 output/wechat-ops-report-*.json 的 articles.stable，bigram Jaccard + 对象共现；核心对象查重依赖 `--object`，不传则只做标题相似度；exit 0=PASS/WARN，1=BLOCK，2=缺库 |

## 本地规则
- 所有路径解析走 `env.py`,不得在子命令内自拼 workspace 路径。
- 用户可见文案一律中文,用 `env.py` 的 print_* 工具保持样式一致。
- 子命令只编排、不实现:网络逻辑进 `fetch/`,计算逻辑进 `analyze/`。
- 真实 `~/.wxops` 禁触;测试与冒烟一律 `WXOPS_HOME` 指向临时目录。

## 发布与复盘的额外纪律(P5)
- **草稿箱止步**:`publish_cmd.py` 不得出现任何发布/群发调用点;网关能力面积由 `../publish/wechat_gateway_client.py` 兜底(仅上传素材 + 建草稿两方法)。
- **dry-run 是默认态**:触网引擎只在 `--go` 分支内惰性 import,使"默认跑法零网络"成为结构性保证而非约定。
- **凭证按账号隔离**:凭证路径由账号 slug 推导(`accounts/<slug>/credentials/wechat.json`),隔离责任在本层;凭证值不打印、不入台账、不写日志。
- **复盘不代人落笔**:`review_cmd.py` 绝不写 `persona.md` 与 niche 包——修订建议止步于报告文本,落笔要主编点头。
- **不编数**:analyze 数据里没有的指标(如单篇完读率)在报告中标"人工核对",绝不推算填充;选题卡未填的占位符行不参与机器判定。
