# feishu-claude-bot

**把你本机的 Claude Code 接进飞书。同事在群里 @ 它、你在私聊里给它派活，它就用你机器上的代码仓、知识库和飞书权限去办，再把结论回到原消息下面。**

## 解决什么问题

| 以前 | 用这个 skill |
|---|---|
| 同事问进度、问接口、报 bug，都得你本人回 | 机器人替你回：查代码、查提交、查文档，给结论 |
| 飞书和终端里的 Claude 是两个世界 | 飞书消息直接进本机 Claude Code，能读写本机文件、跑命令、用 lark-cli |
| 接机器人怕它乱说话 | 人设和边界先问清楚；身份、私密路径由钩子硬拦，不只靠提示词 |
| 无头会话每条消息都重写缓存，一句“在吗”要 $0.18 | 固定开场白 + 续接会话，新会话降到约 $0.02，并附一键验证 |

## 工作方式

1. 常驻进程 `bridge.py` 用 `lark-cli event consume im.message.receive_v1` 收消息。群里只收 @ 机器人的消息，其余不触发。
2. 每个私聊、每个群话题对应一个 `claude -p` 会话。新会话自动带上前文（话题全文，或最近 20 条），之后只补新增的。
3. 守则（人设 + 表达风格 + 边界）通过 `--append-system-prompt-file` 加进系统提示。两个 PreToolUse 钩子按“谁发的、是不是主人私聊”限制 lark-cli 身份和可读路径。
4. Claude 的最终输出用机器人身份回复到原消息；群里回在话题里。

## 可选项

| 选项 | 取值 |
|---|---|
| 运行位置 | 服务器（systemd 用户服务）/ 本机 macOS（launchd） |
| 飞书应用 | 复用已有 lark-cli 应用 / 新建 |
| 人设 | `work` 工作分身：汇报进度、答疑、对接、记 bug；人物资料和私下评价不外露<br>`personal` 私人助理：只为主人服务，私事只对主人说 |
| 表达风格 | `veteran` 干练老同事 / `tsundere` 傲娇毒舌 / `warm` 温和专业 / `minimal` 极简冷静 |
| 身份策略 | 主人能不能用自己的用户身份办事；同事触发时能不能用主人身份读聊天记录 |
| 私密资料 | 完全私密的目录；知识库里要自动排除的分区 |

## 前置条件

| 依赖 | 要求 |
|---|---|
| 系统 | Linux（推荐服务器）或 macOS |
| Claude Code | 已登录，`claude` 在 PATH 里 |
| lark-cli | 已安装（`npm i -g @larksuite/cli`），能 `config init` 和 `auth login` |
| Python | 3.8 或更高，只用标准库 |
| 飞书 | 企业自建应用，能开机器人能力并发布版本 |

> **注意**：机器人长期使用这台机器的 Claude 登录态和额度。复杂任务一次约 $0.3–0.5。

## 安装

```bash
npx skills add DwDestiny/my_skill --skill feishu-claude-bot
```

然后对智能体说“把 Claude 接飞书”。它会先问运行位置、飞书应用、人设、表达风格和边界，再生成实例。

手动用法：

```bash
mkdir -p ~/work/my-bot
cp assets/templates/config.example.json ~/work/my-bot/config.json
bash scripts/ids.sh                       # 查 bot_open_id 和 owner_open_id，填进 config.json
python3 scripts/scaffold.py ~/work/my-bot # 生成实例并打印服务安装命令
cd ~/work/my-bot && python3 bridge.py --cache-check 3   # 验证缓存
```

## 目录

| 路径 | 内容 |
|---|---|
| `SKILL.md` | 智能体入口：五个问题、步骤、验收清单、踩坑 |
| `references/setup.md` | 服务器还是本机、复用还是新建应用、开发者后台清单 |
| `references/boundary.md` | 三层防线、身份策略、私密资料、人设边界 |
| `references/cache.md` | 缓存原理、验证方法、排查步骤、花费预期 |
| `references/config.md` | `config.json` 全部字段 |
| `scripts/scaffold.py` | 按 `config.json` 生成实例 |
| `scripts/ids.sh` | 查机器人和主人的 open_id |
| `assets/templates/` | 桥接服务、钩子、守则模板、配置样例 |

## 已知限制

- 同事触发时允许用主人身份读聊天记录（机器人身份读不了群历史）。这意味着机器人能读到主人的其他私聊，不转述靠守则；在意的话把 `identity.others` 设为 `bot`。
- 本机运行时，电脑睡眠期间的消息收不到；醒来后超过 10 分钟的消息直接跳过。
- 同一个飞书应用的消息只推给一个接收方，不能和别的机器人服务共用应用。
- 改守则后第一个新会话要重写一次缓存（约 $0.2）。
