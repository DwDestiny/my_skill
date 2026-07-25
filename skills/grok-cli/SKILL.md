---
name: grok-cli
description: Use when you need to run the Grok Build CLI (`grok` binary) as an external sub-agent for research, code execution, adversarial review, or best-of-n selection — especially when the user asks to delegate work to grok / grok build / "grok 4.5" / "composer fast" instead of the host agent's native subagents. Covers headless invocation (`grok -p`), structured JSON output via `--json-schema`, reasoning-effort levels that actually work, how to tell which model ID your account is really served, silent model fallback, cost accounting, and permission scoping.
---

# Grok Build CLI(把 grok 当外部子智能体用)

## 这是什么

`grok` 是 xAI 官方的 Grok Build CLI —— 一个 agentic 编码/调研命令行工具(形态类似 Claude Code、Codex CLI)。

本手册讲的不是"怎么跟它聊天",而是**怎么用它的 headless 模式当"外部子智能体"**:跑一次性任务、拿结构化结果、并行择优,用来承担**调研 / 写码 / 对抗审查**。

典型场景:你的主 agent 有治理规则要求"子智能体走 grok",或者你想让另一个模型族做交叉验证——底层就是本手册的 `grok -p ...` 调用。

## 先读这段(关于时效性)

**本文中所有"可用模型清单""供应状态"类结论,都是 2026-07-25 在 CLI `0.2.112` 上、用某一个 grok 账号实测得到的快照。**

模型供应按账号、订阅档位、时间变化。**别把本文的模型清单当常量**——用之前先跑一次:

```bash
grok models
```

以你自己账号的实时返回为准。本文真正长期有效的是**方法**(怎么判定、怎么解析、怎么避坑),不是那份清单。

## 核心事实

| 事项 | 事实 |
|---|---|
| 二进制位置 | `~/.grok/bin/grok`(软链到 `~/.grok/downloads/grok-<ver>-<platform>`) |
| 版本 | `grok --version`;本文基于 `0.2.112`(macOS aarch64) |
| 登录态 | 用 `grok.com` 登录凭据,**命令里不需要带 API key**(`grok login` / `grok logout` 管理) |
| 模型 ID | `-m` 传短 ID(如 `grok-4.5`);返回的 `modelUsage` 里是内部全名(如 `grok-4.5-build`)。**两者不一样,别拿全名去传参** |
| 单次成本 | 一次简单 headless 调用 ≈ $0.04–0.05。系统提示就占 input ~24k tokens(有 cache 命中)。**别拿它刷高频小任务** |

## 想用 Composer 2.5 Fast?先看这节

这是最容易得出错误结论的地方,单独说清楚。

**Composer 2.5 Fast 是真实存在的模型**:Cursor 2026-05-18 发布,xAI 2026-06-01 官宣在 Grok Build 可用,官方明确表示 "Composer 2.5 will remain offered"——它和 Grok 4.5 是**并列的两个 weight class**,不是被取代的旧版本。

**但"存在"不等于"你的账号能调到"。** 在测试账号上把能试的写法都试了一遍:

| 试法 | 结果 |
|---|---|
| `-m composer-2.5-fast` / `grok-composer-2.5-fast` / `composer-2.5` / `composer` / `composer-2.5-thinking` | ❌ 全部 `Invalid params: unknown model id`(服务端拒) |
| 升级 CLI 到最新版后重试 | ❌ 清单不变 |
| 移走 `~/.grok/models_cache.json` 强制刷新清单 | ❌ 服务端实时返回的仍只有 `grok-4.5` |
| 查 xAI 公开 API 文档模型表 | ❌ 无任何 composer ID(该 slug 只在第三方工具链里流传) |
| 在 `~/.grok/config.toml` 里配 `[models] default` 指向它 | ⚠️ **配了也没用**,而且不会报错——见「坑」第 2 条 |

值得注意的是:**CLI 二进制里确实存在 `composer-2.5-fast` 这个字符串**,但服务端就是不给。所以这是**账号/订阅侧的供应问题,不是"模型不存在"**。这两句话在汇报时必须分清楚,否则会把错误结论写进下游文档。

**还能走的路**:① Cursor 通路(Composer 2.5 在那边是一等公民);② 换/升订阅,验证方式就是重跑 `grok models`;③ `[model.*]` 自定义端点挂别家 OpenAI 兼容 API(需自备 key,但 xAI 公开 API 也没有 composer ID,这条对 composer 不通)。

**但先想清楚要不要**:Composer 2.5 Fast 是**编码专用小模型**,主打便宜快;`grok-4.5` 是旗舰,xAI 官方原话是 "For everything else, including code, use Grok 4.5. **It is the most intelligent and fastest model we've built**"。**如果你的目标是"别出错",用旗舰 + 高 effort 才是正解,换 fast 小模型是反向操作。**

## 两个入口,别搞混

- **顶层 `grok -p <prompt>`** = 单轮 headless,打印响应到 stdout 后退出。**这是当子智能体用的主入口**,`--json-schema` / `--best-of-n` / `--output-format` 都在这层。
- **`grok agent <stdio|headless|serve|leader>`** = 给 SDK / MCP / 多客户端共享的**底层进程**,没有 `-p`、没有 `--json-schema`。除非在搭 MCP/SDK,否则别用。

## 标准 headless 调用(照抄)

```bash
grok -p "<任务描述>" \
  -m grok-4.5 \
  --reasoning-effort high \
  --output-format json \
  --cwd /绝对/工作目录 \
  --always-approve \
  --max-turns 20 \
  </dev/null
```

逐条为什么:

- `-p / --single "<prompt>"` — 单轮任务,跑完即退。长/复杂 prompt 改用 `--prompt-file <路径>`(躲开 shell 转义地狱)。
- `-m grok-4.5` — **显式写死模型**,免得默认漂移(见「坑」第 2 条)。换成你 `grok models` 里实际有的 ID。
- `--reasoning-effort high`(别名 `--effort`)— 思考深度。**建议一律 high**,理由见下节。
- `--output-format <plain|json|streaming-json>` — 默认 `plain`(只吐最终文本)。**要程序化解析就用 `json`**。
- `--cwd <绝对路径>` — 工作目录,**必须绝对路径**。grok 会在这里读写文件。
- `--always-approve` — **headless 必加**。不加会卡在工具执行确认交互上挂死(没人点确认)。
- `--max-turns <N>` — agent 循环上限,防跑飞烧钱。调研 5–10、写码 20–40 起。
- `</dev/null` — 重定向空 stdin,**防 grok 等 stdin 输入挂起**。实测所有非交互调用都该加。

### 结构化输出(要 JSON 结果就用这个)

```bash
grok -p "分析这段代码,列出 bug" \
  -m grok-4.5 --effort high \
  --json-schema '{"type":"object","properties":{"bugs":{"type":"array","items":{"type":"object","properties":{"file":{"type":"string"},"line":{"type":"integer"},"desc":{"type":"string"}},"required":["file","desc"]}}},"required":["bugs"]}' \
  --cwd /abs/path --always-approve --max-turns 30 </dev/null \
  | jq '.structuredOutput'
```

`--json-schema` 会**强制模型产出符合 schema 的 JSON,并隐含 `--output-format json`**。结果落在顶层 `structuredOutput` 字段。

## 输出结构与解析

`--output-format json` 吐一个顶层对象:

```json
{
  "text": "模型最终回复的自由文本",
  "stopReason": "EndTurn",
  "sessionId": "<会话 uuid>",
  "requestId": "<请求 id>",
  "thought": "推理摘要(reasoning 模型才有)",
  "usage": { "input_tokens": 24126, "output_tokens": 45, "reasoning_tokens": 36, "total_tokens": 48747, "cache_read_input_tokens": 24576 },
  "num_turns": 2,
  "total_cost_usd": 0.0558948,
  "modelUsage": { "grok-4.5-build": { "inputTokens": 24126, "outputTokens": 45, "modelCalls": 2, "costUSD": 0.0558948 } }
}
```

加了 `--json-schema` 会**多一个顶层 `structuredOutput`**(符合 schema 的对象);此时 `text` 是它的字符串化版(带转义)。

解析口径(**别去解析 `text` 里塞的 JSON,直接取 `structuredOutput`**):

```bash
OUT=$(grok -p "..." -m grok-4.5 --json-schema '...' --cwd /abs --always-approve </dev/null)
echo "$OUT" | jq '.structuredOutput'        # 结构化结果(有 schema 时)
echo "$OUT" | jq -r '.text'                 # 自由文本(无 schema 时)
echo "$OUT" | jq '.total_cost_usd'          # 这次花了多少
echo "$OUT" | jq '.modelUsage | keys'       # 实际用的是哪个模型(验真身用,见坑 2)
```

> `--output-format plain`(默认)只打印 `text` 内容、没有元数据。要成本/用量/结构化就必须 `json`。

## reasoning-effort:建议一律 high

**本手册的强约束:所有 grok 委托——调研、写码、审查——一律 `--effort high`,不要因为"任务简单"就降到 low/medium 省钱。**

理由很算术:一次调用不过几分钱,而低档模型出错的代价是——错结论流进设计文档、错代码进仓、返工重来。**省下的钱远不够赔返工的时间。**

好消息是这跟模型默认一致:`grok-4.5` 的元数据里 `reasoning_effort: "high"`、high 那档标着 `"default": true`,不传也是 high。**但仍建议显式写死 `--effort high`**——防默认漂移,也让命令自己说明意图。

**实际只有三档**(在 `0.2.112` + `grok-4.5` 上实测):

| 档位 | 官方描述 | 用不用 |
|---|---|---|
| `high` | Highest implementation quality with extensive reasoning | ✅ **默认且唯一推荐** |
| `medium` | Balanced effort with standard implementation and testing | ⚠️ 有明确理由才用 |
| `low` | Quick, fast implementations | ⛔ 不建议 |

**坑**:CLI 的 README 写着可选值有 `none / minimal / low / medium / high / xhigh / max` 还有 `deep`——那是**跨模型的通用文档**。对 `grok-4.5` 传这三档之外任何值都直接报错:

```
--effort/--reasoning-effort: unknown effort level 'xhigh'; use one of: high, medium, low
```

## 常用配方

**调研(替代 research 子智能体)** — grok 内置 web_search,X 平台数据是它的强项:

```bash
grok -p "调研 2026 年 Tauri vs Electron 桌面框架现状,给来源链接" \
  -m grok-4.5 --effort high --output-format json \
  --cwd /tmp --always-approve --max-turns 10 </dev/null | jq -r '.text'
```

(要断网可加 `--disable-web-search`;默认开。)

**写码执行(替代 coder 子智能体)** — 注意它会真改 `--cwd` 下的文件:

```bash
grok -p "在 crates/foo 加一个 parse_config 函数并补单测,cargo test 跑绿" \
  -m grok-4.5 --effort high --cwd /abs/repo \
  --always-approve --max-turns 40 </dev/null
```

**best-of-n 择优**(headless only)— 并行跑 N 路取最优,重要任务用:

```bash
grok -p "重写这个易错的迁移器,要求并发安全" \
  -m grok-4.5 --effort high --best-of-n 2 \
  --cwd /abs/repo --always-approve --max-turns 40 </dev/null
```

**自验证循环** — 加 `--check` 让 grok 跑完自己复查一遍(headless only):

```bash
grok -p "..." -m grok-4.5 --check --cwd /abs --always-approve </dev/null
```

**长 prompt 走文件**(躲 shell 转义):

```bash
grok --prompt-file /abs/task.md -m grok-4.5 --effort high \
  --cwd /abs/repo --always-approve --output-format json </dev/null
```

**收敛权限**(默认 `--always-approve` 放开一切;要收紧用):

```bash
--allow "Read,Grep,Glob"      # 只给这些工具(白名单)
--deny "Bash"                 # 禁某些工具(黑名单)
--disallowed-tools "Bash,Write"
--sandbox <profile>           # 文件/网络沙箱(GROK_SANDBOX 环境变量亦可)
--no-subagents                # 禁止它自己再派子 agent
```

## 坑(踩过的 / 会踩的)

1. **别凭一次测试就断言"某模型不存在"。** 正确的判定链是:`grok models`(读服务端实时清单)→ 查 `~/.grok/models_cache.json` → `grok update` 升到最新再复查 → 逐个 ID 实测 → 最后再查官方文档。常见翻车:只试了 `grok-4.5-fast` 一个写法失败,就写成"grok 根本没有 fast 模型"——实际 Composer 2.5 Fast 真实存在,只是该账号调不到。**「服务端不供应」≠「模型不存在」,汇报时别混为一谈。**

2. **`~/.grok/config.toml` 里 `[models] default` 指向拿不到的模型时,CLI 会静默 fallback、一声不吭。** 比如你把 default 配成一个当前账号没供应的 ID,看配置以为在用它,实际每次跑的都是别的模型——**没有任何报错**。验真身:`jq '.modelUsage | keys'`。**不带 `-m` 同样会静默漂移,所以永远显式写 `-m <模型>`。**

3. **CLI 升级会改变可用模型清单。** 升完必须复跑 `grok models`;清单缓存在 `~/.grok/models_cache.json`,**把它移走再跑一次就能强制向服务端重拉**(移走别直接删,留条退路)。

4. **`--effort` 只认 `high|medium|low`。** README 里那串 `none/minimal/xhigh/max/deep` 是跨模型通用文档,对 `grok-4.5` 一律报错。

5. **不加 `--always-approve` 会挂死**在工具确认交互上——headless 环境没人点确认。

6. **不加 `</dev/null` 可能等 stdin 挂起。** 非交互调用一律重定向空 stdin。

7. **macOS 没有 `timeout` 命令**(zsh 报 `command not found`)。要限时用 `gtimeout`(coreutils),或干脆不用——`--max-turns` 能兜底。

8. **`--cwd` 必须绝对路径**,而且写码任务会真动这个目录下的文件。委托前确认目录对、该备份的备份好;涉及删除、覆盖、批量改名时,先只读盘点再动手。

9. **成本**:单次 ≈ $0.04–0.05,系统提示占大头。别拿它跑一堆小碎任务——能合并成一个 prompt 就合并。查账:`jq '.total_cost_usd'`。

10. **`text` 字段在有 schema 时是转义后的 JSON 字符串**,别直接当对象解析——用 `structuredOutput`。

11. **`--best-of-n` / `--check` 只在 headless 生效**,交互 TUI 里没有。

## 辅助命令(排障/管理)

```bash
grok models                     # 列服务端当前实际供应的模型 —— 换订阅/升级 CLI 后先跑这条
grok --version                  # 版本
grok inspect --json             # 看当前目录 grok 发现的配置(agent/plugin/mcp)
grok mcp list                   # grok 连了哪些 MCP server
grok mcp add / remove / doctor  # 管理/诊断 grok 的 MCP 连接
grok sessions                   # 列/搜/恢复历史会话
grok export <id>                # 导出会话 transcript 为 Markdown
grok update                     # 检查/安装更新
```

## 三条通路(何时用哪个)

从宿主 agent 里委托 grok,按封装度从高到低有三条路:

1. **自定义 subagent 类型**(例如 `grok-coder` / `grok-research`)—— 最省心,直接给任务书。**注意:这类 subagent 不是 CLI 自带的,需要你在宿主 agent 里自行配置**;没配就走第 3 条。
2. **MCP 工具封装**(把 grok 包成 MCP server,暴露 `grok_code` / `grok_research` 之类的工具)—— 参数化清晰(择优、自检、时效)。同样**需要自行搭建**。
3. **直接 bash `grok -p ...`**(本手册主体)—— 最底层、最灵活:`--json-schema` 结构化、`--effort` 精调、`--allow/--deny` 精确权限、管道接 `jq`。**要结构化结果或精细控制时用这条,也是前两条的底层实现。**

> 分工纪律不在本手册的管辖范围内。哪些活派给 grok、哪些主 agent 自己扛,以你项目自己的治理文档为准——本手册只回答"怎么调"。

## 更多

- `references/cookbook.md` — 进阶配方(结构化对抗审查、批量 pipeline、把 grok 输出喂回主控、成本控制、排障速查表)。
- **官方 help 是唯一权威**:`grok --help`、`grok <子命令> --help`。CLI 升级后以 help 为准;发现本手册与 help 不符,先信 help,再回来订正本文。
