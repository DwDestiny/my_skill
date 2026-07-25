# grok-cli Cookbook — 进阶配方

`SKILL.md` 讲基础调用,这里放"把 grok 当子智能体编排进真实工作流"的配方。全部基于实测的输出结构(`text` / `structuredOutput` / `total_cost_usd`)。

## 1. 结构化对抗审查(多镜头 → 主控裁决)

让 grok 从某个固定镜头审查代码/文档,吐结构化 findings,由主控汇总裁决。多镜头 = 多次调用换不同 prompt,收集后去重。

```bash
SCHEMA='{"type":"object","properties":{"findings":{"type":"array","items":{"type":"object","properties":{"severity":{"type":"string","enum":["high","medium","low"]},"file":{"type":"string"},"issue":{"type":"string"},"fix":{"type":"string"}},"required":["severity","issue"]}}},"required":["findings"]}'

for LENS in "并发安全与数据一致性" "错误处理与边界" "契约与上游文档是否对齐"; do
  grok -p "从「$LENS」镜头审查 $PWD 下的改动,只报真问题,别客套。" \
    -m grok-4.5 --effort high --json-schema "$SCHEMA" \
    --cwd "$PWD" --always-approve --max-turns 30 </dev/null \
    | jq -c '.structuredOutput.findings[]'
done | jq -s '.'   # 汇总成一个数组,逐条裁决
```

**为什么这样拆**:一个镜头一次调用,比"让它一次看所有维度"召回率高得多——单次调用里模型会自己挑重点,换镜头才能逼出不同类别的问题。**但最终改不改由主控拍板,不是 grok 说了算**。

## 2. 批量 pipeline(一批目标各跑一次)

对一批文件/模块各委托一次,收集结构化结果:

```bash
for f in crates/*/src/*.rs; do
  grok -p "审查 $f 的公开 API 文档是否完整,缺哪些。" \
    -m grok-4.5 --effort high --json-schema "$SCHEMA" \
    --cwd "$PWD" --always-approve --max-turns 5 </dev/null \
    | jq --arg f "$f" '{file:$f, out:.structuredOutput}'
done | jq -s '.' > /tmp/api-audit.json
```

**成本意识**:每次调用光系统提示就 ~24k input tokens。文件多时优先合并成一个 prompt(把清单塞进去一次问),而不是循环刷几十次。

## 3. 把 grok 输出喂回宿主 agent

- **喂回主控**:`jq` 提取 `structuredOutput` → 主控读取裁决。**永远别让 grok 的结论直接落库/合并**,主控要过一遍,审查类尤其如此。
- **喂进编排脚本**:如果宿主 agent 支持声明式工作流,把 grok 通路做成一个自定义 subagent 类型,在脚本里指定它即可。需要精细控制(schema / effort / 权限)时,让那个 subagent 在自己的 Bash 里直接调 `grok -p ... --json-schema`。

```js
// 编排脚本片段(以 Claude Code 的 Workflow 为例)
// 前提:宿主侧已配置好一个走 grok CLI 的自定义 subagent 类型
const review = await agent(
  "从并发安全镜头审查改动,结构化输出 findings",
  { agentType: 'grok-coder', label: 'grok:concurrency', schema: FINDINGS_SCHEMA }
)
```

## 4. 权限与安全

- **`--always-approve` 等于放开一切工具。** 要收敛用:`--allow "Read,Grep,Glob"`(白名单)/ `--deny "Bash"` / `--disallowed-tools "Write,Bash"` / `--sandbox <profile>` / `--no-subagents`。
- **别信 grok 的自述权限。** 它自我报告"我能用哪些工具"未必反映 `--allow` 的实际生效范围——它可能并不知道自己被限制了。要真限制,以是否能实际执行为准;高风险场景直接 `--sandbox` + 只读白名单。
- **写码任务会真改 `--cwd` 下的文件。** 委托前确认目录对、该备份的备份好。涉及删除、覆盖、批量改名的任务,先只读盘点、确认可回滚再动手。
- grok 用 `grok.com` 登录态,命令里不带 API key——**也别把任何 key 写进 prompt 或 task 文件**,它们会随请求发出去,也会留在会话记录里。

## 5. 成本控制

| 手段 | 做法 |
|---|---|
| ~~分档 effort~~ | ⛔ **不走这条**。建议一律 `--effort high`——低档出错的返工成本远高于省下的那几分钱 |
| 合并任务 | 一个 prompt 问清多件事,别循环刷小任务(每次都吃 ~24k 系统提示)。**这是首选省钱手段** |
| 限轮数 | `--max-turns` 卡死,防 agent 循环跑飞 |
| 慎用 best-of-n | `--best-of-n N` 会跑 N 倍成本,只给真正关键的产出 |
| 看账 | `jq '.total_cost_usd'` 每次都能读到这次花了多少 |

## 6. 排障速查

| 症状 | 原因 / 处置 |
|---|---|
| `unknown model id` | 该 ID 你的账号服务端不供应(**≠ 模型不存在**)。先 `grok models` 看实时清单、`grok update` 升级后复查,再下结论。composer / fast 系列的详细情况见 SKILL.md 专节 |
| `unknown effort level 'xhigh'` | `grok-4.5` 只认 `high/medium/low`,README 里那串多档位是跨模型通用文档 |
| 配置里指定了 A 模型,实际跑的却是 B | `config.toml` 的 `default` 拿不到时 CLI 静默 fallback,**不报错**。用 `jq '.modelUsage \| keys'` 验真身 |
| 命令挂住不返回 | 缺 `--always-approve`(在等工具确认)或缺 `</dev/null`(在等 stdin) |
| `command not found: timeout` | macOS 无 `timeout`;用 `gtimeout` 或靠 `--max-turns` 兜底 |
| `structuredOutput` 为空 | 没传 `--json-schema`,或 schema 不合法。先单独校验 schema JSON |
| 输出只有纯文本没元数据 | 用了默认 `--output-format plain`;要元数据/成本改成 `json` |
| 未登录 / 401 | `grok login` 重新登录;用 `grok models` 验证登录态 |
