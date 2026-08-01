---
name: accounts
description: Use when 添加公众号账号、管理多账号、切换当前账号、查看账号列表、给某个账号扫码登录、把旧的单账号 ~/.wxops 工作区迁移到多账号结构, or any WeChat multi-account registry / login / workspace migration task.
---

# accounts — 账号工位

## 核心心智

**一号一间办公室。** 每个公众号在 `~/.wxops/accounts/<slug>/` 有独立的一间：登录态、凭证、人设、数据、产出全部住在里面，账号之间零共享。插件目录只放代码与模板（只读），一切运行态落工作区。

三层分离（本插件的宪法）：

- **通用的是动作**：拉数据、分析、发布的代码，一份跑所有号（插件 `scripts/`）
- **赛道的是知识**：题材分类、爆款词表（`niches/` 包，后续版本解耦）
- **账号的是身份**：登录态 + 凭证 + 人设（`accounts/<slug>/`，本工位管辖）

## 引擎入口

插件根 = 本 SKILL.md 所在目录的上上级。所有命令通过：

```bash
<插件根>/scripts/wxops <子命令>
```

## 命令速查

| 命令 | 作用 |
|---|---|
| `wxops accounts add <slug> --name <显示名> [--niche ai-tools]` | 建账号：创建办公室目录 + account.json；首个账号自动设为当前 |
| `wxops accounts list` | 列出全部账号（● 标当前），含最近登录/拉数时间 |
| `wxops accounts use <slug>` | 切换当前账号 |
| `wxops accounts remove <slug>` | 退休账号：**只改状态标记，数据一个字节不删**，打印目录路径由人处置 |
| `wxops accounts check [<slug>]` | 登录态体检：headless 逐号真探测 token 是否活着（3-5s/号，不打业务接口），● 在线 / ○ 掉线 |
| `wxops migrate [--slug default] [--name <显示名>]` | 旧单账号工作区 → `accounts/<slug>/`（copy-first，源文件原样保留） |
| `wxops login --account <slug>` | 给指定账号扫码登录（扫码前打印账号名，防扫错号） |
| `wxops login --all` | 批量补登录：先体检全部在册账号，掉线的逐个开浏览器等扫码，全在线则直接收工 |
| `wxops init / analyze --account <slug>` | 各工位命令按账号执行 |

slug 规则：小写字母/数字/连字符，≤32 字符（如 `maizong`、`foodie-01`）。

## 账号解析优先级（所有子命令一致）

1. `--workspace <dir>`：**旧模式直通**，路径即工作区，不经过账号系统（npm 老用户兼容；与 `--account` 互斥，同时给会报错）
2. `--account <slug>`：工作区 = `~/.wxops/accounts/<slug>`
3. 都不给：用 `accounts.json` 里的当前账号；若账号系统尚未初始化，回落到旧版 `~/.wxops` 单租户行为并提示可 `migrate`

工作区根可用环境变量 `WXOPS_HOME` 覆盖（默认 `~/.wxops`，测试与多机同步场景用）。

## 一间办公室的布局

```
~/.wxops/
├── accounts.json                # 薄指针：version + current（账号事实以各自 account.json 为准）
├── runs/                        # 迁移清单、批次报告（analyze --all 的汇总落这里）
└── accounts/<slug>/
    ├── account.json             # slug/name/niche/created_at/last_login_at/last_fetch_at/status
    │                            # + login_alive/last_check_at（accounts check 的体检结果）
    ├── credentials/             # 0700；发布凭证后续版本落这里（0600）
    ├── browser-profile/         # 该号专属登录态（Playwright persistent context）
    ├── raw/  reports/  data/  output/     # 数据链（与旧版工作区同构，引擎无感）
    ├── topics/  drafts/  images/  published/   # 内容工位产物（后续版本启用）
    └── pipeline.json            # 工位游标：desk 总控台读这里
```

## 典型剧本

**老用户首次升级**（`~/.wxops` 下已有旧数据）：

```bash
<插件根>/scripts/wxops migrate --slug maizong --name "麦总玩AI"
```

migrate 是复制不是搬家：只读盘点 → 复制进 `accounts/maizong/` → 校验数量/大小/抽样哈希 → 清单落 `~/.wxops/runs/`。**源文件原位保留**，确认无误后由人自行归档。`dashboard/` 构建产物不迁（可再生）。

**新用户 / 加第二个号**：

```bash
<插件根>/scripts/wxops accounts add foodie --name "深夜食堂研究所"
<插件根>/scripts/wxops login --account foodie
<插件根>/scripts/wxops analyze --account foodie
```

**晨间体检 + 补登录**（多号日常）：

```bash
<插件根>/scripts/wxops accounts check      # 逐号探测，输出形如：
```

```
=== 登录态体检 ===
账号        名称          登录态    最近登录     耗时
maizong     麦总玩AI      ● 在线    今天         3.2s
backup      备用号        ○ 掉线    8 天前       4.1s

掉线号补登录：wxops login --account backup   （一次补齐：wxops login --all）
```

体检是真探测（headless 打开该号 browser-profile 看 token），结果写回 `account.json` 的 `login_alive` + `last_check_at`，desk 总控台的登录列直接引用。探测不打任何业务接口，逐号顺序进行。

## 安全红线

- **remove 永不删数据**：退休只是标记。真要删，人自己动手。
- **凭证与登录态永不入库**：`~/.wxops` 整棵树都不进 git；`credentials/` 目录 0700、凭证文件 0600。
- **同号并发锁**：同一账号的 `browser-profile/` 同时只允许一个进程打开（login、拉数、体检三方互斥），撞锁会明确报错带对方 PID。不同账号互不影响，但拉数仍应逐号顺序跑。
- **扫码前核对**：login 会先打印目标账号名，扫码前看一眼，别把 A 号的码扫进 B 号的办公室。`login --all` 每换一个号都重新打印重新核对。
- **扫码永远留给人**：体检、批量补登录都不会也不能绕过扫码本身——自动化到"浏览器已打开、二维码已就位"为止。
